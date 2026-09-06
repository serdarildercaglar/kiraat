"""Konuşmacı aşamasının sözleşmesi: ölçer, karar vermez, belirlenimcidir."""

import numpy as np
import pytest

from kiraat.base import get_stage
from kiraat.config import Config
from kiraat.stages.speaker import consistency, pick_clips


def test_klip_secimi_belirlenimci_ve_sirali(tmp_path):
    paths = [tmp_path / f"{i:05d}.flac" for i in range(50)]
    a = pick_clips(paths, 12, seed="kiraat:7")
    b = pick_clips(paths, 12, seed="kiraat:7")
    assert a == b and len(a) == 12
    assert a == sorted(a)
    # Tohum kaydın kimliğini taşır: başka kayıt başka klip seçer.
    assert pick_clips(paths, 12, seed="kiraat:8") != a


def test_uygunluk_gerektigi_kadar_sinanir(tmp_path):
    """Süre eşiği sırayla sınanır: binlerce klipli kayıtta hepsinin süresini
    okumak aşamayı klip sayısına bağımlı kılıyordu (2.698 kayıtta ~2 saat)."""
    paths = [tmp_path / f"{i:05d}.flac" for i in range(500)]
    bakilan = []

    def keep(p):
        bakilan.append(p)
        return True

    picked = pick_clips(paths, 12, seed="kiraat:7", keep=keep)
    assert len(picked) == 12
    assert len(bakilan) == 12, "gereğinden fazla dosya açıldı"
    # Eşiği geçmeyen dosyalar atlanır, sıradaki denenir.
    atla = {p for p in paths[:400]}
    picked2 = pick_clips(paths, 5, seed="kiraat:7", keep=lambda p: p not in atla)
    assert len(picked2) == 5 and all(p not in atla for p in picked2)


def test_tutarlilik_ayni_sesle_yuksek_karisik_kayitta_dusuk():
    rng = np.random.default_rng(0)
    tek = rng.normal(size=(8, 16)) * 0.05 + np.ones(16)
    tek /= np.linalg.norm(tek, axis=1, keepdims=True)
    assert consistency(tek)["speaker_consistency"] > 0.95

    a = rng.normal(size=(4, 16)) * 0.05 + np.array([1.0] + [0] * 15)
    b = rng.normal(size=(4, 16)) * 0.05 + np.array([0, 1.0] + [0] * 14)
    iki = np.vstack([a, b])
    iki /= np.linalg.norm(iki, axis=1, keepdims=True)
    c = consistency(iki)
    assert c["speaker_consistency"] < 0.6 and c["speaker_consistency_min"] < 0.3


def test_asama_karar_alani_yazmaz_ve_kaynak_asamasidir():
    from kiraat.base import SourceStage

    cls = get_stage("speaker")
    assert issubclass(cls, SourceStage)
    # Küme/konuşmacı kimliği aşamada YOK: kümeleme korpus düzeyinde yapılır.
    src = (cls.__module__, cls.__doc__ or "")
    assert "speaker_id" not in open("kiraat/stages/speaker.py", encoding="utf-8").read()


def test_konfig_bolumu_ve_bagimlilik():
    cfg = Config.load("configs/default.yaml")
    opts = cfg.section("speaker")
    assert opts["clips"] >= 2 and opts["min_sec"] > 0
    assert opts["revision"], "ağırlık revizyonu sabitlenmeli"
    assert get_stage("speaker").depends_on == ("segment",)
