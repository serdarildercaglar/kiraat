"""DNSMOS aşamasının saf parçaları ve model bütünlüğü.

Referans: microsoft/DNS-Challenge `dnsmos_local.py`. Pencereleme ve polinom
eşleme oradan birebir alındı; bu testler o sözleşmeyi sabitler.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np

from kiraat.config import Config
from kiraat.stages.dnsmos import (INPUT_SEC, SR, _P_SIG, load_session,
                                  resolve_model_path, score_clips, score_windows,
                                  windows)

ROOT = Path(__file__).resolve().parents[1]


def _cfg() -> Config:
    return Config.load(ROOT / "configs/default.yaml")


def test_model_dosyasi_konfigdeki_ozete_uyuyor():
    """Depodaki ağırlık ile konfigdeki sha256 kopmasın; kopması bütün
    dnsmos sütunlarının sessizce değişmesi demektir."""
    cfg = _cfg()
    p = resolve_model_path(cfg.get("dnsmos.model_path"))
    assert p.exists(), p
    assert hashlib.sha256(p.read_bytes()).hexdigest() == cfg.get("dnsmos.model_sha256")


def test_pencereleme_referansla_ayni():
    need = int(INPUT_SEC * SR)
    # 2 s: kendi üstüne yinelenir (2→4→8→16 s), int(16-9,01)+1 = 7 pencere.
    assert windows(np.zeros(SR * 2, dtype="float32")).shape == (7, need)
    # 12 s: int(12-9,01)+1 = 3 pencere, 1 s adım.
    assert windows(np.zeros(SR * 12, dtype="float32")).shape == (3, need)
    # Tam 9,01 s: tek pencere.
    assert windows(np.zeros(need, dtype="float32")).shape == (1, need)


def test_polinom_eslemesi_referans_katsayilarla():
    assert abs(float(np.polyval(_P_SIG, 1.0)) - (-0.08397278 + 1.22083953 + 0.0052439)) < 1e-9


def test_gercek_modelle_skor_araligi_ve_belirlenimcilik():
    cfg = _cfg()
    sess = load_session(str(resolve_model_path(cfg.get("dnsmos.model_path"))))
    rng = np.random.default_rng(0)
    wave = (rng.standard_normal(SR * 2) * 0.05).astype("float32")
    out = score_windows(sess, windows(wave))
    assert set(out) == {"dnsmos_sig", "dnsmos_bak", "dnsmos_ovrl"}
    for v in out.values():
        assert 0.5 < v < 5.5, out
    assert out == score_windows(sess, windows(wave))


def test_toplu_cikarim_tek_tek_ile_ayni():
    """Klipler arası paketleme (v2, GPU için) ölçümü değiştirmemeli: her
    klibin skoru tek başına çıkarılanla aynı; dilim sınırı (256 pencere)
    da klip ortasına düşebilmeli."""
    import kiraat.stages.dnsmos as d

    cfg = _cfg()
    sess = load_session(str(resolve_model_path(cfg.get("dnsmos.model_path"))))
    rng = np.random.default_rng(1)
    clips = [windows((rng.standard_normal(SR * s) * 0.05).astype("float32")) for s in (2, 5, 12)]
    tek = [score_windows(sess, w) for w in clips]
    assert score_clips(sess, clips) == tek
    eski = d._RUN_WINDOWS
    d._RUN_WINDOWS = 4          # 7 + 7 + 3 pencere → dilimler klip ortasından geçer
    try:
        assert score_clips(sess, clips) == tek
    finally:
        d._RUN_WINDOWS = eski
    assert score_clips(sess, []) == []
