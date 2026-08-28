from kiraat.dedupe import dedupe_key, duplicate_summary, mark_duplicates


def clip(id_, text, speaker, duration=5.0):
    return {"id": id_, "text": text, "speaker_id": speaker, "duration": duration, "flags": []}


def test_anahtar_noktalama_ve_buyuk_harf_gormez():
    assert dedupe_key("Merhaba, dünya!") == dedupe_key("merhaba dünya")
    assert dedupe_key("IĞDIR") == dedupe_key("ığdır")


def test_ayni_metin_ayni_ses_yinelemedir():
    out = mark_duplicates([
        clip("a", "Seslendiren Vasfiye Sarıkaya", "ch-001", 6.0),
        clip("b", "Seslendiren Vasfiye Sarıkaya", "ch-001", 4.0),
    ])
    assert out[0]["duplicate_of"] is None      # daha uzun olan korunur
    assert out[1]["duplicate_of"] == "a"
    assert "duplicate" in out[1]["flags"]


def test_ayni_metin_farkli_ses_korunur():
    out = mark_duplicates([
        clip("a", "Bir varmış bir yokmuş.", "ch-001"),
        clip("b", "Bir varmış bir yokmuş.", "ch-002"),
    ])
    assert all(c["duplicate_of"] is None for c in out)
    assert all("duplicate" not in c["flags"] for c in out)


def test_bos_metin_gruplanmaz():
    out = mark_duplicates([clip("a", "", "ch-001"), clip("b", "", "ch-001")])
    assert all(c["duplicate_of"] is None for c in out)


def test_ozet():
    out = mark_duplicates([
        clip("a", "aynı", "s", 9.0), clip("b", "aynı", "s", 1.0), clip("c", "aynı", "s", 2.0),
    ])
    assert duplicate_summary(out) == {"duplicates": 2, "kept_groups": 1}
