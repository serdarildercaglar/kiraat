"""Konuşmacı gömmesi: kayıt başına ses kimliği ölçümü.

Aşama yalnızca ÖLÇER: kayıttan birkaç klip seçer, konuşmacı doğrulama
modeliyle (ECAPA-TDNN) gömer, kaydın merkez vektörünü ve kayıt içi
tutarlılığını yazar. Kim kimdir kararı — yani kümeleme — burada verilmez;
korpusun tamamını gördükten sonra `scripts/cluster_speakers.py` verir ve
eşiğini veriden çıkarır. v1'in kusuru (`docs/DESIGN.md` madde 8) küme
sayısını 64'te sabitlemekti; burada küme sayısı hiçbir yerde verilmiyor.

Kayıt içi tutarlılık ayrıca bir ölçüm: kaydın klipleri birbirine benzemezse
kayıtta birden çok ses var demektir (röportaj, çok sesli okuma) ve o kayıt
kümelemede tek bir konuşmacı gibi ele alınamaz.

Ölçülen dağılımlar (6 Eyl 2026, 105 kayıt): kayıt içi klip-klip benzerliği
medyan 0,742; aynı kanalın iki kaydı 0,872; farklı kanal 0,179. Eşit hata
noktası 0,483 ve oradaki hata %1,9.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

import numpy as np

from ..base import SourceStage, register


def hash_order(paths: Sequence[Path], seed: str) -> list[Path]:
    """Belirlenimci sıra: kaydın kimliğiyle tohumlanmış özet.

    Rastgele sayı üreteci yerine özet kullanılır ki seçim koşudan koşuya,
    makineden makineye aynı olsun ve yeniden koşmak gömmeyi değiştirmesin.
    """
    return sorted(paths, key=lambda p: hashlib.sha256(f"{seed}:{p.name}".encode()).hexdigest())


def pick_clips(paths: Sequence[Path], n: int, seed: str,
               keep: "Callable[[Path], bool] | None" = None) -> list[Path]:
    """Sıradaki ilk `n` uygun klip.

    Uygunluk (süre eşiği) sırayla ve gerektiği kadar sınanır: bir kayıtta
    binlerce klip var ve hepsinin süresini okumak aşamayı klip sayısına
    bağımlı kılıyordu — 2.698 kayıtta ~2 saat, oysa gömme çıkarımının
    kendisi dakikalar (6 Eyl 2026 ölçümü). Sıra özetten geldiği için
    "ilk n uygun" seçimi de belirlenimcidir.
    """
    out: list[Path] = []
    for p in hash_order(paths, seed):
        if keep is None or keep(p):
            out.append(p)
            if len(out) == n:
                break
    return sorted(out)


def consistency(emb: np.ndarray) -> dict[str, float]:
    """Kayıt içi benzerlik: klip gömmeleri arasındaki kosinüs istatistikleri."""
    sims = emb @ emb.T
    iu = np.triu_indices(len(emb), k=1)
    vals = sims[iu]
    return {"speaker_consistency": round(float(vals.mean()), 4),
            "speaker_consistency_min": round(float(vals.min()), 4)}


@register
class SpeakerStage(SourceStage):
    name = "speaker"
    version = "1"
    gpu = True
    depends_on = ("segment",)
    config_sections = ("speaker",)

    def setup(self) -> None:
        from speechbrain.inference.speaker import EncoderClassifier

        self.device = str(self.cfg.get("runtime.device", "cuda:0"))
        self.sr = 16000
        self.encoder = EncoderClassifier.from_hparams(
            source=str(self.opts["model"]), savedir=str(self.opts.get("savedir", "models/ecapa")),
            run_opts={"device": self.device})

    def teardown(self) -> None:
        self.encoder = None

    def _embed(self, paths: Sequence[Path]) -> np.ndarray:
        import torch
        import torchaudio

        waves = []
        for p in paths:
            wave, sr = torchaudio.load(str(p))
            wave = wave.mean(dim=0)
            if sr != self.sr:
                wave = torchaudio.functional.resample(wave, sr, self.sr)
            waves.append(wave)
        batch = int(self.opts.get("batch", 8))
        order = sorted(range(len(waves)), key=lambda i: len(waves[i]))
        out: dict[int, Any] = {}
        for start in range(0, len(order), batch):
            idx = order[start:start + batch]
            chunk = [waves[i] for i in idx]
            n = max(len(w) for w in chunk)
            padded = torch.stack([torch.nn.functional.pad(w, (0, n - len(w))) for w in chunk])
            lens = torch.tensor([len(w) / n for w in chunk])
            with torch.no_grad():
                e = self.encoder.encode_batch(padded.to(self.device), wav_lens=lens.to(self.device))
            e = torch.nn.functional.normalize(e.squeeze(1), dim=-1).cpu()
            for k, i in enumerate(idx):
                out[i] = e[k]
        return torch.stack([out[i] for i in range(len(waves))]).numpy()

    def process_source(self, source: Mapping[str, Any]) -> Sequence[Mapping[str, Any]]:
        import soundfile as sf

        work = Path(self.cfg.get("paths.work_root"))
        clip_dir = work / "clips" / source["channel"] / f"src{source['id']:05d}"
        min_sec = float(self.opts.get("min_sec", 3.0))
        want = int(self.opts.get("clips", 12))

        def long_enough(p: Path) -> bool:
            try:
                info = sf.info(str(p))
            except Exception:
                return False
            return info.frames / info.samplerate >= min_sec

        picked = pick_clips(sorted(clip_dir.glob("*.flac")), want,
                            seed=f"{self.opts.get('seed', 'kiraat')}:{source['id']}",
                            keep=long_enough)
        if len(picked) < 2:
            # Kaydın kimliği kurulamıyor; ölçüm yok, karar da yok.
            return [{"speaker_embedding": None, "speaker_n_clips": len(picked)}]

        emb = self._embed(picked)
        center = emb.mean(0)
        center = center / max(1e-9, float(np.linalg.norm(center)))
        out_dir = work / "speaker"
        out_dir.mkdir(parents=True, exist_ok=True)
        dst = out_dir / f"src{source['id']:05d}.npz"
        np.savez_compressed(dst, center=center.astype(np.float32), clips=emb.astype(np.float32),
                            names=np.array([p.name for p in picked]))
        return [{"speaker_embedding": str(dst), "speaker_n_clips": len(picked),
                 **consistency(emb)}]
