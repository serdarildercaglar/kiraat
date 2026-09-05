"""Bozuk kelime damgası kaydın tamamını düşürmemeli.

Rakamlar hizalanmaz (kabul edilmiş sınır, defter 30 Ağu 2026): o kelimelerin
damgası Whisper yedeğine düşer ve Whisper'ın damgası geriye atlayabilir.
3 Eyl 2026 tam koşusunda 1.107 hizalanmış kaynağın %27,7'sinde en az bir
atlama ölçüldü ve iki ayrı yerde kaydın tamamını düşürdü:

  1. `segment`: klip ters uzunluk alıyor (`end <= start`) ve bölütleme
     `sifir/eksi sureli klip` hatası veriyordu — src00249, src00558.
  2. `refine_boundaries`: bağlam dilimi boşalıyor ve `np.percentile`
     "index -1 is out of bounds for axis 0 with size 0" veriyordu —
     src00613, src00891.

Dördü de 3,9–5,6 saatlik kayıtlardı, toplam 20,12 saat düştü. Bu dosyadaki
iki sınama o iki yolu ayrı ayrı tutar.
"""

import numpy as np
import pytest

from kiraat.boundaries import Envelope, RefineConfig, find_boundary_ex
from kiraat.segment import SegmentConfig, Word, segment


def _words(spec):
    return [Word(t, s, e, 0.9) for t, s, e in spec]


def test_geriye_atlayan_damga_ters_klip_uretmez():
    """Rakam damgası geriye atlarsa klip ters uzunluk almamalı.

    Girdi src00249'dan alınmış en küçük gerçek örüntü: '13' hizalanamadığı
    için Whisper damgasına düşmüş ve komşusundan 2 s geriye atlamış. Eski
    kod klibin ucunu ilk ve son kelimeden okuduğu için `start=15736.04`,
    `end=15735.06` üretiyor ve bölütleme kaydın tamamını düşürüyordu;
    `_extent` geri alınırsa bu sınama düşer.
    """
    words = _words([("Anna", 15736.19, 15736.33), ("13", 15734.23, 15734.81)])
    clips = segment(words, SegmentConfig())
    assert clips, "klip üretilmedi"
    bad = [c for c in clips if c.end <= c.start]
    assert not bad, f"ters/sıfır uzunluklu klip: {bad}"
    # Klip, aralığın gerçek uçlarını kapsamalı (pay dışarıya doğru eklenir).
    c = clips[0]
    assert c.start <= 15734.23 and c.end >= 15736.33, f"aralık kapsanmadı: {c}"


def test_geriye_atlayan_damga_uzun_baglamda_da_ters_klip_uretmez():
    """Aynı örüntü gerçek komşularıyla birlikte de temiz kalmalı.

    src00249'un 15717–15752 s aralığı; içinde iki geriye atlama var ('13'
    ve '19'). `_extent` geri alınırsa 'Anna 13' klibi yine ters çıkar.
    """
    words = _words([
        ("olur", 15732.46, 15732.70), ("Dostun", 15733.35, 15734.31),
        ("Anna", 15736.19, 15736.33), ("13", 15734.23, 15734.81),
        ("Mayıs", 15736.49, 15736.75), ("1944", 15736.75, 15737.35),
        ("Cumartesi", 15738.27, 15738.91), ("Sevgili", 15739.91, 15740.25),
        ("Kitty", 15740.29, 15740.51), ("Dün", 15741.29, 15741.47),
        ("babamın", 15741.53, 15741.95), ("doğum", 15742.03, 15742.27),
        ("günüydü", 15742.35, 15742.75), ("Annemle", 15743.65, 15744.05),
        ("babam", 15744.09, 15744.35), ("evleneli", 15744.41, 15744.91),
        ("19", 15744.77, 15745.19), ("yıl", 15745.77, 15745.89),
        ("olmuş", 15745.97, 15746.31),
    ])
    clips = segment(words, SegmentConfig())
    bad = [c for c in clips if c.end <= c.start]
    assert not bad, f"ters/sıfır uzunluklu klip: {bad}"
    for c in clips:
        a, b = c.word_span
        assert c.start <= min(w.start for w in words[a:b]) + 1e-9
        assert c.end >= max(w.end for w in words[a:b]) - 1e-9


def test_geriye_atlayan_damga_sinir_duzeltmesini_cokertmez():
    """`t_next < t_end` olduğunda bağlam dilimi boşalmamalı.

    Düzeltme (`ctx_hi` artık `max(t_next, t_end)`e dayanıyor) geri alınırsa
    `np.percentile` boş dilimde `IndexError` verir ve bu sınama düşer.
    """
    hop = 0.01
    env = Envelope(db=np.linspace(-60.0, -20.0, 4000), hop=hop, frame=0.025)
    t_end, t_next = 30.0, 11.6      # 18,4 s geriye atlama (src00558'deki en büyüğü)
    prev_end, next_start, _ = find_boundary_ex(env, t_end, t_next, SegmentConfig(), RefineConfig())
    assert np.isfinite(prev_end) and np.isfinite(next_start)
    assert next_start >= prev_end


def test_sirali_damgada_davranis_degismez():
    """Damgalar sıralıyken uçlar eskisiyle birebir aynı kalmalı."""
    spec = [("Bir", 0.0, 0.4), ("gün", 0.5, 0.9), ("çok", 1.0, 1.4),
            ("güzel", 1.5, 2.0), ("bir", 2.1, 2.4), ("masal", 2.5, 3.0),
            ("dinledim.", 3.1, 3.9), ("Sonra", 4.0, 4.5), ("uyudum.", 4.6, 5.4)]
    words = _words(spec)
    clips = segment(words, SegmentConfig())
    for c in clips:
        a, b = c.word_span
        assert min(w.start for w in words[a:b]) == words[a].start
        assert max(w.end for w in words[a:b]) == words[b - 1].end
