"""Bölütleyicinin sözleşmesi: hiçbir klip cümle ortasından başlamaz."""

from __future__ import annotations

import pytest

from kiraat.segment import Clip, SegmentConfig, Word, attach_clitics, segment
from kiraat.text.turkish import has_sentence_end, is_lower_start


def mk(text: str, *, word_sec: float = 0.5, gap: float = 0.0) -> list[Word]:
    """Her kelimeyi sabit süreli yapıp sözde zaman damgası üret."""
    words: list[Word] = []
    t = 0.0
    for tok in text.split():
        words.append(Word(tok, round(t, 3), round(t + word_sec, 3)))
        t += word_sec + gap
    return words


CFG = SegmentConfig(min_sec=1.0, target_sec=4.0, max_sec=8.0)


def test_bos_girdi():
    assert segment([], CFG) == []


def test_hicbir_klip_cumle_ortasindan_baslamaz():
    text = (
        "Bugün hava çok güzeldi. Sabah erkenden yola çıktık. "
        "Yolda uzun uzun konuştuk. Akşam olunca geri döndük. "
        "Herkes çok yorulmuştu ama mutluydu."
    )
    clips = segment(mk(text), CFG)
    assert clips
    for c in clips:
        assert not is_lower_start(c.text), c.text


def test_klipler_cumle_sonunda_biter():
    text = "Bir vardı. İki vardı. Üç vardı. Dört vardı."
    for c in segment(mk(text), CFG):
        assert has_sentence_end(c.text), c.text


def test_uzun_sessizlik_cumleleri_yapistirmaz():
    words = mk("Kısa cümle.") + [
        Word(w.text, w.start + 10.0, w.end + 10.0) for w in mk("Sonraki cümle.")
    ]
    clips = segment(words, CFG)
    assert len(clips) == 2


def test_asiri_uzun_cumle_ic_noktalamadan_bolunur():
    text = "bir iki üç dört beş, altı yedi sekiz dokuz on, on bir on iki on üç on dört."
    clips = segment(mk(text, word_sec=0.6), SegmentConfig(min_sec=0.5, target_sec=3.0, max_sec=5.0))
    assert len(clips) > 1
    assert any("forced_split" in c.flags for c in clips)


def test_bolunemeyen_uzun_cumle_isaretlenir_ama_atilmaz():
    text = "bir iki üç dört beş altı yedi sekiz dokuz on on bir on iki."
    clips = segment(mk(text, word_sec=1.0), SegmentConfig(min_sec=0.5, target_sec=3.0, max_sec=5.0))
    assert len(clips) == 1
    assert "oversize" in clips[0].flags


def test_kisa_klip_birlestirilir_yoksa_isaretlenir():
    clips = segment(mk("Kısa."), SegmentConfig(min_sec=5.0, target_sec=9.0, max_sec=20.0))
    assert len(clips) == 1
    assert "short" in clips[0].flags


def test_klipler_cakismaz_ve_sirali():
    text = " ".join(f"Cümle {i} burada bitiyor." for i in range(20))
    clips = segment(mk(text), CFG)
    for a, b in zip(clips, clips[1:]):
        assert a.end <= b.start + 1e-9, (a, b)


def test_hicbir_kelime_kaybolmaz():
    text = "Bir iki üç. Dört beş altı. Yedi sekiz dokuz on."
    words = mk(text)
    clips = segment(words, CFG)
    covered = [i for c in clips for i in range(*c.word_span)]
    assert covered == list(range(len(words)))


def test_birlestirme_hedefi_asmaz():
    # Her cümle 3 s; hedef 4 s. İki cümle birleşince 6 s olur ve hedefi aşar,
    # dolayısıyla her cümle kendi klibi olmalı. Eski kural "hedefe ulaşana
    # kadar ekle" dediği için 6 s'lik klipler üretiyordu.
    text = " ".join(f"Cümle {i} altı kelime ile burada bitiyor." for i in range(6))
    clips = segment(mk(text), SegmentConfig(min_sec=1.0, target_sec=4.0, max_sec=10.0))
    assert len(clips) == 6
    for c in clips:
        assert c.duration <= 4.0 + 0.25 + 0.15, c


def test_tek_cumle_hedefi_asabilir_ama_maxi_asamaz():
    text = "bir iki üç dört beş altı yedi sekiz dokuz on. Kısa."
    clips = segment(mk(text, word_sec=0.6), SegmentConfig(min_sec=1.0, target_sec=4.0, max_sec=10.0))
    assert clips[0].text.endswith("on.")
    assert 4.0 < clips[0].duration <= 10.0


def test_kesme_isareti_ekleri_birlesir():
    words = [Word("Benjamin", 0, 0.5, 0.9), Word("Button", 0.5, 1.0, 0.8), Word("'ın", 1.0, 1.2, 0.3),
             Word("''Padişahım,", 1.5, 2.0, 0.9), Word("-ı", 2.0, 2.1), Word(".", 2.1, 2.2)]
    out = attach_clitics(words)
    assert [w.text for w in out] == ["Benjamin", "Button'ın", "''Padişahım,-ı."]
    assert out[1].start == 0.5 and out[1].end == 1.2 and out[1].prob == 0.3


def test_uzun_ic_bosluk_noktalamasiz_cumleyi_boler():
    # "Başlık" + 49 s giriş müziği + gerçek cümle; ASR araya noktalama koymadı.
    title = mk("Edgar Allan Poe'dan Kuyu ve Sarkaç")
    body = [Word(w.text, w.start + 52.0, w.end + 52.0) for w in mk("Bitkindim uzun acıyla ölecek gibiydim.")]
    clips = segment(title + body, SegmentConfig(min_sec=0.5, target_sec=7.0, max_sec=15.0))
    assert len(clips) == 2
    assert "gap_split" in clips[0].flags          # başlık: cümle sonu yok → işaretli
    assert "gap_split" not in clips[1].flags      # gerçek cümle bütün → işaretsiz
    assert clips[1].text.startswith("Bitkindim")


def test_pay_komsuyla_bosluğun_ortasini_gecmez():
    # İki cümle arasında yalnızca 0,10 s var; pay 0,15 olsa da sınır ortada durur.
    a = mk("Bir cümle burada bitiyor.")
    b = [Word(w.text, w.start + a[-1].end + 0.10, w.end + a[-1].end + 0.10) for w in mk("Sonraki cümle başlıyor.")]
    clips = segment(a + b, SegmentConfig(min_sec=0.5, target_sec=1.0, max_sec=8.0, lead_pad_sec=0.15, trail_pad_sec=0.25))
    assert len(clips) == 2
    mid = (a[-1].end + b[0].start) / 2
    assert clips[0].end <= mid + 1e-6 and clips[1].start >= mid - 1e-6


def test_noktali_kisaltma_parcalari_birlesir():
    words = [Word("P", 0, .2), Word(".O", .2, .4), Word(".Y", .4, .6), Word(".M.", .6, .8), Word("lağvedildi.", .9, 1.5)]
    assert [w.text for w in attach_clitics(words)] == ["P.O.Y.M.", "lağvedildi."]

