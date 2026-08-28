"""Klip düzeyinde ucuz ölçümler: konuşma oranı, kırpma oranı, iç sessizlik.

Politikanın ilk üç kuralını besler; hiçbiri kapı değildir.
  speech_ratio          VAD'ın konuşma saydığı sürenin klibe oranı
  clip_ratio            tam ölçeğe dayanan örneklerin oranı (kırpma)
  internal_silence_sec  klip içindeki en uzun konuşmasız aralık
  peak_dbfs, rms_dbfs   seviye
"""

from __future__ import annotations

import math
from typing import Any, Mapping, Sequence

import numpy as np

from ..base import ClipStage, register


def level_metrics(wave: np.ndarray) -> dict[str, float]:
    wave = np.asarray(wave, dtype=np.float32).ravel()
    if wave.size == 0:
        return {"clip_ratio": 0.0, "peak_dbfs": -120.0, "rms_dbfs": -120.0}
    peak = float(np.max(np.abs(wave)))
    rms = float(np.sqrt(np.mean(wave ** 2)))
    return {
        "clip_ratio": round(float(np.mean(np.abs(wave) >= 0.99)), 5),
        "peak_dbfs": round(20 * math.log10(max(peak, 1e-6)), 2),
        "rms_dbfs": round(20 * math.log10(max(rms, 1e-6)), 2),
    }


def speech_metrics(segments: Sequence[Mapping[str, float]], duration: float) -> dict[str, float]:
    """VAD bölgelerinden konuşma oranı ve en uzun iç sessizlik."""
    speech = sum(s["end"] - s["start"] for s in segments)
    gaps = [b["start"] - a["end"] for a, b in zip(segments, segments[1:])]
    return {
        "speech_ratio": round(min(speech / duration, 1.0), 4) if duration > 0 else 0.0,
        "internal_silence_sec": round(max(gaps), 3) if gaps else 0.0,
        "leading_silence_sec": round(segments[0]["start"], 3) if segments else round(duration, 3),
        "trailing_silence_sec": round(duration - segments[-1]["end"], 3) if segments else round(duration, 3),
    }


_VAD = None


def _measure_one(args: tuple[str, str, dict[str, Any]]) -> dict[str, Any]:
    """Tek klip; işçi süreçlerinde çalışır, silero modelini süreç başına bir kez yükler."""
    import soundfile as sf
    import torch
    import torchaudio
    from silero_vad import get_speech_timestamps, load_silero_vad

    global _VAD
    if _VAD is None:
        torch.set_num_threads(1)
        _VAD = load_silero_vad()
    clip_id, path, vad_opts = args
    try:
        data, sr = sf.read(path, dtype="float32", always_2d=True)
    except Exception:
        return {"id": clip_id, "metrics": {}, "flags": ["unreadable_audio"]}
    mono = data.mean(axis=1)
    if mono.size == 0:
        return {"id": clip_id, "metrics": {}, "flags": ["unreadable_audio"]}
    metrics = level_metrics(mono)
    wave16 = torch.from_numpy(mono)
    if sr != 16000:
        wave16 = torchaudio.functional.resample(wave16, sr, 16000)
    ts = get_speech_timestamps(
        wave16, _VAD, sampling_rate=16000, return_seconds=True,
        threshold=float(vad_opts.get("threshold", 0.5)),
        min_speech_duration_ms=int(vad_opts.get("min_speech_duration_ms", 250)),
        min_silence_duration_ms=int(vad_opts.get("min_silence_duration_ms", 300)),
        speech_pad_ms=int(vad_opts.get("speech_pad_ms", 100)),
    )
    metrics.update(speech_metrics(ts, len(mono) / sr))
    return {"id": clip_id, "metrics": metrics, "flags": []}


@register
class ClipQcStage(ClipStage):
    name = "clip_qc"
    version = "1"   # ölçümler değişmedi; yalnızca paralel

    def setup(self) -> None:
        import multiprocessing as mp

        self.workers = int(self.cfg.get("runtime.source_workers", 1) or 1)
        self.pool = mp.get_context("spawn").Pool(self.workers) if self.workers > 1 else None

    def teardown(self) -> None:
        if self.pool is not None:
            self.pool.close()
            self.pool.join()
            self.pool = None

    def process_clips(self, clips: Sequence[Mapping[str, Any]]) -> Sequence[Mapping[str, Any]]:
        vad_opts = dict(self.cfg.section("vad"))
        jobs = [(c["id"], c["audio"], vad_opts) for c in clips]
        rows = list(self.pool.imap(_measure_one, jobs, chunksize=8)) if self.pool else [_measure_one(j) for j in jobs]
        self.validate_output(rows)
        return rows
