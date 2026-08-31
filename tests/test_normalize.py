import pytest

from kiraat.text.normalize import number_to_words as N
from kiraat.text.normalize import ordinal_to_words as O
from kiraat.text.normalize import light_clean, to_spoken


@pytest.mark.parametrize("n,expected", [
    (0, "sıfır"), (1, "bir"), (11, "on bir"), (20, "yirmi"),
    (100, "yüz"), (101, "yüz bir"), (200, "iki yüz"),
    (1000, "bin"), (1001, "bin bir"), (2000, "iki bin"),
    (1923, "bin dokuz yüz yirmi üç"),
    (1000000, "bir milyon"),
    (1234567, "bir milyon iki yüz otuz dört bin beş yüz altmış yedi"),
    (-5, "eksi beş"),
])
def test_sayilar(n, expected):
    assert N(n) == expected


@pytest.mark.parametrize("n,expected", [
    (1, "birinci"), (3, "üçüncü"), (4, "dördüncü"), (10, "onuncu"),
    (40, "kırkıncı"), (100, "yüzüncü"), (1000, "bininci"),
    (21, "yirmi birinci"), (1923, "bin dokuz yüz yirmi üçüncü"),
])
def test_sira_sayilari(n, expected):
    assert O(n) == expected


def test_yuzde():
    assert to_spoken("%50 arttı") == "yüzde elli arttı"
    assert to_spoken("% 12 azaldı") == "yüzde on iki azaldı"


def test_kisaltma():
    assert to_spoken("elma, armut vb. meyveler") == "elma, armut ve benzeri meyveler"
    assert "milattan önce" in to_spoken("M.Ö. 300")


def test_ondalik_ve_saat():
    assert to_spoken("1,5 litre") == "bir virgül beş litre"
    assert to_spoken("saat 14:30 oldu") == "saat on dört otuz oldu"
    assert to_spoken("saat 09:00 oldu") == "saat dokuz oldu"


def test_sira_metin_icinde():
    assert to_spoken("3. bölüm başlıyor") == "üçüncü bölüm başlıyor"


def test_binlik_ayirici():
    assert to_spoken("1.234 kişi") == "bin iki yüz otuz dört kişi"


def test_para():
    assert to_spoken("50₺ verdi") == "elli lira verdi"


def test_harf_rakam_belirtecleri():
    """Açık madde 9: 'MI6', 'M5', '3G' okunuşa çevrilmiyordu."""
    assert to_spoken("3G çekmiyor") == "üç ge çekmiyor"
    assert to_spoken("M5 otoyolu uzun") == "me beş otoyolu uzun"
    # ASCII I'nın Türkçe adı 'ı'dır (İ → 'i'); "MI6" noktasız I ile yazılır.
    assert to_spoken("MI6'ya girdi") == "me ı altı'ya girdi"
    assert to_spoken("F-16 havalandı") == "fe on altı havalandı"
    assert to_spoken("A380 indi") == "a üç yüz seksen indi"


def test_harf_rakam_kurali_dar():
    # Rakamsız kısaltma, küçük harfli karışım ve uzun kelime dokunulmaz.
    assert to_spoken("TBMM açıldı") == "TBMM açıldı"
    assert to_spoken("mp3 çalar bozuk") == "mp3 çalar bozuk"


def test_sira_sayisi_ozel_isim_onunde():
    assert to_spoken("Sonra 1. Naip geldi") == "Sonra birinci Naip geldi"
    assert to_spoken("Sultan 3. Selim dönemi") == "Sultan üçüncü Selim dönemi"
    # 4 basamak cümle sonu olabilir; sayı okunur ama nokta kalır.
    assert to_spoken("Savaş bitti 1918. Yeni dönem") == "Savaş bitti bin dokuz yüz on sekiz. Yeni dönem"


def test_light_clean_sayiya_dokunmaz():
    assert light_clean("1923'te  doğdu..") == "1923'te doğdu."
