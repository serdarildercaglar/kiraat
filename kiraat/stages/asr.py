"""Uzun form ASR, kelime zaman damgalı.

VAD burada yalnızca konuşma bölgesi bulucudur (faster-whisper'ın silero
filtresi); kesim kararı transcript üzerinde, `segment` aşamasında alınır.
`condition_on_previous_text` kapalıdır — halüsinasyon zincirini kıran ayar.
Çıktı kayıt başına bir kelime dosyasıdır: metin, başlangıç, bitiş, olasılık.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from ..base import SourceStage, register


def whisper_name(model: str) -> str:
    """'openai/whisper-large-v3' → 'large-v3' (faster-whisper adlandırması)."""
    return model.split("whisper-", 1)[1] if model.startswith("openai/whisper-") else model


@register
class AsrStage(SourceStage):
    name = "asr"
    config_sections = ("vad",)   # VAD bölgeleri ASR girdisini belirler
    version = "2"
    gpu = True
    depends_on = ("prepare",)

    def setup(self) -> None:
        from faster_whisper import BatchedInferencePipeline, WhisperModel

        device = str(self.cfg.get("runtime.device", "cuda:0"))
        self.model = WhisperModel(whisper_name(self.opts.get("model", "large-v3")),
                                  device=device.split(":")[0],
                                  device_index=int(device.split(":")[1]) if ":" in device else 0,
                                  compute_type="float16" if device.startswith("cuda") else "int8")
        # Toplu çıkarım: VAD'ın bulduğu konuşma bölgeleri 30 s'lik pencerelere
        # toplanıp birlikte çözülür. Pencereler bağımsızdır, yani
        # condition_on_previous_text zaten yoktur — halüsinasyon zinciri kırık kalır.
        self.batch_size = int(self.opts.get("batch_size", 0) or 0)
        self.pipeline = BatchedInferencePipeline(self.model) if self.batch_size > 0 else None

    def teardown(self) -> None:
        self.model = None

    def process_source(self, source: Mapping[str, Any]) -> Sequence[Mapping[str, Any]]:
        vad = self.cfg.section("vad")
        out = Path(self.cfg.get("paths.work_root")) / "asr" / f"src{source['id']:05d}.jsonl"
        out.parent.mkdir(parents=True, exist_ok=True)
        common = dict(
            language=self.opts.get("language", "tr"),
            beam_size=5,
            temperature=float(self.opts.get("temperature", 0.0)),
            word_timestamps=bool(self.opts.get("word_timestamps", True)),
            vad_filter=True,
            vad_parameters=dict(
                threshold=float(vad.get("threshold", 0.5)),
                min_speech_duration_ms=int(vad.get("min_speech_duration_ms", 250)),
                min_silence_duration_ms=int(vad.get("min_silence_duration_ms", 300)),
                speech_pad_ms=int(vad.get("speech_pad_ms", 100)),
            ),
        )
        if self.pipeline is not None:
            segments, info = self.pipeline.transcribe(source["audio"], batch_size=self.batch_size, **common)
        else:
            segments, info = self.model.transcribe(
                source["audio"],
                condition_on_previous_text=bool(self.opts.get("condition_on_previous_text", False)),
                **common,
            )
        n = 0
        with out.open("w", encoding="utf-8") as fh:
            for seg in segments:
                for w in seg.words or ():
                    tok = w.word.strip()
                    if not tok:
                        continue
                    fh.write(json.dumps({"text": tok, "start": round(w.start, 3), "end": round(w.end, 3),
                                         "prob": round(w.probability, 4)}, ensure_ascii=False) + "\n")
                    n += 1
        return [{"words": str(out), "n_words": n, "asr_model": self.opts.get("model"),
                 "asr_batch_size": self.batch_size, "language_prob": round(info.language_probability, 3)}]


def load_words(path: str) -> list[dict[str, Any]]:
    with open(path, encoding="utf-8") as fh:
        return [json.loads(line) for line in fh]
