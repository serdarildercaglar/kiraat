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
#: Ölçülen eşik (28 Ağu 2026, kör dinleme, 34 klip): −40 dB altında müzik
#: duyulmuyor. İlk tahmin −30 idi ve dinleme onu çürüttü; konfig her zaman
#: bu anahtarı verir, buradaki değer yalnızca aşamasız kullanımın varsayılanı.
INAUDIBLE_DB = -40.0
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


#: AudioSet müzik skoru bu eşiğin altındaysa dB oranı tek başına işaret üretmez.
AUDIOSET_MIN = 0.3


def has_background_music(db: float | None, threshold_db: float = INAUDIBLE_DB,
                         audioset: float | None = None, audioset_min: float | None = AUDIOSET_MIN) -> bool:
    """Yayımlanan sütunlardan türetilen ikili yanıt — 'var mı yok mu'.

    İki koşul birden: eşlik/konuşma oranı `threshold_db` üstünde **ve** AudioSet
    müzik skoru `audioset_min` üstünde. Tek başına dB, ayrıştırıcının konuşma
    kaydındaki oda tınısını "eşlik" saydığı kanallarda müziksiz klipleri
    işaretliyordu (29 Ağu 2026, sample-15: 41/74 işaret tek kanaldan, kullanıcı
    dinledi, müzik yok; o kliplerde AudioSet medyanı 0,10, gerçek müzikte 0,53).
    `audioset_min=None` yalnızca dB kuralına döner.
    """
    if db is None or db <= threshold_db:
        return False
    if audioset_min is None:
        return True
    return audioset is not None and audioset >= audioset_min


@dataclass
class MusicMeasurer:
    """Model taşıyan ölçüm motoru. Aşamadan bağımsız kullanılabilir."""

    device: str = "cuda:0"
    audioset_model: str = "MIT/ast-finetuned-audioset-10-10-0.4593"
    #: Müzik sayılan AudioSet etiketleri. Konfigden gelir; buradaki değer
    #: yalnızca aşamasız kullanım için varsayılandır.
    audioset_labels: tuple[str, ...] = AUDIOSET_MUSIC_LABELS
    #: Kaynak ayrıştırıcı paketi. Tek bir uygulama var; konfigde başka bir ad
    #: yazılırsa sessizce yok saymak yerine hata verilir (30 Ağu 2026: anahtar
    #: konfigde duruyordu ama hiçbir kod okumuyordu).
    separator: str = "hdemucs_high_musdb_plus"
    #: Ağırlık commit'i; sabitlenmezse depo güncellendiğinde müzik skorları
    #: sessizce değişir. torchaudio paketlerinin (MMS_FA, HDemucs) karşılığı
    #: yok — onları requirements.txt'teki torchaudio sürümü sabitliyor.
    audioset_revision: str | None = None
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

        self._ast_fx = AutoFeatureExtractor.from_pretrained(self.audioset_model, revision=self.audioset_revision)
        self._ast = AutoModelForAudioClassification.from_pretrained(self.audioset_model, revision=self.audioset_revision)
        self._ast.to(self.device).eval()
        wanted = {label.casefold() for label in self.audioset_labels}
        self._music_idx = [
            int(i) for i, label in self._ast.config.id2label.items()
            if label.casefold() in wanted
        ]
        if not self._music_idx:
            raise RuntimeError("AudioSet muzik etiketleri bulunamadi")

        if self.separator != "hdemucs_high_musdb_plus":
            raise ValueError(f"bilinmeyen ayristirici: {self.separator!r}; "
                             "uygulanan tek paket 'hdemucs_high_musdb_plus'")
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
    def prepare(self, wave, sr: int) -> dict[str, Any]:
        """Bir klibin CPU tarafı: 16 kHz dalga ve AST öznitelikleri (log-mel).

        GPU'ya dokunmaz, iş parçacığında koşabilir; `MusicStage` GPU bir
        klibi ölçerken sonrakileri böyle hazırlar. Sonuç yalnızca klibin
        kendisine bağlıdır — hangi iş parçacığında, hangi sırada
        hazırlandığı ölçümü değiştirmez."""
        wave16 = self._resample(wave, sr, 16000)
        window = int(self.window_sec * 16000)
        hop = int(self.hop_sec * 16000)
        chunks = [wave16[i:i + window] for i in range(0, max(len(wave16) - window, 0) + 1, hop)]
        if not chunks:
            chunks = [wave16]
        inputs = self._ast_fx(
            [c.cpu().numpy() for c in chunks], sampling_rate=16000, return_tensors="pt"
        )
        return {"wave": wave, "sr": sr, "wave16": wave16, "ast_inputs": inputs}

    def _audioset_score(self, inputs) -> float:
        import torch

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

    def _external_prob(self, wave16) -> float:
        import torch

        inputs = self._ext_fx(wave16.cpu().numpy(), sampling_rate=16000, return_tensors="pt")
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        with torch.inference_mode():
            logits = self._ext(**inputs).logits
        return float(torch.softmax(logits, dim=-1)[0, self._ext_music_idx].item())

    def measure(self, wave, sr: int) -> dict[str, Any]:
        """Bir klibin bütün müzik ölçümleri."""
        return self.measure_prepared(self.prepare(wave, sr))

    def measure_prepared(self, prepared: Mapping[str, Any]) -> dict[str, Any]:
        """`prepare` çıktısından GPU tarafı ölçümler."""
        score = self._audioset_score(prepared["ast_inputs"])
        out: dict[str, Any] = {
            "music_score_audioset": round(score, 4),
            "music_to_speech_db": FLOOR_DB,
            "music_db_separated": False,
        }
        if score >= self.separator_screen:
            db, stems = self.separate_db(prepared["wave"], prepared["sr"])
            out["music_to_speech_db"] = round(db, 2)
            out["music_db_separated"] = True
            out["music_stem_db"] = stems
        if self._ext is not None:
            out["music_prob_external"] = round(self._external_prob(prepared["wave16"]), 4)
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
    depends_on = ("segment",)
    version = "4"   # v4: okunamayan klip koşuyu durdurmaz, ölçümler boş kalır; v3: AudioSet modeli ve ağırlık revizyonu konfigden
    gpu = True
    produces_metrics = ("music_score_audioset", "music_to_speech_db", "music_db_separated",
                        "music_stem_db", "music_prob_external")
    produces_flags = ("background_music",)

    def setup(self) -> None:
        from concurrent.futures import ThreadPoolExecutor

        self.measurer = MusicMeasurer(
            device=self.cfg.get("runtime.device", "cuda:0"),
            audioset_model=self.opts.get("audioset_model", MusicMeasurer.audioset_model),
            audioset_revision=self.opts.get("audioset_revision"),
            external_model=self.opts.get("external_model"),
            audioset_labels=tuple(self.opts.get("audioset_labels", AUDIOSET_MUSIC_LABELS)),
            separator=str(self.opts.get("separator", MusicMeasurer.separator)),
            separator_screen=float(self.opts.get("separator_screen", SEPARATOR_SCREEN)),
            window_sec=float(self.opts.get("window_sec", MusicMeasurer.window_sec)),
            hop_sec=float(self.opts.get("hop_sec", MusicMeasurer.hop_sec)),
        )
        self.measurer.setup()
        # Ön-yükleme: çözme, yeniden örnekleme ve log-mel CPU işidir ve GPU
        # ölçerken boş bekliyordu; iş parçacıkları sonraki klipleri hazırlar.
        # Sıra `map` ile korunur, her satır kendi klibinin kimliğini taşır.
        self.prefetch = ThreadPoolExecutor(max(1, int(self.cfg.get("runtime.clip_prefetch_threads", 4))))

    def teardown(self) -> None:
        self.prefetch.shutdown(wait=True)
        self.measurer.teardown()

    def _prepare(self, clip: Mapping[str, Any]) -> dict[str, Any] | None:
        """Okunamayan klipte None — ölçümler boş kalır, koşu durmaz;
        `unreadable_audio` işaretinin sahibi `clip_qc` (dnsmos ile aynı sözleşme)."""
        try:
            wave, sr = load_audio(clip["audio"])
        except Exception:
            return None
        if wave.numel() == 0:
            return None
        return self.measurer.prepare(wave, sr)

    def process_clips(self, clips: Sequence[Mapping[str, Any]]) -> Sequence[Mapping[str, Any]]:
        threshold = float(self.opts.get("inaudible_db", INAUDIBLE_DB))
        audioset_min = self.opts.get("audioset_min", AUDIOSET_MIN)
        audioset_min = None if audioset_min is None else float(audioset_min)
        rows: list[dict[str, Any]] = []
        for clip, prepared in zip(clips, self.prefetch.map(self._prepare, clips)):
            if prepared is None:
                rows.append({"id": clip["id"], "metrics": {}, "flags": []})
                continue
            metrics = self.measurer.measure_prepared(prepared)
            flags = ["background_music"] if has_background_music(
                metrics["music_to_speech_db"], threshold,
                audioset=metrics.get("music_score_audioset"), audioset_min=audioset_min,
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
