"""Taban kolun (sessizlik hizalı kesim) sözleşmesi.

Bu kol ablasyonda cümle hizalı kesimin karşısına konur; ölçüm ancak iki kol
aynı süre ayarlarını paylaşırsa kesim ölçütünü yalıtır.
"""

import pytest

from kiraat.config import Config
from kiraat.segment import Word
from kiraat.segment_vad import assign_words, segment_by_silence, segment_vad


@pytest.fixture
def cfg():
    return Config.load("configs/default.yaml").segment_config()


def test_kisa_bosluk_birlestirir_uzun_bosluk_keser(cfg):
    # 0,5 s boşluk birleştirme sınırının (1,2 s) altında; 3 s üstünde.
    spans = segment_by_silence([(0.0, 3.0), (3.5, 6.0), (9.0, 12.0)], cfg)
    assert [(s, e) for s, e, _ in spans] == [(0.0, 6.0), (9.0, 12.0)]


def test_tavani_asan_tek_bolge_sert_kesilir(cfg):
    """Nefessiz okunan 40 s: tavanda sert kesilir ve işaretlenir —
    cümle ortasından kesmenin taban koldaki karşılığı."""
    spans = segment_by_silence([(0.0, 40.0)], cfg)
    assert len(spans) == 3
    assert [round(e - s, 2) for s, e, _ in spans] == [15.0, 15.0, 10.0]
    assert [f for _, _, f in spans][:2] == [("hard_cut",), ("hard_cut",)]


def test_asgari_sureden_kisa_parca_atilir(cfg):
    assert segment_by_silence([(0.0, 0.8)], cfg) == []


def test_kelime_orta_noktasina_gore_atanir(cfg):
    words = [Word("Bir", 0.0, 0.5), Word("cümle.", 0.6, 1.2), Word("İkinci", 5.0, 5.6)]
    clips = assign_words([(0.0, 2.0, ()), (4.5, 6.0, ())], words)
    assert [c.text for c in clips] == ["Bir cümle.", "İkinci"]
    assert [c.word_span for c in clips] == [(0, 2), (2, 3)]


def test_ayni_ayarlarla_paylar_cumle_koluyla_ayni(cfg):
    clips = segment_vad([(2.0, 8.0)], [Word("tek", 3.0, 3.4)], cfg)
    assert clips[0].start == pytest.approx(2.0 - cfg.lead_pad_sec)
    assert clips[0].end == pytest.approx(8.0 + cfg.trail_pad_sec)
