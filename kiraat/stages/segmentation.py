"""Kelime zaman damgalarından klipler: cümle hizalı kesim + ses tabanlı sınır.

Sıra: ekleri birleştir → kanalın boilerplate aralıklarını bul → cümle
sınırında bölütle → sınırı sessizliğe çek → klipleri kes → üç metin alanı.
Aşama ölçüm üretir (süre, kelime güveni, boşluklar), karar vermez.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

from ..base import SourceStage, register
from ..boilerplate import find_spans
from ..boundaries import envelope_of_file, refine_boundaries
from ..segment import Word, attach_clitics, segment, clamp_to_audio
from ..text.normalize import light_clean, to_spoken
from .asr import load_words


def cut(src: str, sr: int, dst: Path, start: float, end: float) -> None:
    """Çözülmüş kayıttan klibi kesip yaz; yalnızca klibin aralığı okunur.

    Kaydın tamamını belleğe alıp dilimlemek 20 dakikalık örneklerde ucuzdu
    ama korpusta 14,9 saatlik kayıtlar var: tek kopya bile 5 GB tutuyor ve
    altı işçi aynı anda koşuyor. Klip başına ffmpeg süreci açmak da pahalı
    (18 bin klipte dakikalar); aradaki yol, dosyadan aralık okumak."""
    import soundfile as sf

    a, b = int(round(start * sr)), int(round(end * sr))
    data, _ = sf.read(src, start=a, stop=b, dtype="float32", always_2d=False)
    sf.write(str(dst), data, sr, format="FLAC", subtype="PCM_16")


@register
class SegmentStage(SourceStage):
    name = "segment"
    config_sections = ("align", "text")   # align.enabled/confidence_source, text.emit_*
    version = "8"
    depends_on = ("asr", "align", "boilerplate")

    def process_source(self, source: Mapping[str, Any]) -> Sequence[Mapping[str, Any]]:
        seg_cfg = self.cfg.segment_config()
        work = Path(self.cfg.get("paths.work_root"))
        raw = load_words(source["words"])
        # Hizalama varsa kelime zamanları oradan; güven kaynağı konfigden.
        use_align = bool(self.cfg.get("align.enabled", True)) and source.get("aligned") and Path(source["aligned"]).exists()
        conf_src = str(self.cfg.get("align.confidence_source", "asr"))
        if use_align:
            aligned = load_words(source["aligned"])
            assert len(aligned) == len(raw), "hizalama dosyası ASR kelime dosyasıyla uyuşmuyor"
            raw = aligned
        words = attach_clitics([
            Word(w["text"],
                 w.get("align_start", w["start"]) if use_align else w["start"],
                 w.get("align_end", w["end"]) if use_align else w["end"],
                 w.get("align_score", w.get("prob")) if conf_src == "align" else w.get("prob"))
            for w in raw
        ])
        align_scores = attach_clitics([Word(w["text"], 0.0, 0.0, w.get("align_score")) for w in raw]) if use_align else None
        if not words:
            return []
        phrases = []
        bp_path = work / "boilerplate" / f"{source['channel']}.json"
        if bp_path.exists():
            phrases = [tuple(p) for p in json.load(bp_path.open(encoding="utf-8"))]
        spans = find_spans([w.text for w in words], phrases)
        clips = segment(words, seg_cfg, boilerplate=spans)

        env, sr, n_samples = envelope_of_file(source["audio"])
        clips = refine_boundaries(clips, words, env, seg_cfg)
        clips = clamp_to_audio(clips, n_samples / sr)

        out_dir = work / "clips" / source["channel"] / f"src{source['id']:05d}"
        out_dir.mkdir(parents=True, exist_ok=True)
        emit_raw = bool(self.cfg.get("text.emit_raw", True))
        emit_spoken = bool(self.cfg.get("text.emit_spoken", True))
        bad = [c for c in clips if c.end <= c.start]
        if bad:
            raise RuntimeError(f"sifir/eksi sureli klip: {bad[0]}")
        rows: list[dict[str, Any]] = []
        for i, c in enumerate(clips):
            a, b = c.word_span
            probs = [w.prob for w in words[a:b] if w.prob is not None]
            text = light_clean(c.text)
            dst = out_dir / f"{i:05d}.flac"
            cut(source["audio"], sr, dst, c.start, c.end)
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
                    "confidence_source": conf_src if use_align else "asr",
                    **({"align_score_min": round(min(sc), 3), "align_score_mean": round(float(np.mean(sc)), 3)}
                       if align_scores and (sc := [w.prob for w in align_scores[a:b] if w.prob is not None]) else {}),
                    "n_words": b - a,
                    "lead_gap_sec": round(words[a].start - words[a - 1].end, 3) if a > 0 else None,
                    "trail_gap_sec": round(words[b].start - words[b - 1].end, 3) if b < len(words) else None,
                },
                "meta": {"word_span": [a, b], "snapped": [f for f in c.flags if f.startswith("snapped")]},
            })
        return rows
