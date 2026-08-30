"""Bağımlılık çizelgeli dağıtıcı: CPU ve GPU işlerini üst üste bindirir.

Sıralı hat (`Pipeline.run_source_stage` / `run_clip_stage`) aşama aşama,
her aşamada kaynak kaynak gider: ffmpeg çözerken GPU boş bekler, ASR
sırasında CPU boş bekler. Burada iş birimi (aşama, nesne) çiftidir ve iki
havuza dağıtılır — CPU havuzu (prepare, segment, clip_qc) ve GPU havuzu
(asr, align, music). Ana süreç çizgeyi kurar, hazır işleri verir, dönen
sonucu yazar; depoya yalnızca ana süreç yazar.

Sıralı koşuyla özdeş çıktı üç kurala dayanır:

1. **Kanal bariyeri.** Bir kaynağın bölütlemesi, kanalın seçili bütün
   kayıtlarının ASR'si bitene (ya da hataya düşene) kadar başlamaz. Künye
   madenciliği (boilerplate) kanalın tamamını görür; sonuç, o an hangi
   kaydın bitmiş olduğuna yani zamanlamaya bağlı kalmaz.
2. **Tek yazıcı.** İşçiler yalnızca sonuç döndürür; sqlite'a ana süreç
   yazar ve 'bitti' kaydını yazımdan sonra düşer. Yarıda kesilen iş
   yeniden koşar, hiçbir şey çift yazılmaz.
3. **İş içi hesap sıralı kodla aynıdır.** Aşama nesneleri aynı
   `process_source` / `process_clips` yolunu koşar; paketleme yalnızca
   hangi klibin hangi işçide ölçüleceğini değiştirir. Dolgulu toplu çıkarım
   yoktur, bir klibin sayıları yanındaki kliplere bağlı değildir.
4. **Kaynak işi seçime, klip işi depoya bağlıdır.** Sıralı yolda
   `run_source_stage` seçilmiş kimlikleri gezer ama `run_clip_stage`
   depodaki bütün bekleyen klipleri ölçer, `export` de hepsini yazar.
   Dağıtıcı klip işlerini de seçimden kuruyordu; hata almış ya da seçim
   dışı kalmış bir kaynağın klipleri ölçülmeden manifestoya giriyordu.

Klip işleri bir kaynağın bölütlemesi biter bitmez kuyruğa girer; müzik
ölçümü ASR ile aynı GPU kuyruğunu paylaşır ve ASR öncelikli gider, çünkü
ASR alt akışı (hizalama → bölütleme → klipler) besler, müzik yalnızca
kendini.
"""

from __future__ import annotations

import importlib
import logging
import os
import time
from concurrent.futures import FIRST_COMPLETED, Future, ProcessPoolExecutor, wait
from dataclasses import dataclass, field
from multiprocessing import get_context
from typing import TYPE_CHECKING, Any, Sequence

from . import base
from .config import Config
from .stages import align, asr, clip_qc, music, prepare, segmentation  # noqa: F401  (kayıt için)

if TYPE_CHECKING:
    from .pipeline import Pipeline

log = logging.getLogger("kiraat")

#: Hazır işler arasında sıra: küçük önce. ASR alt akışı besler, müzik
#: yalnızca kendini; ikisi aynı GPU kuyruğundayken ASR öne geçer.
PRIORITY = {"prepare": 0, "asr": 0, "align": 1, "boilerplate": 1, "segment": 2, "clip_qc": 3, "music": 3}
TERMINAL = frozenset({"ok", "failed", "skipped"})
PROGRESS_EVERY_SEC = 60.0

# ------------------------------------------------------------------ işçi tarafı
_CFG: Config | None = None
_STAGES: dict[str, base.Stage] = {}


def _worker_init(cfg_data: dict[str, Any], threads: int, imports: Sequence[str]) -> None:
    """Spawn edilen işçi: iş parçacığı sayısı torch içe aktarılmadan önce
    ayarlanır (6 işçi × 12 iş parçacığı olmasın); işçi içinde ikinci bir
    havuz açılmaz (`clip_qc` kendi havuzunu `source_workers`'a göre kurar)."""
    os.environ.setdefault("OMP_NUM_THREADS", str(max(1, int(threads))))
    global _CFG
    runtime = {**dict(cfg_data.get("runtime", {})), "source_workers": 1}
    _CFG = Config({**cfg_data, "runtime": runtime})
    for mod in imports:
        importlib.import_module(mod)


def _stage(name: str) -> base.Stage:
    """Aşama nesnesi işçi başına bir kez kurulur (model yüklemesi pahalı)."""
    st = _STAGES.get(name)
    if st is None:
        assert _CFG is not None, "isci kurulmamis"
        st = base.get_stage(name)(_CFG)
        st.setup()
        _STAGES[name] = st
    return st


def run_source_job(name: str, source: dict[str, Any]) -> tuple[list[dict[str, Any]], float]:
    t0 = time.time()
    stage = _stage(name)
    assert isinstance(stage, base.SourceStage)
    rows = stage.process_source(source)
    return [dict(r) for r in rows], time.time() - t0


def run_clip_job(name: str, clips: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], float]:
    t0 = time.time()
    stage = _stage(name)
    assert isinstance(stage, base.ClipStage)
    rows = stage.process_clips(clips)
    base.ClipStage.validate_output(rows)
    return [dict(r) for r in rows], time.time() - t0


# ------------------------------------------------------------------- iş çizgesi
@dataclass
class Job:
    stage: str
    key: str
    kind: str                       # 'source' | 'channel' | 'clips'
    payload: Any = None             # kaynak kimliği / kanal adı / klip listesi
    deps: set[str] = field(default_factory=set)
    need_ok: bool = True            # False: bağımlılıkların bitmesi yeter, hata da sayılır (bariyer)
    state: str = "pending"          # pending | running | ok | failed | skipped
    seq: int = 0

    @property
    def id(self) -> str:
        return f"{self.stage}:{self.key}"

    @property
    def prio(self) -> tuple[int, int]:
        return (PRIORITY.get(self.stage, 9), self.seq)


class Scheduler:
    def __init__(self, pipe: "Pipeline", wanted: Sequence[str], source_ids: Sequence[int],
                 worker_imports: Sequence[str] = ()):
        from .pipeline import CLIP_STAGES, SOURCE_STAGES

        self.pipe = pipe
        self.cfg = pipe.cfg
        self.store = pipe.store
        self.wanted = list(wanted)
        unknown = set(self.wanted) - set(SOURCE_STAGES) - set(CLIP_STAGES) - {"boilerplate", "export"}
        if unknown:
            raise KeyError(f"bilinmeyen asama: {', '.join(sorted(unknown))}")
        self.ids = list(source_ids)
        self.imports = list(worker_imports)
        self.jobs: dict[str, Job] = {}
        self.running: dict[Future, Job] = {}
        self.versions: dict[str, str] = {}
        self.stage_cls: dict[str, type[base.Stage]] = {}
        self.channel_ids: dict[str, list[int]] = {}
        self.clip_stages: list[str] = []
        self.counts: dict[str, list[int]] = {}      # aşama → [biten, toplam] (kaynak ya da klip sayısı)
        self.cpu_workers = max(1, int(self.cfg.get("runtime.source_workers", 1) or 1))
        self.gpu_workers = max(1, int(self.cfg.get("runtime.gpu_stage_concurrency", 1) or 1))
        self._seq = 0

    # ------------------------------------------------------------ çizge kurulumu
    def _add(self, job: Job) -> Job:
        self._seq += 1
        job.seq = self._seq
        self.jobs[job.id] = job
        return job

    def _build(self) -> None:
        from .pipeline import CLIP_STAGES, SOURCE_STAGES, stage_version

        src_stages = [s for s in SOURCE_STAGES if s in self.wanted]
        if "align" in src_stages and not bool(self.cfg.get("align.enabled", True)):
            log.info("align: kapalı (align.enabled=false)")
            src_stages.remove("align")
        self.clip_stages = [s for s in CLIP_STAGES if s in self.wanted]
        for name in src_stages + self.clip_stages:
            cls = base.get_stage(name)
            self.stage_cls[name] = cls
            self.versions[name] = stage_version(self.cfg, cls)
            self.counts[name] = [0, 0]
        need_bp = "segment" in src_stages or "boilerplate" in self.wanted
        selected = self.store.sources(self.ids)
        # Künye kanalın tamamından madenlenir: hata almış ama ASR'si bitmiş bir
        # kayıt da sayılmalı. Sıralı yol `run_boilerplate(ids)` ile hepsini
        # veriyor ve kabul ölçütünü (kelime dosyası var mı) kendi uyguluyor;
        # burada süzmek kanalın ifade kümesini, dolayısıyla `boilerplate`
        # işaretlerini ve klip metnini iki yolda farklılaştırıyordu.
        for s in selected:
            self.channel_ids.setdefault(s["channel"], []).append(s["id"])
        sources = [s for s in selected if not s.get("error")]
        asr_by_channel: dict[str, set[str]] = {}
        resegment: set[int] = set()
        for s in sources:
            prev: str | None = None
            segment_pending = False
            for name in src_stages:
                job = Job(name, str(s["id"]), "source", s["id"], deps={prev} if prev else set())
                if self.store.is_done("source", str(s["id"]), name, self.versions[name]):
                    job.state = "ok"
                else:
                    self.counts[name][1] += 1
                if name == "segment" and need_bp:
                    job.deps.add(f"boilerplate:{s['channel']}")
                if name == "asr":
                    asr_by_channel.setdefault(s["channel"], set()).add(job.id)
                self._add(job)
                prev = job.id
                if name == "segment" and job.state != "ok":
                    segment_pending = True
            if segment_pending:
                resegment.add(s["id"])
        # Klip işleri depoya bağlıdır, seçime değil (bkz. 4. kural).
        self._queue_pending_clips(resegment)
        if need_bp:
            for ch in sorted(self.channel_ids):
                self._add(Job("boilerplate", ch, "channel", ch, deps=set(asr_by_channel.get(ch, ())), need_ok=False))
        log.info("sürüm: %s", ", ".join(f"{n}={v}" for n, v in sorted(self.versions.items())))
        for name in src_stages:
            if self.counts[name][1]:
                log.info("%s: %d kaynak", name, self.counts[name][1])
            else:
                log.info("%s: yapılacak kaynak yok", name)

    def _batch_size(self, name: str) -> int:
        return int(self.cfg.get("runtime.gpu_batch_size", 32)) if self.stage_cls[name].gpu \
            else int(self.cfg.get("runtime.cpu_batch_size", 64))

    def _enqueue(self, name: str, source_id: int, pending: list[dict[str, Any]]) -> None:
        batch = self._batch_size(name)
        for i in range(0, len(pending), batch):
            self._add(Job(name, f"{source_id}-{i // batch}", "clips", pending[i:i + batch]))
        self.counts[name][1] += len(pending)

    def _add_clip_jobs(self, source: dict[str, Any]) -> None:
        """Tek kaynağın klipleri; bölütleme bitince `_write_source` çağırır."""
        for name in self.clip_stages:
            self._enqueue(name, source["id"],
                          self.store.pending_clips(name, self.versions[name], source_id=source["id"]))

    def _queue_pending_clips(self, skip_sources: set[int]) -> int:
        """Depodaki bütün bekleyen klipleri kuyruğa al.

        Sıralı yol da böyle yapıyor: `Pipeline.run_clip_stage` kaynak süzgeci
        olmadan `pending_clips` çağırıyor ve `export` depodaki bütün klipleri
        yazıyor. Dağıtıcı ise klip işlerini yalnız seçilmiş ve hatasız
        kaynaklardan kuruyordu; hata almış ya da seçim dışı kalmış bir
        kaynağın klipleri hiç ölçülmeden manifestoya giriyor ve
        `eksik_olcum:*` ile önerilen alt kümeden sessizce düşüyordu.

        `skip_sources`: bu koşuda yeniden bölütlenecek kaynaklar. Onların
        klipleri şimdi alınamaz — `replace_clips` eski satırları silecek —
        bölütleme bitince `_write_source` üzerinden girerler.
        """
        added = 0
        for name in self.clip_stages:
            pending = [c for c in self.store.pending_clips(name, self.versions[name])
                       if c["source_id"] not in skip_sources]
            by_source: dict[int, list[dict[str, Any]]] = {}
            for c in pending:                      # pending_clips source_id, idx sırasında döner
                by_source.setdefault(c["source_id"], []).append(c)
            for source_id, rows in by_source.items():
                self._enqueue(name, source_id, rows)
                added += len(rows)
        return added

    # ------------------------------------------------------------------ dağıtım
    def _pool_of(self, job: Job) -> str:
        return "gpu" if self.stage_cls[job.stage].gpu else "cpu"

    def _deps_terminal(self, job: Job) -> bool:
        return all(self.jobs[d].state in TERMINAL for d in job.deps if d in self.jobs)

    def _deps_ok(self, job: Job) -> bool:
        return all(self.jobs[d].state == "ok" for d in job.deps if d in self.jobs)

    def _submit(self, job: Job, pool: ProcessPoolExecutor) -> Future:
        if job.kind == "source":
            s = self.store.sources([job.payload])[0]
            return pool.submit(run_source_job, job.stage, {**s, **s.get("meta", {})})
        return pool.submit(run_clip_job, job.stage, job.payload)

    def _submit_ready(self, pools: dict[str, ProcessPoolExecutor]) -> None:
        limits = {"cpu": 2 * self.cpu_workers, "gpu": 2 * self.gpu_workers}
        while True:
            changed = False
            inflight = {"cpu": 0, "gpu": 0}
            for j in self.running.values():
                inflight[self._pool_of(j)] += 1
            ready = sorted((j for j in self.jobs.values() if j.state == "pending" and self._deps_terminal(j)),
                           key=lambda j: j.prio)
            for job in ready:
                if job.need_ok and not self._deps_ok(job):
                    job.state = "skipped"
                    changed = True
                    continue
                if job.stage == "boilerplate":
                    self.pipe.run_boilerplate(self.channel_ids[job.key])
                    job.state = "ok"
                    changed = True
                    continue
                pool = self._pool_of(job)
                if inflight[pool] >= limits[pool]:
                    continue
                job.state = "running"
                self.running[self._submit(job, pools[pool])] = job
                inflight[pool] += 1
            if not changed:
                return

    # ----------------------------------------------------------------- sonuçlar
    def _complete(self, job: Job, fut: Future) -> None:
        try:
            rows, secs = fut.result()
        except Exception as exc:
            job.state = "failed"
            if job.kind != "source":
                raise   # klip işi hatası koşuyu durdurur; sıralı kodla aynı
            log.error("%s: src%05d hata: %s", job.stage, job.payload, exc, exc_info=exc)
            self.store.update_source(job.payload, error=f"{job.stage}: {exc}")
            return
        if job.kind == "source":
            self._write_source(job, rows, secs)
        else:
            self._write_clips(job, rows, secs)
        job.state = "ok"

    def _write_source(self, job: Job, rows: list[dict[str, Any]], secs: float) -> None:
        s = self.store.sources([job.payload])[0]
        name = job.stage
        if issubclass(self.stage_cls[name], segmentation.SegmentStage):
            self.store.replace_clips(s["id"], rows)
            self.store.update_source(s["id"], meta={**s["meta"], "n_clips": len(rows)})
        else:
            meta = {**s["meta"], **(rows[0] if rows else {})}
            fields = {k: meta[k] for k in ("audio", "duration", "source_sample_rate") if k in meta}
            self.store.update_source(s["id"], meta=meta, **fields)
        self.store.mark_done("source", str(s["id"]), name, self.versions[name])
        self.counts[name][0] += 1
        log.info("%s: src%05d [%s] %.0fs", name, s["id"], s["channel"], secs)
        if issubclass(self.stage_cls[name], segmentation.SegmentStage):
            self._add_clip_jobs(s)

    def _write_clips(self, job: Job, rows: list[dict[str, Any]], secs: float) -> None:
        name = job.stage
        cls = self.stage_cls[name]
        assert issubclass(cls, base.ClipStage)
        self.store.merge_clip_results(rows, owned_metrics=cls.produces_metrics, owned_flags=cls.produces_flags)
        for c in job.payload:
            self.store.mark_done("clip", c["id"], name, self.versions[name])
        self.counts[name][0] += len(job.payload)
        log.info("%s: %d/%d klip (src%05d, %.0fs)", name, *self.counts[name], job.payload[0]["source_id"], secs)

    def _progress(self) -> None:
        parts = [f"{name} {done}/{total}" for name, (done, total) in self.counts.items() if total]
        inflight = {"cpu": 0, "gpu": 0}
        for j in self.running.values():
            inflight[self._pool_of(j)] += 1
        pending = sum(1 for j in self.jobs.values() if j.state == "pending")
        log.info("hat: %s | koşan cpu %d gpu %d, bekleyen %d", ", ".join(parts) or "-",
                 inflight["cpu"], inflight["gpu"], pending)

    # --------------------------------------------------------------------- koşu
    def run(self) -> Any:
        self._build()
        ncpu = os.cpu_count() or 4
        ctx = get_context("spawn")
        pools = {
            "cpu": ProcessPoolExecutor(self.cpu_workers, mp_context=ctx, initializer=_worker_init,
                                       initargs=(dict(self.cfg.data), max(1, ncpu // self.cpu_workers), self.imports)),
            "gpu": ProcessPoolExecutor(self.gpu_workers, mp_context=ctx, initializer=_worker_init,
                                       initargs=(dict(self.cfg.data), max(1, ncpu // (2 * self.gpu_workers)), self.imports)),
        }
        log.info("dağıtıcı: cpu %d işçi, gpu %d işçi", self.cpu_workers, self.gpu_workers)
        last_progress = time.time()
        late_sweep = False
        try:
            while True:
                self._submit_ready(pools)
                if not self.running:
                    stuck = [j.id for j in self.jobs.values() if j.state == "pending"]
                    if stuck:
                        raise RuntimeError(f"kilit: koşan iş yok ama bekleyen var: {stuck[:5]}")
                    # Bölütlemesi hataya düşen ya da atlanan kaynakların eski
                    # klipleri kimsenin kuyruğuna girmedi; sıralı yol onları
                    # ölçerdi. Tek seferlik, ve ancak her iş bittiğinde koşar,
                    # yani `replace_clips` ile yarışamaz.
                    if not late_sweep:
                        late_sweep = True
                        if self._queue_pending_clips(set()):
                            continue
                    break
                done, _ = wait(list(self.running), timeout=PROGRESS_EVERY_SEC, return_when=FIRST_COMPLETED)
                for fut in done:
                    self._complete(self.running.pop(fut), fut)
                if time.time() - last_progress >= PROGRESS_EVERY_SEC:
                    self._progress()
                    last_progress = time.time()
        except BaseException:
            # Hata ya da kesme: bekleyen işler iptal, koşanlar beklenmez;
            # 'bitti' kaydı yazımdan sonra düştüğü için yeniden koşu güvenlidir.
            for p in pools.values():
                p.shutdown(wait=False, cancel_futures=True)
            raise
        else:
            for p in pools.values():
                p.shutdown(wait=True)
        self._progress()
        failed = [j for j in self.jobs.values() if j.state == "failed"]
        if failed:
            log.warning("hata alan kaynak: %d (%s)", len(failed), ", ".join(j.id for j in failed[:5]))
        if "export" in self.wanted:
            return self.pipe.export()
        return None
