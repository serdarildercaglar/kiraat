"""Kelime zaman damgalarından klipler: cümle hizalı kesim + ses tabanlı sınır.

Sıra: ekleri birleştir → kanalın boilerplate aralıklarını bul → cümle
sınırında bölütle → sınırı sessizliğe çek → klipleri kes → üç metin alanı.
Aşama ölçüm üretir (süre, kelime güveni, boşluklar), karar vermez.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

from ..base import SourceStage, register
from ..boilerplate import find_spans
from ..boundaries import envelope, refine_boundaries
from ..segment import Word, attach_clitics, segment
from ..text.normalize import light_clean, to_spoken
from .asr import load_words


def cut(src_wav: str, dst: Path, start: float, end: float) -> None:
    cmd = ["ffmpeg", "-nostdin", "-loglevel", "error", "-y", "-ss", f"{start:.3f}",
           "-t", f"{end - start:.3f}", "-i", src_wav, "-c:a", "flac", str(dst)]
    if subprocess.run(cmd).returncode != 0 or not dst.exists():
        raise RuntimeError(f"kesim basarisiz: {dst}")


@register
class SegmentStage(SourceStage):
    name = "segment"
    version = "1"
    depends_on = ("asr", "boilerplate")

    def process_source(self, source: Mapping[str, Any]) -> Sequence[Mapping[str, Any]]:
        import soundfile as sf

        seg_cfg = self.cfg.segment_config()
        work = Path(self.cfg.get("paths.work_root"))
        words = attach_clitics([Word(w["text"], w["start"], w["end"], w.get("prob")) for w in load_words(source["words"])])
        if not words:
            return []
        phrases = []
        bp_path = work / "boilerplate" / f"{source['channel']}.json"
        if bp_path.exists():
            phrases = [tuple(p) for p in json.load(bp_path.open(encoding="utf-8"))]
        spans = find_spans([w.text for w in words], phrases)
        clips = segment(words, seg_cfg, boilerplate=spans)

        audio, sr = sf.read(source["audio"], dtype="float32", always_2d=True)
        mono = audio.mean(axis=1)
        clips = refine_boundaries(clips, words, envelope(mono, sr), seg_cfg)

        out_dir = work / "clips" / source["channel"] / f"src{source['id']:05d}"
        out_dir.mkdir(parents=True, exist_ok=True)
        emit_raw = bool(self.cfg.get("text.emit_raw", True))
        emit_spoken = bool(self.cfg.get("text.emit_spoken", True))
        rows: list[dict[str, Any]] = []
        for i, c in enumerate(clips):
            a, b = c.word_span
            probs = [w.prob for w in words[a:b] if w.prob is not None]
            text = light_clean(c.text)
            dst = out_dir / f"{i:05d}.flac"
            cut(source["audio"], dst, c.start, c.end)
            flags = [f for f in c.flags if not f.startswith("snapped")]
            rows.append({
                "id": f"src{source['id']:05d}-{i:05d}", "idx": i, "channel": source["channel"],
                "start": c.start, "end": c.end, "duration": round(c.end - c.start, 3),
                "audio": str(dst),
                "text_raw": c.text if emit_raw else None,
                "text": text,
                "text_spoken": to_spoken(text) if emit_spoken else None,
                "flags": flags,
                "metrics": {
                    "word_confidence": round(min(probs), 3) if probs else None,
                    "word_confidence_mean": round(float(np.mean(probs)), 3) if probs else None,
                    "n_words": b - a,
                    "lead_gap_sec": round(words[a].start - words[a - 1].end, 3) if a > 0 else None,
                    "trail_gap_sec": round(words[b].start - words[b - 1].end, 3) if b < len(words) else None,
                },
                "meta": {"word_span": [a, b], "snapped": [f for f in c.flags if f.startswith("snapped")]},
            })
        return rows
