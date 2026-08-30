import textwrap

import pytest

from kiraat.config import Config, ConfigError

DEFAULT = "configs/default.yaml"


def test_varsayilan_konfig_yuklenir():
    cfg = Config.load(DEFAULT)
    assert cfg.get("prepare.target_sr") == 24000
    assert cfg.get("events.gate_synthetic") is False


def test_segment_konfigi_dataclassa_donuyor():
    seg = Config.load(DEFAULT).segment_config()
    assert seg.target_sec == 7.0
    assert seg.max_sec == 15.0


def test_politika_kurallari_okunuyor():
    policy = Config.load(DEFAULT).policy()
    assert policy.version == "4"
    assert policy.rules
    ok, reasons = policy.evaluate(
        {"speech_ratio": 0.9, "clip_ratio": 0.0, "internal_silence_sec": 0.2,
         "word_confidence": 0.9},
        [],
    )
    assert ok, reasons


def test_bilinmeyen_bolum_hata_verir(tmp_path):
    p = tmp_path / "c.yaml"
    p.write_text("paths: {}\nsegmnet: {}\n", encoding="utf-8")
    with pytest.raises(ConfigError, match="segmnet"):
        Config.load(p)


def test_bilinmeyen_segment_anahtari_hata_verir(tmp_path):
    p = tmp_path / "c.yaml"
    p.write_text(textwrap.dedent("""
        segment:
          target_sec: 9.0
          hedef_sure: 9.0
    """), encoding="utf-8")
    with pytest.raises(ConfigError, match="hedef_sure"):
        Config.load(p).segment_config()


def test_politikanin_her_kurali_uretilen_bir_sutuna_bakiyor():
    """Politika, hiçbir aşamanın üretmediği bir ölçüme kural koyamaz.

    `dnsmos_ovrl` kuralı `allow_missing: true` ile tam bir örneklemde
    (12.958 klip) hiç tetiklenmedi: DNSMOS aşaması bağlı değil, sütun hiç
    yazılmadı, kural sessizce geçti. Politika "DNSMOS ≥ 3,0 uygulandı" gibi
    okunuyordu. Kural ancak sütunu üreten aşama bağlanınca geri konabilir.
    """
    from kiraat import schema

    known = set(schema.column_names())
    policy = Config.load(DEFAULT).policy()
    unknown = [r.metric for r in policy.rules if r.metric and r.metric not in known]
    assert not unknown, f"şemada olmayan ölçüme kural: {unknown}"
