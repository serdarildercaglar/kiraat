"""Orkestratör: kaynakları bul, aşamaları sırayla koştur, manifestoyu yaz.

Tek süreç, sıralı. Her aşama bitirdiği nesneyi `done` tablosuna sürümüyle
yazar; yeniden koşuda aynı sürümle bitmiş nesneler atlanır. Kaynak
aşamaları kayıt kayıt, klip aşamaları toplu çalışır. Hiçbir aşama klip
elemez; `recommended` yalnızca dışa aktarımda politikadan hesaplanır.

Kaynak seçimi kanal-dönüşümlüdür: `runtime.max_sources` küçükken bile
örnek kanal çeşitliliği taşısın diye kanallar sırayla birer kayıt verir.
"""

from __future__ import annotations

import hashlib
import json
import logging
import random
import time
from pathlib import Path
from typing import Callable, Any, Sequence

from . import base
from .boilerplate import mine
from .config import Config
from .dedupe import mark_duplicates
from .scoring import annotate
from .stages import align, asr, clip_qc, music, prepare, segmentation  # noqa: F401  (kayıt için)
from .stages.asr import load_words
from .store import Store

log = logging.getLogger("kiraat")

SOURCE_STAGES = ("prepare", "asr", "align", "segment")
CLIP_STAGES = ("clip_qc", "music")


def discover_sources(cfg: Config, duration_of: Callable[[str], float] | None = None) -> list[dict[str, Any]]:
    """Kaynakları bul ve örnek sınırlarını uygula.

    `runtime.max_hours` verilirse seçim, kapsayıcı sürelerinin toplamı bütçeye
    ulaşınca durur (`duration_of` varsayılan olarak ffprobe; testte
    enjekte edilir). Bütçeyi aşan ilk kayıt da alınır ki bütçe alt sınır
    olsun; "20 saat" istenince 19,4 değil ≥20 gelir.

    `runtime.max_sources_per_channel` her kanaldan en çok bu kadar kayıt
    alır; `prepare.max_minutes` verilmişse bütçe kesilmiş süreyle sayılır
    (kayıt 2 saat, tavan 20 dk → 20 dk). İkisi birlikte "tüm kanallar, kanal
    başına eşit saat" örneklemini kurar; kayıt seçimi yine rastgeledir,
    kısa kayıtlara doğru eğilmez.
    """
    root = Path(cfg.get("paths.raw_root"))
    exts = {e.lower() for e in cfg.get("sources.extensions", [])}
    excl = list(cfg.get("sources.exclude_patterns", []) or [])
    by_channel: dict[str, list[Path]] = {}
    for p in sorted(root.rglob("*")):
        if not p.is_file() or p.suffix.lower() not in exts:
            continue
        if any(pat in str(p) for pat in excl):
            continue
        by_channel.setdefault(p.parent.name, []).append(p)
    limit = int(cfg.get("runtime.max_sources", 0) or 0)
    max_hours = float(cfg.get("runtime.max_hours", 0) or 0)
    max_channels = int(cfg.get("runtime.max_channels", 0) or 0)
    per_channel = int(cfg.get("runtime.max_sources_per_channel", 0) or 0)
    cap_sec = float(cfg.get("prepare.max_minutes", 0) or 0) * 60.0
    if max_hours and duration_of is None:
        import subprocess
        from .stages.prepare import ffprobe

        def duration_of(path: str) -> float:
            # Bozuk dosya keşfi düşürmesin; prepare aşaması kaydı hata ile işaretler.
            try:
                return ffprobe(path)["duration"]
            except (subprocess.CalledProcessError, ValueError, KeyError):
                log.warning("ffprobe basarisiz, süre 0 sayıldı: %s", path)
                return 0.0
    total_sec = 0.0
    seed = cfg.get("runtime.sample_seed")
    out: list[dict[str, Any]] = []
    channels = sorted(by_channel.items(), key=lambda kv: kv[0].casefold())
    if seed is not None:
        # Rastgele örneklem: kanal sırası ve kanal içi kayıt sırası tohumla
        # karıştırılır; sınırlar sonra uygulanır. Tam koşuyu taklit eden
        # örnek koşular için (rastgele kanal, kanal başına birden çok kayıt).
        rng = random.Random(int(seed))
        channels = [(ch, rng.sample(ps, len(ps))) for ch, ps in channels]
        rng.shuffle(channels)
    if max_channels:
        channels = channels[:max_channels]
    queues = {ch: list(ps[:per_channel] if per_channel else ps) for ch, ps in channels}
    def budget_full() -> bool:
        return bool(limit and len(out) >= limit) or bool(max_hours and total_sec >= max_hours * 3600)

    while queues and not budget_full():
        for ch in list(queues):
            if budget_full():
                break
            p = queues[ch].pop(0)
            out.append({"path": str(p), "channel": ch, "ext": p.suffix.lower(), "bytes": p.stat().st_size})
            if max_hours:
                dur = float(duration_of(str(p)) or 0.0)
                total_sec += min(dur, cap_sec) if cap_sec else dur
            if not queues[ch]:
                del queues[ch]
    return out


def stage_version(cfg: Config, stage: base.Stage) -> str:
    """Kod sürümü + aşamanın konfig bölümünün özeti.

    Konfigde eşik değişince (`segment.min_sec` gibi) 'bitti' kaydı eskimeli;
    yalnızca kod sürümüne bakmak konfig değişikliğini görmezden geliyordu.
    Bölütleme hizalama ayarlarına da bağlıdır.
    """
    sections = [stage.name]
    if stage.name == "segment":
        sections += ["align", "text"]
    payload = json.dumps({s: cfg.section(s) for s in sections}, sort_keys=True, ensure_ascii=False, default=str)
    return f"{stage.version}+{hashlib.sha1(payload.encode('utf-8')).hexdigest()[:8]}"


class Pipeline:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.store = Store(cfg.get("paths.db"))
        self.work = Path(cfg.get("paths.work_root"))

    # ------------------------------------------------------------ kaynaklar
    def run_source_stage(self, name: str, source_ids: Sequence[int]) -> None:
        stage_cls = base.get_stage(name)
        stage = stage_cls(self.cfg)
        assert isinstance(stage, base.SourceStage)
        version = stage_version(self.cfg, stage)
        todo = [s for s in self.store.sources(source_ids)
                if not self.store.is_done("source", str(s["id"]), name, version) and not s.get("error")]
        if not todo:
            log.info("%s: yapılacak kaynak yok", name)
            return
        log.info("%s: %d kaynak", name, len(todo))
        stage.setup()
        try:
            for s in todo:
                t0 = time.time()
                src = {**s, **s.get("meta", {})}
                try:
                    rows = stage.process_source(src)
                except Exception as exc:  # aşama hatası kaydı düşürmez, işaretler
                    log.exception("%s: kaynak %s hata", name, s["id"])
                    self.store.update_source(s["id"], error=f"{name}: {exc}")
                    continue
                if isinstance(stage, segmentation.SegmentStage):
                    self.store.replace_clips(s["id"], rows)
                    self.store.update_source(s["id"], meta={**s["meta"], "n_clips": len(rows)})
                else:
                    meta = {**s["meta"], **(rows[0] if rows else {})}
                    fields = {k: meta[k] for k in ("audio", "duration", "source_sample_rate") if k in meta}
                    self.store.update_source(s["id"], meta=meta, **fields)
                self.store.mark_done("source", str(s["id"]), name, version)
                log.info("%s: src%05d [%s] %.0fs", name, s["id"], s["channel"], time.time() - t0)
        finally:
            stage.teardown()

    def run_boilerplate(self, source_ids: Sequence[int]) -> None:
        """Kanal düzeyi: ASR'si biten kayıtlardan künye/anons ifadeleri madenle."""
        opts = self.cfg.section("boilerplate")
        version = "1"
        out_dir = self.work / "boilerplate"
        out_dir.mkdir(parents=True, exist_ok=True)
        by_channel: dict[str, dict[str, list[str]]] = {}
        for s in self.store.sources(source_ids):
            words_path = s.get("meta", {}).get("words")
            if words_path and Path(words_path).exists():
                by_channel.setdefault(s["channel"], {})[str(s["id"])] = [w["text"] for w in load_words(words_path)]
        for channel, recs in by_channel.items():
            mined = mine(recs, min_recordings=int(opts.get("min_recordings", 3)),
                         min_words=int(opts.get("min_words", 3)), max_words=int(opts.get("max_words", 12)),
                         head_words=int(opts.get("head_words", 80)), tail_words=int(opts.get("tail_words", 80)),
                         min_ratio=opts.get("min_ratio"))
            phrases = [list(p) for p, _ in mined]
            json.dump(phrases, (out_dir / f"{channel}.json").open("w", encoding="utf-8"), ensure_ascii=False, indent=1)
            self.store.mark_done("channel", channel, "boilerplate", version)
            log.info("boilerplate: %s — %d kayıt, %d ifade%s", channel, len(recs), len(phrases),
                     (": " + "; ".join(" ".join(p) for p in phrases[:3])) if phrases else "")

    # ---------------------------------------------------------------- klipler
    def run_clip_stage(self, name: str) -> None:
        stage_cls = base.get_stage(name)
        stage = stage_cls(self.cfg)
        assert isinstance(stage, base.ClipStage)
        version = stage_version(self.cfg, stage)
        todo = self.store.pending_clips(name, version)
        if not todo:
            log.info("%s: yapılacak klip yok", name)
            return
        log.info("%s: %d klip", name, len(todo))
        batch = int(self.cfg.get("runtime.gpu_batch_size", 32)) if stage.gpu else 512
        stage.setup()
        try:
            for i in range(0, len(todo), batch):
                chunk = todo[i:i + batch]
                rows = stage.process_clips(chunk)
                base.ClipStage.validate_output(rows)
                self.store.merge_clip_results(rows, owned_metrics=stage.produces_metrics,
                                              owned_flags=stage.produces_flags)
                for c in chunk:
                    self.store.mark_done("clip", c["id"], name, version)
                log.info("%s: %d/%d", name, min(i + batch, len(todo)), len(todo))
        finally:
            stage.teardown()

    # ------------------------------------------------------------------ çıktı
    def export(self) -> Path:
        clips = self.store.clips()
        speaker_field = str(self.cfg.get("dedupe.speaker_field", "speaker_id"))
        if not any(c.get("metrics", {}).get(speaker_field) or c.get(speaker_field) for c in clips):
            log.warning("dedupe: %s yok, kanal anahtar alınıyor (konuşmacı aşaması bağlanınca değişecek)", speaker_field)
            speaker_field = "channel"
        if bool(self.cfg.get("dedupe.enabled", True)):
            clips = mark_duplicates(clips, speaker_field=speaker_field, text_field="text")
        policy = self.cfg.policy()
        clips = annotate(clips, policy)
        out = self.work / "manifests"
        out.mkdir(parents=True, exist_ok=True)
        path = out / "clips.jsonl"
        sources = {s["id"]: s for s in self.store.sources()}
        with path.open("w", encoding="utf-8") as fh:
            for c in clips:
                s = sources[c["source_id"]]
                row = {
                    "id": c["id"], "audio": c["audio"], "channel": c["channel"],
                    "source_id": c["source_id"], "source_path": s["path"],
                    "source_sample_rate": s.get("source_sample_rate"),
                    "source_flags": s.get("meta", {}).get("source_flags", []),
                    "start": c["start"], "end": c["end"], "duration": c["duration"],
                    "text_raw": c.get("text_raw"), "text": c.get("text"), "text_spoken": c.get("text_spoken"),
                    "flags": c["flags"], "duplicate_of": c.get("duplicate_of"),
                    **{k: v for k, v in c["metrics"].items()},
                    "recommended": c["recommended"], "exclusion_reasons": c["exclusion_reasons"],
                    "policy_version": c["policy_version"],
                }
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        log.info("export: %d klip → %s", len(clips), path)
        return path

    # ------------------------------------------------------------------- koşu
    def run(self, stages: Sequence[str] | None = None) -> Path | None:
        found = discover_sources(self.cfg)
        added = self.store.add_sources(found)
        ids = [s["id"] for s in self.store.sources() if s["path"] in {f["path"] for f in found}]
        log.info("kaynak: %d bulundu, %d yeni, %d seçili", len(found), added, len(ids))
        wanted = list(stages) if stages else [*SOURCE_STAGES, *CLIP_STAGES, "export"]
        for name in wanted:
            if name == "segment" and "boilerplate" not in wanted:
                self.run_boilerplate(ids)
            if name == "boilerplate":
                self.run_boilerplate(ids)
            elif name == "align" and not bool(self.cfg.get("align.enabled", True)):
                log.info("align: kapalı (align.enabled=false)")
            elif name in SOURCE_STAGES:
                self.run_source_stage(name, ids)
            elif name in CLIP_STAGES:
                self.run_clip_stage(name)
            elif name == "export":
                return self.export()
            else:
                raise KeyError(f"bilinmeyen asama: {name}")
        return None
