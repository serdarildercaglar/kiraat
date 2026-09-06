"""Yineleme kuralı: aynı metin + aynı ses yinelemedir, ayrı okuma korunur.

Kural 6 Eylül 2026'da kullanıcı kararıyla keskinleştirildi: okuyanın kimliği
değil, sesin ölçülen kimliği belirler. `work/full-1` manifestinde eski
(metin + kanal) anahtarı 72.839 klip işaretliyordu, yenisi 598; aradaki
62,5 bin klip aynı cümlenin ayrı okumalarıydı.
"""

from kiraat.dedupe import IDENTITY_FIELDS, dedupe_key, duplicate_summary, identity, mark_duplicates


def clip(id_, text, *, duration=5.0, lufs=-23.0, rms=-24.0, peak=-3.0, channel="ch-001"):
    return {"id": id_, "text": text, "channel": channel, "duration": duration, "flags": [],
            "metrics": {"loudness_lufs": lufs, "rms_dbfs": rms, "peak_dbfs": peak}}


def test_anahtar_noktalama_ve_buyuk_harf_gormez():
    assert dedupe_key("Merhaba, dünya!") == dedupe_key("merhaba dünya")
    assert dedupe_key("IĞDIR") == dedupe_key("ığdır")


def test_ayni_metin_ayni_ses_yinelemedir():
    """Kanalın her bölüme koyduğu jenerik: ölçümler birebir aynı."""
    out = mark_duplicates([
        clip("a", "Kitapların büyüsü kumaşlarda hayat buluyor.", duration=3.12, lufs=-12.88),
        clip("b", "Kitapların büyüsü kumaşlarda hayat buluyor.", duration=3.12, lufs=-12.88),
    ])
    assert out[0]["duplicate_of"] is None
    assert out[1]["duplicate_of"] == "a"
    assert "duplicate" in out[1]["flags"]


def test_ayni_metin_ayri_okuma_korunur():
    """Aynı cümlenin iki ayrı okuması — aynı kanalda, hatta aynı kişide bile
    olsa prozodi çeşitliliğidir, yineleme değildir."""
    out = mark_duplicates([
        clip("a", "Hayır.", duration=0.74, lufs=-22.4, rms=-23.94, peak=-4.22),
        clip("b", "Hayır.", duration=0.76, lufs=-21.45, rms=-22.49, peak=-8.02),
    ])
    assert all(c["duplicate_of"] is None for c in out)
    assert all("duplicate" not in c["flags"] for c in out)


def test_tek_alan_ayrilsa_bile_korunur():
    """Süre aynı ama yükseklik farklı: ayrı kayıt, ayrı okuma."""
    out = mark_duplicates([
        clip("a", "Bir varmış bir yokmuş.", lufs=-23.0),
        clip("b", "Bir varmış bir yokmuş.", lufs=-23.1),
    ])
    assert all(c["duplicate_of"] is None for c in out)


def test_kanal_anahtara_girmez():
    """Ses birebir aynıysa iki ayrı kanalda da aynı kaydın kopyasıdır."""
    out = mark_duplicates([
        clip("a", "Seslendiren Vasfiye Sarıkaya", channel="ch-001"),
        clip("b", "Seslendiren Vasfiye Sarıkaya", channel="ch-002"),
    ])
    assert out[1]["duplicate_of"] == "a"


def test_olcumu_eksik_klip_yineleme_sayilmaz():
    """Okunamayan sesin ses kimliği yoktur; kimliksiz klip gruplanmaz."""
    a = clip("a", "aynı metin")
    b = clip("b", "aynı metin")
    b["metrics"] = {"loudness_lufs": None, "rms_dbfs": -24.0, "peak_dbfs": -3.0}
    assert identity(b, IDENTITY_FIELDS) is None
    out = mark_duplicates([a, b])
    assert all(c["duplicate_of"] is None for c in out)


def test_bos_metin_gruplanmaz():
    out = mark_duplicates([clip("a", ""), clip("b", "")])
    assert all(c["duplicate_of"] is None for c in out)


def test_ozet():
    out = mark_duplicates([clip("a", "aynı"), clip("b", "aynı"), clip("c", "aynı")])
    assert duplicate_summary(out) == {"duplicates": 2, "kept_groups": 1}
