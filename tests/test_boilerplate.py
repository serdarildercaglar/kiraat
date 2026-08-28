from kiraat.boilerplate import find_spans, mine
from kiraat.segment import SegmentConfig, Word, segment


def toks(text: str) -> list[str]:
    return text.split()


def test_kanal_kunyesi_madenlenir():
    recs = {
        "a": toks("Ferman Ömer Seyfettin seslendiren Vasfiye Sarıkaya. Sanki bir tufandı. " + "kelime " * 50 + "Son. Seslendiren Vasfiye Sarıkaya."),
        "b": toks("Kaşağı Ömer Seyfettin seslendiren Vasfiye Sarıkaya. At ahırdaydı. " + "başka " * 50 + "Bitti. Seslendiren Vasfiye Sarıkaya."),
        "c": toks("Pembe İncili Kaftan seslendiren Vasfiye Sarıkaya. Padişah oturdu. " + "sözcük " * 50 + "Son. Seslendiren Vasfiye Sarıkaya."),
    }
    mined = mine(recs, min_recordings=3, min_words=3, max_words=6)
    phrases = [p for p, _ in mined]
    assert ("seslendiren", "vasfiye", "sarıkaya") in phrases
    # Kayda özgü başlık kelimeleri ("ferman") hiçbir ifadeye girmez.
    assert not any("ferman" in p for p in phrases)


def test_span_bulma_ve_bolutleyiciye_baglama():
    text = "Ferman Ömer Seyfettin seslendiren Vasfiye Sarıkaya Sanki bir tufandı. Gök delinmiş gibiydi."
    tokens = toks(text)
    spans = find_spans(tokens, [("seslendiren", "vasfiye", "sarıkaya")])
    assert spans == [(3, 6)]
    words = [Word(t, i * 0.5, i * 0.5 + 0.5) for i, t in enumerate(tokens)]
    clips = segment(words, SegmentConfig(min_sec=0.5, target_sec=4.0, max_sec=8.0), boilerplate=spans)
    bp = [c for c in clips if "boilerplate" in c.flags]
    assert len(bp) == 1 and bp[0].text == "seslendiren Vasfiye Sarıkaya"
    # Künye komşularıyla birleşmez; ilk gerçek cümle künyeden temiz başlar.
    after = [c for c in clips if c.word_span[0] == 6]
    assert after and after[0].text.startswith("Sanki bir tufandı.")
