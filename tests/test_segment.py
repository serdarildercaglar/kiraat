"""Bölütleyicinin sözleşmesi: hiçbir klip cümle ortasından başlamaz."""

from __future__ import annotations

import pytest

from kiraat.segment import Clip, SegmentConfig, Word, segment
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
