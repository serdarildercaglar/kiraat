"""Cümle sınırı kurallarının doğrudan testleri.

Bugüne kadar yalnızca `test_segment.py` üzerinden dolaylı sınanıyordu;
kısaltma, baş harf ve sıra sayısı kuralları burada tek tek sınanır.
"""

from __future__ import annotations

from kiraat.text.sentences import is_boundary, sentence_spans


def B(text: str, i: int) -> bool:
    return is_boundary(text.split(), i)


def test_duz_cumle_sonu():
    assert B("Hava güzeldi. Sonra yağmur başladı.", 1)
    assert B("Geldi mi? Gelmedi.", 1)
    assert B("Koş! Hemen.", 0)


def test_kucuk_harf_devami_sinir_degil():
    assert not B("Sayın dinleyiciler, merhaba.", 0)   # virgül cümle bitirmez
    assert not B("Nokta yok burada", 0)


def test_kisaltmalar():
    assert not B("Dr. Ahmet geldi.", 0)
    assert not B("Prof. Dr. Ayşe konuştu.", 0)
    assert not B("M.Ö. 300 yılında oldu.", 0)


def test_tek_harfli_bas_harf():
    assert not B("A. Hamdi Tanpınar yazdı.", 0)


def test_kapanis_tirnagi_hos_gorulur():
    assert B('"Geliyorum." Dedi ve çıktı.', 0)


def test_sira_sayisi_kucuk_harf_takipli():
    assert not B("3. bölüm başlıyor şimdi.", 0)


def test_sira_sayisi_ozel_isim_onunde_sinir_degil():
    """Açık madde 9: '… 1. Naip …' ayrı cümle sayılıp 0,1 s'lik klip oluyordu."""
    assert not B("Sonra 1. Naip tahta çıktı.", 1)
    assert not B("Sultan 3. Selim tahttaydı.", 1)
    assert not B("100. Yıl Marşı çalındı.", 0)


def test_sayac_sozcugu_sonrasi_sayi_cumle_sonu_olabilir():
    """'Bölüm 5.' bir addır: sayı kardinal, noktası cümle sonu (31 Ağu
    incelemesi — aksi hâlde iki cümle tek klip oluyordu)."""
    assert B("Bölüm 5. Ali eve gitti.", 1)
    assert B("Madde 12. Yeni fıkra eklendi.", 1)


def test_dort_basamakli_yil_sinir_kalir():
    assert B("Savaş bitti 1918. Yeni dönem başladı.", 2)


def test_kayit_sonu_ciplak_sayi_sinir_degil():
    assert not B("Sayfa 5.", 1)


def test_ordinal_follower_buyuk_harfli():
    assert not B("1. Bölüm burada başlar.", 0)


def test_spans_kelime_kaybetmez():
    tokens = "Bir vardı. Sonra 1. Naip geldi. Bitti.".split()
    spans = sentence_spans(tokens)
    covered = [i for a, b in spans for i in range(a, b)]
    assert covered == list(range(len(tokens)))
    # "1." tek başına cümle olmadı:
    assert all(b - a > 1 or tokens[a] != "1." for a, b in spans)
