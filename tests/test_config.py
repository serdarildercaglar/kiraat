import textwrap

import pytest

from kiraat.config import Config, ConfigError

DEFAULT = "configs/default.yaml"


def test_varsayilan_konfig_yuklenir():
    cfg = Config.load(DEFAULT)
    assert cfg.get("prepare.target_sr") == 24000
    assert cfg.get("asr.language") == "tr"


def test_konfigde_okunmayan_anahtar_yok():
    """Konfig yalnızca uygulanan şeyi ilan etmeli.

    30 Ağu 2026'da on üç anahtar hiçbir kod tarafından okunmuyordu:
    `export.max_hours_per_channel` (uygulansa korpusu yarıya indirecek bir
    tavan), `music.audioset_labels` (etiketler koda gömülüydü),
    `dnsmos.enabled: true` (aşama yok), `runtime.max_clips`, `clip_qc.enabled`
    ve diğerleri. Bu yalnızca dağınıklık değil: okunmayan bir anahtarı
    değiştirmek aşamanın sürüm özetini değiştirdiği için bütün korpusu
    yeniden koşturur ve hiçbir şeyi değiştirmez.
    """
    from pathlib import Path

    import yaml

    from kiraat.segment import SegmentConfig

    root = Path(__file__).resolve().parents[1]
    cfg = yaml.safe_load((root / DEFAULT).read_text(encoding="utf-8"))
    src = "\n".join(p.read_text(encoding="utf-8") for p in (root / "kiraat").rglob("*.py"))
    okunmayan = []
    for section, body in cfg.items():
        if not isinstance(body, dict):
            continue
        for key in body:
            if any(pat in src for pat in (f'"{key}"', f"'{key}'", f"{section}.{key}")):
                continue
            # `segment` bölümü SegmentConfig'e olduğu gibi açılır.
            if section == "segment" and key in SegmentConfig.__dataclass_fields__:
                continue
            okunmayan.append(f"{section}.{key}")
    assert not okunmayan, f"konfigde hiçbir kodun okumadığı anahtar(lar): {okunmayan}"


def test_segment_konfigi_dataclassa_donuyor():
    seg = Config.load(DEFAULT).segment_config()
    assert seg.target_sec == 7.0
    assert seg.max_sec == 15.0


def test_politika_kurallari_okunuyor():
    policy = Config.load(DEFAULT).policy()
    assert policy.version == "6"
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
