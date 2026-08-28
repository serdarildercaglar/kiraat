"""Arka plan müziği ölçümü.

Sorulan soru "bu klip konuşma mı müzik mi" değil, "**konuşmanın altında**
müzik var mı" sorusudur. İkili, birbirini dışlayan bir konuşma/müzik
sınıflandırıcısı ikincisini yanıtlayamaz: altında müzik olan bir anlatım
onun için hâlâ konuşmadır, çünkü karışık durum eğitim dağılımında yoktur.
Bu yüzden ölçüm üç katmanlıdır ve üçü de yayımlanır.

  music_score_audioset  AudioSet AST'nin müzik etiketleri üzerinden azami
                        skor. Çok etiketli olduğu için konuşmayla birlikte
                        var olabilir. Ucuz; her klipte hesaplanır.
  music_to_speech_db    Kaynak ayrıştırmasından gelen fiziksel ölçü: eşlik
                        (davul+bas+diğer) enerjisinin konuşma (vokal)
                        enerjisine oranı, dB. Pahalı; ucuz skor eleme
                        eşiğini geçen kliplerde hesaplanır.
  music_prob_external   İsteğe bağlı dış sınıflandırıcının müzik olasılığı.
                        Doğrulanmadan politikada kural olamaz.

`background_music` işareti yalnızca yayımlanan `music_to_speech_db`
sütunundan, konfigdeki eşikle türetilir; kullanıcı veriyi yeniden üretmeden
kendi eşiğini kesebilir.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from ..base import ClipStage, register

#: Konuşmanın altındaki müziğin duyulmaz sayıldığı sınır (dB).
INAUDIBLE_DB = -30.0
#: Ölçülemeyen/müziksiz durumda yazılan taban değer.
FLOOR_DB = -80.0
#: AudioSet müzik skoru bu eşiğin altındaysa ayrıştırıcı hiç koşmaz.
SEPARATOR_SCREEN = 0.05

AUDIOSET_MUSIC_LABELS = (
    "Music", "Background music", "Soundtrack music", "Theme music",
    "Musical instrument", "Singing", "Song", "Jingle (music)",
)


def rms(samples) -> float:
    """Kök ortalama kare. numpy dizisi veya sayı dizisi kabul eder."""
    try:
        import numpy as np

        arr = np.asarray(samples, dtype="float64").ravel()
        if arr.size == 0:
            return 0.0
        return float(np.sqrt(np.mean(arr * arr)))
    except ImportError:  # pragma: no cover - numpy her zaman var
        values = list(samples)
        if not values:
            return 0.0
        return math.sqrt(sum(float(v) * float(v) for v in values) / len(values))


def music_to_speech_db(speech, accompaniment, *, floor_db: float = FLOOR_DB) -> float:
    """Eşlik enerjisinin konuşma enerjisine oranı, dB.

    Negatif değer müziğin konuşmanın altında olduğunu söyler. Konuşma
    sessizse müzik baskın demektir ve 0 dB döner.
    """
    speech_rms = rms(speech)
    music_rms = rms(accompaniment)
    if music_rms <= 0.0:
        return floor_db
    if speech_rms <= 0.0:
        return 0.0
    return max(20.0 * math.log10(music_rms / speech_rms), floor_db)


def has_background_music(db: float | None, threshold_db: float = INAUDIBLE_DB) -> bool:
    """Yayımlanan sütundan türetilen ikili yanıt — 'var mı yok mu'."""
    return db is not None and db > threshold_db


@dataclass
class MusicMeasurer:
    """Model taşıyan ölçüm motoru. Aşamadan bağımsız kullanılabilir."""

    device: str = "cuda:0"
    audioset_model: str = "MIT/ast-finetuned-audioset-10-10-0.4593"
    external_model: str | None = None
    separator_screen: float = SEPARATOR_SCREEN
    window_sec: float = 10.24
    hop_sec: float = 5.0

    def __post_init__(self) -> None:
        self._ast = None
        self._ast_fx = None
        self._music_idx: list[int] = []
        self._sep = None
        self._sep_sr = 44100
        self._sep_sources: list[str] = []
        self._ext = None
        self._ext_fx = None
        self._ext_music_idx = 0

    # ------------------------------------------------------------------ setup
    def setup(self) -> None:
        import torch
        import torchaudio
        from transformers import AutoFeatureExtractor, AutoModelForAudioClassification

        self._ast_fx = AutoFeatureExtractor.from_pretrained(self.audioset_model)
        self._ast = AutoModelForAudioClassification.from_pretrained(self.audioset_model)
        self._ast.to(self.device).eval()
        wanted = {label.casefold() for label in AUDIOSET_MUSIC_LABELS}
        self._music_idx = [
            int(i) for i, label in self._ast.config.id2label.items()
            if label.casefold() in wanted
        ]
        if not self._music_idx:
            raise RuntimeError("AudioSet muzik etiketleri bulunamadi")

        bundle = torchaudio.pipelines.HDEMUCS_HIGH_MUSDB_PLUS
        model = bundle.get_model()
        # Kaynak adları paketin kendisinde değil modelde duruyor
        # (torchaudio 2.5); sıra ayrıştırıcı çıktısının eksen sırasıdır.
        self._sep_sources = list(getattr(model, "sources", ["drums", "bass", "other", "vocals"]))
        if "vocals" not in self._sep_sources:
            raise RuntimeError(f"ayristiricida 'vocals' kaynagi yok: {self._sep_sources}")
        self._sep = model.to(self.device).eval()
        self._sep_sr = bundle.sample_rate

        if self.external_model:
            self._ext_fx = AutoFeatureExtractor.from_pretrained(self.external_model)
            self._ext = AutoModelForAudioClassification.from_pretrained(self.external_model)
            self._ext.to(self.device).eval()
            labels = {int(i): l.casefold() for i, l in self._ext.config.id2label.items()}
            music = [i for i, l in labels.items() if "music" in l]
            if not music:
                raise RuntimeError(f"{self.external_model}: 'music' etiketi yok: {labels}")
            self._ext_music_idx = music[0]
        del torch

    def teardown(self) -> None:
        self._ast = self._sep = self._ext = None

    # --------------------------------------------------------------- ölçümler
    def audioset_music_score(self, wave, sr: int) -> float:
        """Pencereler üzerinde azami müzik skoru (çok etiketli, sigmoid)."""
        import torch

        wave16 = self._resample(wave, sr, 16000)
        window = int(self.window_sec * 16000)
        hop = int(self.hop_sec * 16000)
        chunks = [wave16[i:i + window] for i in range(0, max(len(wave16) - window, 0) + 1, hop)]
        if not chunks:
            chunks = [wave16]
        inputs = self._ast_fx(
            [c.cpu().numpy() for c in chunks], sampling_rate=16000, return_tensors="pt"
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        with torch.inference_mode():
            logits = self._ast(**inputs).logits
        probs = torch.sigmoid(logits)[:, self._music_idx]
        return float(probs.max().item())

    def separate_db(self, wave, sr: int) -> tuple[float, dict[str, float]]:
        """HDemucs ile ayrıştır, eşlik/konuşma oranını dB olarak döndür."""
        import torch

        wave44 = self._resample(wave, sr, self._sep_sr)
        # HDemucs stereo bekler; mono kanal iki kez verilir.
        batch = wave44.unsqueeze(0).repeat(2, 1).unsqueeze(0).to(self.device)
        ref = batch.mean(dim=(1, 2), keepdim=True)
        std = batch.std(dim=(1, 2), keepdim=True).clamp_min(1e-8)
        with torch.inference_mode():
            stems = self._sep((batch - ref) / std)
        stems = stems * std.unsqueeze(1) + ref.unsqueeze(1)
        stems = stems[0]  # (kaynak, kanal, ornek)

        by_name = {name: stems[i] for i, name in enumerate(self._sep_sources)}
        vocals = by_name["vocals"].mean(dim=0).cpu().numpy()
        accompaniment = sum(
            by_name[name].mean(dim=0) for name in self._sep_sources if name != "vocals"
        ).cpu().numpy()
        energies = {
            name: round(20.0 * math.log10(max(rms(by_name[name].mean(dim=0).cpu().numpy()), 1e-12)), 2)
            for name in self._sep_sources
        }
        return music_to_speech_db(vocals, accompaniment), energies

    def external_music_prob(self, wave, sr: int) -> float:
        import torch

        wave16 = self._resample(wave, sr, 16000)
        inputs = self._ext_fx(wave16.cpu().numpy(), sampling_rate=16000, return_tensors="pt")
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        with torch.inference_mode():
            logits = self._ext(**inputs).logits
        return float(torch.softmax(logits, dim=-1)[0, self._ext_music_idx].item())

    def measure(self, wave, sr: int) -> dict[str, Any]:
        """Bir klibin bütün müzik ölçümleri."""
        score = self.audioset_music_score(wave, sr)
        out: dict[str, Any] = {
            "music_score_audioset": round(score, 4),
            "music_to_speech_db": FLOOR_DB,
            "music_db_separated": False,
        }
        if score >= self.separator_screen:
            db, stems = self.separate_db(wave, sr)
            out["music_to_speech_db"] = round(db, 2)
            out["music_db_separated"] = True
            out["music_stem_db"] = stems
        if self._ext is not None:
            out["music_prob_external"] = round(self.external_music_prob(wave, sr), 4)
        return out

    # ------------------------------------------------------------- yardımcılar
    @staticmethod
    def _resample(wave, sr: int, target: int):
        import torchaudio

        if sr == target:
            return wave
        return torchaudio.functional.resample(wave, sr, target)


@register
class MusicStage(ClipStage):
    """Klip başına müzik ölçümlerini üretir. Karar vermez."""

    name = "music"
    gpu = True

    def setup(self) -> None:
        self.measurer = MusicMeasurer(
            device=self.cfg.get("runtime.device", "cuda:0"),
            external_model=self.opts.get("external_model"),
            separator_screen=float(self.opts.get("separator_screen", SEPARATOR_SCREEN)),
        )
        self.measurer.setup()

    def teardown(self) -> None:
        self.measurer.teardown()

    def process_clips(self, clips: Sequence[Mapping[str, Any]]) -> Sequence[Mapping[str, Any]]:
        threshold = float(self.opts.get("inaudible_db", INAUDIBLE_DB))
        rows: list[dict[str, Any]] = []
        for clip in clips:
            wave, sr = load_audio(clip["audio"])
            metrics = self.measurer.measure(wave, sr)
            flags = ["background_music"] if has_background_music(
                metrics["music_to_speech_db"], threshold
            ) else []
            rows.append({"id": clip["id"], "metrics": metrics, "flags": flags})
        self.validate_output(rows)
        return rows


def load_audio(path: str):
    """Tek kanallı float32 dalga ve örnekleme hızı."""
    import soundfile as sf
    import torch

    data, sr = sf.read(path, dtype="float32", always_2d=True)
    return torch.from_numpy(data.mean(axis=1)), int(sr)
