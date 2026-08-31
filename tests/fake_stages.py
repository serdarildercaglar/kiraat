"""Dağıtıcı testleri için sahte aşamalar.

Gerçek adların yerine geçerler (`register(override=True)`), model yüklemezler
ve her adımı çalışma dizinindeki `events.jsonl`'e düşerler; testler sıra ve
bariyer özelliklerini oradan okur. Çıktılar yalnızca kaynağa/klibe bağlı
belirlenimci değerlerdir, böylece sıralı ve paralel koşu bayt bayt aynı
manifestoyu üretmelidir. İşçi süreçleri (spawn) bu modülü
`Pipeline.worker_imports` ile içe aktarır.
"""

from __future__ import annotations

import json
import os
import shutil
import time
from pathlib import Path
from typing import Any, Mapping, Sequence

from kiraat.base import ClipStage, SourceStage, register
from kiraat.stages.segmentation import SegmentStage

HEAD = ["bu", "kanal", "sesli", "kitap", "sunar"]      # kanal künyesi: her kayıtta baştadır


def log_event(cfg: Any, event: str, **kw: Any) -> None:
    path = Path(cfg.get("paths.work_root")) / "events.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:     # O_APPEND, küçük satır: süreçler arası atomik
        fh.write(json.dumps({"t": time.time(), "event": event, "pid": os.getpid(), **kw}) + "\n")


def _work(cfg: Any) -> Path:
    return Path(cfg.get("paths.work_root"))


@register(override=True)
class FakePrepare(SourceStage):
    name = "prepare"
    version = "t1"

    def process_source(self, source: Mapping[str, Any]) -> Sequence[Mapping[str, Any]]:
        if "bad" in source["path"]:
            raise RuntimeError("bozuk kaynak")
        time.sleep(0.02)
        out = _work(self.cfg) / "audio" / f"src{source['id']:05d}.wav"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(b"RIFF")
        log_event(self.cfg, "prepare", src=source["id"], channel=source["channel"])
        return [{"audio": str(out), "duration": 60.0 + source["id"], "source_sample_rate": 44100}]


@register(override=True)
class FakeAsr(SourceStage):
    name = "asr"
    version = "t1"
    gpu = True

    def process_source(self, source: Mapping[str, Any]) -> Sequence[Mapping[str, Any]]:
        # Kanal içinde sonraki kayıt daha geç biter: bariyer olmasa ilk
        # kaydın bölütlemesi eksik künye listesiyle başlardı.
        time.sleep(0.05 * (source["id"] % 4))
        words = HEAD + ["merhaba", "dünya."] + [f"k{source['id']}", "cümle."] * 4
        out = _work(self.cfg) / "asr" / f"src{source['id']:05d}.jsonl"
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("w", encoding="utf-8") as fh:
            for i, w in enumerate(words):
                fh.write(json.dumps({"text": w, "start": i * 0.5, "end": i * 0.5 + 0.4, "prob": 0.9}) + "\n")
        log_event(self.cfg, "asr", src=source["id"], channel=source["channel"])
        return [{"words": str(out), "n_words": len(words)}]


@register(override=True)
class FakeAlign(SourceStage):
    name = "align"
    version = "t1"
    gpu = True

    def process_source(self, source: Mapping[str, Any]) -> Sequence[Mapping[str, Any]]:
        out = _work(self.cfg) / "align" / f"src{source['id']:05d}.jsonl"
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(source["words"], out)
        log_event(self.cfg, "align", src=source["id"], channel=source["channel"])
        return [{"aligned": str(out), "n_aligned": source["n_words"]}]


@register(override=True)
class FakeSegment(SegmentStage):
    name = "segment"
    version = "t1"

    def process_source(self, source: Mapping[str, Any]) -> Sequence[Mapping[str, Any]]:
        log_event(self.cfg, "segment_start", src=source["id"], channel=source["channel"])
        bp = _work(self.cfg) / "boilerplate" / f"{source['channel']}.json"
        phrases = json.load(bp.open(encoding="utf-8")) if bp.exists() else []
        rows = []
        for i in range(5):
            rows.append({
                "id": f"src{source['id']:05d}-{i:05d}", "idx": i, "channel": source["channel"],
                "start": i * 2.0, "end": i * 2.0 + 1.5, "duration": 1.5,
                "audio": str(_work(self.cfg) / "clips" / f"src{source['id']:05d}-{i:05d}.flac"),
                "text_raw": f"Cümle {i}.", "text": f"Cümle {i}. bp={len(phrases)}", "text_spoken": f"Cümle {i}.",
                "flags": [], "metrics": {"n_words": 2},
            })
        return rows


@register(override=True)
class FakeClipQc(ClipStage):
    name = "clip_qc"
    version = "t1"
    produces_metrics = ("speech_ratio",)

    def process_clips(self, clips: Sequence[Mapping[str, Any]]) -> Sequence[Mapping[str, Any]]:
        time.sleep(0.01)
        log_event(self.cfg, "clip_qc", n=len(clips))
        return [{"id": c["id"], "metrics": {"speech_ratio": (sum(map(ord, c["id"])) % 100) / 100}, "flags": []}
                for c in clips]


@register(override=True)
class FakeDnsmos(ClipStage):
    name = "dnsmos"
    version = "t1"
    produces_metrics = ("dnsmos_ovrl",)

    def process_clips(self, clips: Sequence[Mapping[str, Any]]) -> Sequence[Mapping[str, Any]]:
        time.sleep(0.01)
        log_event(self.cfg, "dnsmos", n=len(clips))
        return [{"id": c["id"], "metrics": {"dnsmos_ovrl": round((sum(map(ord, c["id"])) % 40) / 10 + 1, 3)},
                 "flags": []} for c in clips]


@register(override=True)
class FakeMusic(ClipStage):
    name = "music"
    version = "t1"
    gpu = True
    produces_metrics = ("music_to_speech_db",)
    produces_flags = ("background_music",)

    def process_clips(self, clips: Sequence[Mapping[str, Any]]) -> Sequence[Mapping[str, Any]]:
        time.sleep(0.01)
        log_event(self.cfg, "music", n=len(clips))
        rows = []
        for c in clips:
            db = -(sum(map(ord, c["id"])) % 60)
            rows.append({"id": c["id"], "metrics": {"music_to_speech_db": db},
                         "flags": ["background_music"] if db > -40 else []})
        return rows
