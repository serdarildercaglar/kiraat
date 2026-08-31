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

DEFAULT_MODEL_PATH = "models/dnsmos/sig_bak_ovr.onnx"

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
    num_hops = int(np.floor(len(audio) / SR) - INPUT_SEC) + 1
    out = []
    for i in range(num_hops):
        seg = audio[int(i * SR): int((i + INPUT_SEC) * SR)]
        if len(seg) >= need:
            out.append(seg[:need])
    return np.stack(out if out else [audio[:need]])


def load_session(model_path: str):
    """Tek iş parçacıklı CPU oturumu; işçi süreç sayısını havuz belirler."""
    import onnxruntime as ort

    opts = ort.SessionOptions()
    opts.intra_op_num_threads = 1
    return ort.InferenceSession(str(model_path), sess_options=opts,
                                providers=["CPUExecutionProvider"])


def score_windows(sess, wins: np.ndarray) -> dict[str, float]:
    """Pencereleri toplu çıkar, polinomla eşle, pencere ortalamasını döndür.

    Referans uygulama gibi ortalama, eşlenmiş değerler üzerinden alınır
    (polinom doğrusal olmadığı için ham ortalamayı eşlemekle aynı değildir).
    """
    raw = sess.run(None, {"input_1": wins.astype(np.float32)})[0]  # (N, 3): sig, bak, ovr
    return {
        "dnsmos_sig": round(float(np.mean(np.polyval(_P_SIG, raw[:, 0]))), 3),
        "dnsmos_bak": round(float(np.mean(np.polyval(_P_BAK, raw[:, 1]))), 3),
        "dnsmos_ovrl": round(float(np.mean(np.polyval(_P_OVR, raw[:, 2]))), 3),
    }


_SESS = None
_SESS_PATH: str | None = None


def _measure_one(args: tuple[str, str, str]) -> dict[str, Any]:
    """Tek klip; işçi süreçlerinde çalışır, oturumu süreç başına bir kez kurar.

    Okunamayan klip işaretlenmez — `unreadable_audio` işaretinin sahibi
    `clip_qc`; burada yalnızca ölçüm boş bırakılır.
    """
    import soundfile as sf
    import torch
    import torchaudio

    global _SESS, _SESS_PATH
    clip_id, path, model_path = args
    if _SESS is None or _SESS_PATH != model_path:
        torch.set_num_threads(1)
        _SESS = load_session(model_path)
        _SESS_PATH = model_path
    try:
        data, sr = sf.read(path, dtype="float32", always_2d=True)
    except Exception:
        return {"id": clip_id, "metrics": {}, "flags": []}
    mono = data.mean(axis=1)
    if mono.size == 0:
        return {"id": clip_id, "metrics": {}, "flags": []}
    wave = torch.from_numpy(mono)
    if sr != SR:
        wave = torchaudio.functional.resample(wave, sr, SR)
    return {"id": clip_id, "metrics": score_windows(_SESS, windows(wave.numpy())), "flags": []}


@register
class DnsmosStage(ClipStage):
    """Klip başına DNSMOS P.835 skorları. Karar vermez."""

    name = "dnsmos"
    depends_on = ("segment",)
    version = "1"
    #: Yol yalnızca konum; içerik sha256 ile sürüme girer. Dosyayı taşımak
    #: yeniden ölçüm gerektirmez, içeriğini değiştirmek gerektirir.
    version_ignore = ("model_path",)
    produces_metrics = ("dnsmos_sig", "dnsmos_bak", "dnsmos_ovrl")

    def setup(self) -> None:
        import multiprocessing as mp

        path = resolve_model_path(str(self.opts.get("model_path", DEFAULT_MODEL_PATH)))
        want = self.opts.get("model_sha256")
        if not want:
            raise RuntimeError("dnsmos.model_sha256 konfigde yok: ağırlık sabitlenmeden ölçüm koşmaz")
        got = hashlib.sha256(path.read_bytes()).hexdigest()
        if got != str(want):
            raise RuntimeError(f"dnsmos modeli beklenen özetle uyuşmuyor: {path} sha256={got}, beklenen {want}")
        self.model_path = str(path)
        self.workers = int(self.cfg.get("runtime.source_workers", 1) or 1)
        self.pool = mp.get_context("spawn").Pool(self.workers) if self.workers > 1 else None

    def teardown(self) -> None:
        if self.pool is not None:
            self.pool.close()
            self.pool.join()
            self.pool = None

    def process_clips(self, clips: Sequence[Mapping[str, Any]]) -> Sequence[Mapping[str, Any]]:
        jobs = [(c["id"], c["audio"], self.model_path) for c in clips]
        rows = list(self.pool.imap(_measure_one, jobs, chunksize=8)) if self.pool else [_measure_one(j) for j in jobs]
        self.validate_output(rows)
        return rows
