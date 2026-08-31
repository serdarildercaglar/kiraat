"""DNSMOS P.835: klip başına algısal kalite kestirimi (SIG/BAK/OVRL).

Alanın yerleşik kalite sinyali: WenetSpeech4TTS yayın katmanlarını, Emilia
süzgecini bu skorla kurar. Burada skor yalnızca SÜTUNDUR — politika kuralı
kör dinleme denetiminden geçmeden konmaz; `dnsmos_ovrl ≥ 3,0` kuralı tam da
bu sütun üretilmeden politikada durduğu için v4'te kaldırılmıştı.

Model, Microsoft DNS-Challenge deposundaki `DNSMOS/sig_bak_ovr.onnx`
dosyasıdır; küçük olduğu için depoya işlendi (`models/dnsmos/`) ve sha256'sı
konfigde sabitlidir — aşama kuruluşta doğrular. Hesap, referans uygulamayla
(dnsmos_local.py) birebir aynıdır: ses 16 kHz'e indirilir, 9,01 s'lik
pencereler 1 s adımla gezdirilir (kısa klip kendi üstüne yinelenerek
doldurulur), ham model çıktısı pencere başına ikinci derece polinomla MOS
ölçeğine eşlenir ve pencerelerin ortalaması alınır.

Çıkarım GPU'da (onnxruntime CUDA sağlayıcısı): CPU'da 2,07 çekirdek-s/klip
ölçüldü (31 Ağu 2026, sample-25d) ve tam koşuda ~1.000 çekirdek-saat
demekti; RTX 3090'da pencere başına 9 ms. Bir işteki bütün kliplerin
pencereleri tek kuyrukta çıkarılır; paketleme ölçümü değiştirmez.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

from ..base import ClipStage, register

SR = 16000
INPUT_SEC = 9.01

#: Ham model çıktısını MOS ölçeğine eşleyen polinomlar (dnsmos_local.py,
#: is_personalized_MOS=False; np.polyval sırası: en yüksek derece önce).
_P_SIG = (-0.08397278, 1.22083953, 0.0052439)
_P_BAK = (-0.13166888, 1.60915514, -0.39604546)
_P_OVR = (-0.06766283, 1.11546468, 0.04602535)

_ROOT = Path(__file__).resolve().parents[2]


def resolve_model_path(value: str) -> Path:
    """Göreli yol depo köküne göre çözülür; koşunun cwd'sine bağlı kalmaz."""
    p = Path(value)
    return p if p.is_absolute() else _ROOT / p


def windows(wave16: np.ndarray) -> np.ndarray:
    """Referans uygulamanın pencerelemesi: 9,01 s pencere, 1 s adım.

    9,01 s'den kısa ses, referanstaki gibi kendi üstüne yinelenerek
    doldurulur (`np.append(audio, audio)` döngüsü); eksik kalan son pencere
    atılır. Çıktı (pencere, 144160) biçimindedir ve modele toplu verilir.
    """
    need = int(INPUT_SEC * SR)
    audio = np.asarray(wave16, dtype=np.float32).ravel()
    while len(audio) < need:
        audio = np.concatenate([audio, audio])
    # Doldurmadan sonra her dilim tam `need` örnektir ve num_hops ≥ 1;
    # eksik pencere dalı ölüydü, kaldırıldı (31 Ağu incelemesi).
    num_hops = int(np.floor(len(audio) / SR) - INPUT_SEC) + 1
    return np.stack([audio[int(i * SR): int((i + INPUT_SEC) * SR)] for i in range(num_hops)])


def load_session(model_path: str, device: str = "cpu"):
    """ONNX oturumu. `cuda:N` CUDA sağlayıcısını ister ve yoksa HATA verir —
    sessizce CPU'ya düşmek 16 kat yavaşlamayı gizlerdi (CPU 150 ms/pencere,
    RTX 3090 9 ms/pencere; ham çıktı farkı ≤ 1e-4, üç ondalıkta görünmez).
    `cpu` tek iş parçacıklı oturumdur (testler ve aşamasız kullanım)."""
    import torch  # noqa: F401  — CUDA/cuDNN kütüphaneleri önce torch ile yüklenir

    import onnxruntime as ort

    opts = ort.SessionOptions()
    if device.startswith("cuda"):
        if "CUDAExecutionProvider" not in ort.get_available_providers():
            raise RuntimeError("onnxruntime CUDA sağlayıcısı yok (onnxruntime-gpu kurulu mu?); "
                               "dnsmos GPU'da koşmalı, sessizce CPU'ya düşülmez")
        idx = int(device.split(":")[1]) if ":" in device else 0
        # Arena yalnızca istendiği kadar büyür: varsayılan strateji tek
        # 16'lık koşuda bile 6,6 GB ayırıyordu; GPU işçisinde Whisper ve
        # HDemucs ile yan yana yaşayacak. (Cihaz sıralaması CUDA çalışma
        # zamanınındır — torch ile aynı; cuda:0 bu makinede RTX 3090.)
        providers = [("CUDAExecutionProvider",
                      {"device_id": idx, "arena_extend_strategy": "kSameAsRequested"})]
    else:
        opts.intra_op_num_threads = 1
        providers = ["CPUExecutionProvider"]
    return ort.InferenceSession(str(model_path), sess_options=opts, providers=providers)


#: Tek `run` çağrısındaki SABİT pencere sayısı. Modelin Conv katmanları
#: pencere başına ~73 MB ara bellek istiyor (64 pencerede 4,7 GB) ve
#: değişken dilim boyutları onnxruntime'ın BFC arenasını parçalayıp koşu
#: ortasında OOM'a götürüyor (31 Ağu 2026, sample-25d: 443 klipten sonra
#: düştü; 256/128 hiç başlamadı). Her çağrı tam bu sayıda pencereyle
#: yapılır — son dilim sıfırla doldurulur, çıktısı atılır; tek şekil = tek
#: tahsis, parçalanma yok. 16 pencere ≈ 1,2 GB, GPU işçisindeki diğer
#: modellerle (Whisper, HDemucs) yan yana sığar.
_RUN_WINDOWS = 16


def _mos(raw: np.ndarray) -> dict[str, float]:
    """Ham (N, 3) çıktıyı polinomla eşle, pencere ortalamasını döndür.

    Referans uygulama gibi ortalama, eşlenmiş değerler üzerinden alınır
    (polinom doğrusal olmadığı için ham ortalamayı eşlemekle aynı değildir).
    """
    return {
        "dnsmos_sig": round(float(np.mean(np.polyval(_P_SIG, raw[:, 0]))), 3),
        "dnsmos_bak": round(float(np.mean(np.polyval(_P_BAK, raw[:, 1]))), 3),
        "dnsmos_ovrl": round(float(np.mean(np.polyval(_P_OVR, raw[:, 2]))), 3),
    }


def score_windows(sess, wins: np.ndarray) -> dict[str, float]:
    """Tek klibin pencerelerini çıkar ve MOS'a eşle."""
    return _mos(sess.run(None, {"input_1": wins.astype(np.float32)})[0])


def score_clips(sess, per_clip: Sequence[np.ndarray]) -> list[dict[str, float]]:
    """Birden çok klibin pencerelerini tek kuyrukta toplu çıkar.

    Pencereler `_RUN_WINDOWS`lik dilimlerle modele verilir, sonra klip
    sınırlarında geri bölünür; her klibin sonucu `score_windows` ile
    tek başına hesaplananla aynıdır (test altında) — paketleme ölçümü
    değiştirmez, yalnızca GPU'yu dolu tutar.
    """
    if not per_clip:
        return []
    sizes = [len(w) for w in per_clip]
    allw = np.concatenate(per_clip)   # windows() float32 döndürür; kopyasız
    total = len(allw)
    pad = (-total) % _RUN_WINDOWS
    if pad:
        allw = np.concatenate([allw, np.zeros((pad, allw.shape[1]), dtype=np.float32)])
    raw = np.concatenate([sess.run(None, {"input_1": allw[i:i + _RUN_WINDOWS]})[0]
                          for i in range(0, len(allw), _RUN_WINDOWS)])[:total]
    out, at = [], 0
    for n in sizes:
        out.append(_mos(raw[at:at + n]))
        at += n
    return out


def clip_windows(path: str) -> np.ndarray | None:
    """Klibi çöz, 16 kHz'e indir, pencerele. Okunamıyorsa None — işaret
    verilmez, `unreadable_audio` işaretinin sahibi `clip_qc`."""
    import soundfile as sf
    import torch
    import torchaudio

    try:
        data, sr = sf.read(path, dtype="float32", always_2d=True)
    except Exception:
        return None
    mono = data.mean(axis=1)
    if mono.size == 0:
        return None
    wave = torch.from_numpy(mono)
    if sr != SR:
        wave = torchaudio.functional.resample(wave, sr, SR)
    return windows(wave.numpy())


@register
class DnsmosStage(ClipStage):
    """Klip başına DNSMOS P.835 skorları. Karar vermez."""

    name = "dnsmos"
    depends_on = ("segment",)
    version = "2"   # v2: GPU oturumu, klipler arası toplu çıkarım (v1 CPU havuzu, 2,07 çekirdek-s/klip)
    gpu = True
    #: Yol yalnızca konum; içerik sha256 ile sürüme girer. Dosyayı taşımak
    #: yeniden ölçüm gerektirmez, içeriğini değiştirmek gerektirir.
    version_ignore = ("model_path",)
    produces_metrics = ("dnsmos_sig", "dnsmos_bak", "dnsmos_ovrl")

    def setup(self) -> None:
        from concurrent.futures import ThreadPoolExecutor

        # Yol da özet de konfigden gelir; koda gömülü mükerrer varsayılan
        # yok (run_boilerplate'in 31 Ağu'da temizlenen sapma sınıfı).
        if not self.opts.get("model_path"):
            raise RuntimeError("dnsmos.model_path konfigde yok")
        path = resolve_model_path(str(self.opts["model_path"]))
        want = self.opts.get("model_sha256")
        if not want:
            raise RuntimeError("dnsmos.model_sha256 konfigde yok: ağırlık sabitlenmeden ölçüm koşmaz")
        got = hashlib.sha256(path.read_bytes()).hexdigest()
        if got != str(want):
            raise RuntimeError(f"dnsmos modeli beklenen özetle uyuşmuyor: {path} sha256={got}, beklenen {want}")
        self.sess = load_session(str(path), str(self.cfg.get("runtime.device", "cuda:0")))
        # Çözme ve yeniden örnekleme CPU işi; GPU çıkarım yaparken sonraki
        # klipler iş parçacıklarında hazırlanır (music aşamasındaki desen).
        self.prefetch = ThreadPoolExecutor(max(1, int(self.cfg.get("runtime.clip_prefetch_threads", 4))))

    def teardown(self) -> None:
        self.prefetch.shutdown(wait=True)
        self.sess = None

    def process_clips(self, clips: Sequence[Mapping[str, Any]]) -> Sequence[Mapping[str, Any]]:
        wins = list(self.prefetch.map(lambda c: clip_windows(c["audio"]), clips))
        ok = [i for i, w in enumerate(wins) if w is not None]
        scores = score_clips(self.sess, [wins[i] for i in ok])
        rows: list[dict[str, Any]] = [{"id": c["id"], "metrics": {}, "flags": []} for c in clips]
        for i, s in zip(ok, scores):
            rows[i]["metrics"] = s
        self.validate_output(rows)
        return rows
