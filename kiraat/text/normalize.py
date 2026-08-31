"""TTS için Türkçe metin normalizasyonu.

v1'de `text_normalized` alanı `text` ile bayt bayt aynıydı: yuva vardı, içi
boştu. Bir TTS korpusunda sayıların, kısaltmaların ve simgelerin okunuşa
çevrilmesi işin yarısıdır, çünkü model "1923" dizgesini değil "bin dokuz yüz
yirmi üç" sesini öğrenmek zorundadır.

Sözleşme üç alanlıdır ve üçü de yayımlanır:
  text_raw     ASR çıktısı, dokunulmamış
  text         hafif temizlik (boşluk, tırnak, tekrar eden noktalama)
  text_spoken  okunuşa çevrilmiş hâli — eğitimde kullanılacak olan
"""

from __future__ import annotations

import re

from .sentences import NUMBER_LABELS, ORDINAL_MAX_DIGITS
from .turkish import lower

ONES = ("", "bir", "iki", "üç", "dört", "beş", "altı", "yedi", "sekiz", "dokuz")
TENS = ("", "on", "yirmi", "otuz", "kırk", "elli", "altmış", "yetmiş", "seksen", "doksan")
SCALES = ((10**12, "trilyon"), (10**9, "milyar"), (10**6, "milyon"), (1000, "bin"), (100, "yüz"))

#: Sıra sayısı eki, kardinalin son sözcüğüne bakılarak verilir.
ORDINAL_SUFFIX = {
    "bir": "birinci", "iki": "ikinci", "üç": "üçüncü", "dört": "dördüncü",
    "beş": "beşinci", "altı": "altıncı", "yedi": "yedinci", "sekiz": "sekizinci",
    "dokuz": "dokuzuncu", "on": "onuncu", "yirmi": "yirminci", "otuz": "otuzuncu",
    "kırk": "kırkıncı", "elli": "ellinci", "altmış": "altmışıncı",
    "yetmiş": "yetmişinci", "seksen": "sekseninci", "doksan": "doksanıncı",
    "yüz": "yüzüncü", "bin": "bininci", "milyon": "milyonuncu",
    "milyar": "milyarıncı", "trilyon": "trilyonuncu", "sıfır": "sıfırıncı",
}

ABBREVIATION_EXPANSIONS = {
    "vb.": "ve benzeri", "vs.": "vesaire", "vd.": "ve diğerleri",
    "örn.": "örneğin", "bkz.": "bakınız", "yy.": "yüzyıl",
    "dr.": "doktor", "prof.": "profesör", "doç.": "doçent",
    "av.": "avukat", "sn.": "sayın", "yrd.": "yardımcı",
    "m.ö.": "milattan önce", "m.s.": "milattan sonra",
    "tl": "lira",
}

CURRENCY = {"₺": "lira", "$": "dolar", "€": "avro", "£": "sterlin"}

#: Türk alfabesindeki harf adları (TDK okunuşu); yabancı kısaltmalarda geçen
#: Q/W/X de eklidir. "MI6" → "me i altı", "3G" → "üç ge".
LETTER_NAMES = {
    "A": "a", "B": "be", "C": "ce", "Ç": "çe", "D": "de", "E": "e", "F": "fe",
    "G": "ge", "Ğ": "yumuşak ge", "H": "he", "I": "ı", "İ": "i", "J": "je",
    "K": "ke", "L": "le", "M": "me", "N": "ne", "O": "o", "Ö": "ö", "P": "pe",
    "R": "re", "S": "se", "Ş": "şe", "T": "te", "U": "u", "Ü": "ü", "V": "ve",
    "Y": "ye", "Z": "ze", "Q": "kü", "W": "çift ve", "X": "iks",
}

_ALNUM_TOKEN = re.compile(r"\b[0-9A-ZÇĞİÖŞÜ][0-9A-ZÇĞİÖŞÜ-]*\b")

_NUM = r"\d{1,3}(?:\.\d{3})+|\d+"


def number_to_words(n: int) -> str:
    """Tam sayıyı Türkçe okunuşuna çevir."""
    if n == 0:
        return "sıfır"
    parts: list[str] = []
    if n < 0:
        parts.append("eksi")
        n = -n
    for value, name in SCALES:
        if n >= value:
            count, n = divmod(n, value)
            # 'bir yüz' ve 'bir bin' denmez; 'bir milyon' denir.
            if not (count == 1 and value in (100, 1000)):
                parts.append(number_to_words(count))
            parts.append(name)
    if n >= 10:
        parts.append(TENS[n // 10])
        n %= 10
    if n > 0:
        parts.append(ONES[n])
    return " ".join(p for p in parts if p)


def ordinal_to_words(n: int) -> str:
    """'3' → 'üçüncü'. Ek yalnızca son sözcüğe uygulanır."""
    words = number_to_words(n).split()
    last = words[-1]
    if last not in ORDINAL_SUFFIX:
        raise ValueError(f"sira sayisi uretilemedi: {n}")
    return " ".join(words[:-1] + [ORDINAL_SUFFIX[last]])


def _int(token: str) -> int:
    return int(token.replace(".", ""))


def spell_alphanumeric(token: str) -> str | None:
    """Harf+rakam belirtecini okunuşa çevir: "3G" → "üç ge", "F-16" → "fe on altı".

    Kural bilinçli olarak dar: yalnızca BÜYÜK harfler (kısaltma görünümü),
    en çok 4 harf ve 4 basamak. "SAYI-5" gibi gerçek kelime + sayı bileşimleri
    nadiren de olsa yanlış heceleyebilir; küçük harfli karışımlara ("mp3") ve
    uzun kelimelere hiç dokunulmaz. İngilizce okunan markalar ("MI6" aslında
    'em ay siks') Türkçe harf adlarıyla yaklaşıklanır — ASR metninden gerçek
    okunuş bilinemez, sözleşme TDK harf adlarıdır.
    """
    letters = [c for c in token if c.isalpha()]
    digit_runs = re.findall(r"\d+", token)
    if not letters or not digit_runs:
        return None
    if len(letters) > 4 or any(len(r) > 4 for r in digit_runs):
        return None
    parts: list[str] = []
    # findall eşleşmeyen karakterleri (tire) zaten atlar.
    for piece in re.findall(r"\d+|[^\d-]", token):
        if piece.isdigit():
            parts.append(number_to_words(int(piece)))
        else:
            name = LETTER_NAMES.get(piece)
            if name is None:
                return None
            parts.append(name)
    return " ".join(parts)


def _collapse(text: str) -> str:
    text = text.replace(" ", " ")
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"([.,!?;:])\1{1,}", r"\1", text)
    return text.strip()


def light_clean(text: str) -> str:
    """`text` alanı: yalnızca boşluk ve tekrarlı noktalama temizliği.

    Sayılar, kesme işaretleri ve özgün noktalama korunur — v1'in metin
    politikası da böyleydi ve bu kısmı doğruydu.
    """
    return _collapse(text)


def to_spoken(text: str) -> str:
    """`text_spoken` alanı: okunuşa çevrilmiş metin."""
    out = _collapse(text)

    # Kısaltmalar; en uzundan başlayarak, sözcük sınırında.
    for abbr in sorted(ABBREVIATION_EXPANSIONS, key=len, reverse=True):
        pattern = re.compile(r"(?<![\w.])" + re.escape(abbr) + r"(?!\w)", re.IGNORECASE)
        out = pattern.sub(ABBREVIATION_EXPANSIONS[abbr], out)

    # Yüzde: '%50' ve '% 50'.
    out = re.sub(rf"%\s*({_NUM})", lambda m: "yüzde " + number_to_words(_int(m.group(1))), out)

    # Para birimi simgeleri sayıdan sonra okunur: '50₺' → 'elli lira'.
    for sym, word in CURRENCY.items():
        out = re.sub(
            rf"({_NUM})\s*{re.escape(sym)}",
            lambda m, w=word: f"{number_to_words(_int(m.group(1)))} {w}",
            out,
        )
        out = re.sub(
            rf"{re.escape(sym)}\s*({_NUM})",
            lambda m, w=word: f"{number_to_words(_int(m.group(1)))} {w}",
            out,
        )

    # Saat: '14:30' → 'on dört otuz', '09:00' → 'dokuz sıfır sıfır' değil 'dokuz'.
    def _time(m: re.Match[str]) -> str:
        hh, mm = int(m.group(1)), int(m.group(2))
        if mm == 0:
            return number_to_words(hh)
        return f"{number_to_words(hh)} {number_to_words(mm)}"

    out = re.sub(r"\b([01]?\d|2[0-3]):([0-5]\d)\b", _time, out)

    # Ondalık: '1,5' → 'bir virgül beş'.
    out = re.sub(
        rf"({_NUM}),(\d+)",
        lambda m: f"{number_to_words(_int(m.group(1)))} virgül {number_to_words(int(m.group(2)))}",
        out,
    )

    # Harf+rakam belirteçleri: '3G' → 'üç ge', 'MI6' → 'me i altı'. Sayı
    # kurallarından önce koşar ki 'F-16'nın 16'sı çıplak sayı sayılmasın.
    out = _ALNUM_TOKEN.sub(lambda m: spell_alphanumeric(m.group(0)) or m.group(0), out)

    # Sıra sayısı: '3.' — ardından küçük harfli sözcük gelirse.
    out = re.sub(
        rf"\b({_NUM})\.(?=\s+[a-zçğıöşü])",
        lambda m: ordinal_to_words(_int(m.group(1))),
        out,
    )

    # Sıra sayısı, özel isim önünde: '1. Naip' → 'birinci Naip'. Cümle sınırı
    # kuralıyla aynı sözleşme (text/sentences.py, ortak sabitler): 1-3
    # basamak sıra sayısıdır; 4 basamak ('... bitti 1918. Yeni ...') cümle
    # sonu olabilir. Sayaç sözcüğünden sonra gelen sayı ise addır ve
    # kardinal kalır: 'Bölüm 5. Ali...' → 'Bölüm beş. Ali...'.
    def _ordinal_caps(m: re.Match[str], text: str) -> str:
        before = text[:m.start()].rstrip().rsplit(None, 1)
        if before and lower(before[-1].strip("\"'«»“”’()[]")) in NUMBER_LABELS:
            return m.group(0)
        return ordinal_to_words(int(m.group(1)))

    out = re.sub(
        rf"\b(\d{{1,{ORDINAL_MAX_DIGITS}}})\.(?=\s+[A-ZÇĞİÖŞÜ])",
        lambda m, _t=out: _ordinal_caps(m, _t),
        out,
    )

    # Kalan tam sayılar.
    out = re.sub(rf"\b({_NUM})\b", lambda m: number_to_words(_int(m.group(1))), out)

    return _collapse(out)
