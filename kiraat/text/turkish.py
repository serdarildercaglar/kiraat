"""Türkçeye özgü harf işlemleri.

`str.lower()` ve `str.upper()` Türkçede yanlış çalışır: 'I' → 'i' olmalı değil
'ı' olmalı, 'i' → 'İ' olmalı değil 'I' olmamalı. Metin politikasının her yeri
bu iki fonksiyonu kullanır; doğrudan `str.lower()` çağrılmaz.
"""

from __future__ import annotations

_LOWER_MAP = str.maketrans("IİÇĞÖŞÜ", "ıiçğöşü")
_UPPER_MAP = str.maketrans("ıiçğöşü", "IİÇĞÖŞÜ")

# Cümle sonu sayılabilecek noktalama. Kapanış tırnak ve parantezleri de
# içerir, çünkü '... dedi."' bir cümle sonudur.
SENTENCE_END = frozenset(".!?…")
CLOSERS = frozenset('"\'»”’)]}')

VOWELS = frozenset("aeıioöuü")
FRONT_VOWELS = frozenset("eiöü")


def lower(text: str) -> str:
    return text.translate(_LOWER_MAP).lower()


def upper(text: str) -> str:
    return text.translate(_UPPER_MAP).upper()


def is_lower_start(text: str) -> bool:
    """Metin küçük harfle mi başlıyor — yani cümle ortasından mı giriyor.

    Rakam, tırnak veya noktalama ile başlayan metin 'kırık' sayılmaz; bunlar
    meşru cümle başlangıçlarıdır.
    """
    for ch in text:
        if ch.isalpha():
            return ch == lower(ch) and ch != upper(ch)
        if ch.isdigit():
            return False
    return False


def has_sentence_end(text: str) -> bool:
    """Metin cümle sonu noktalamasıyla mı bitiyor (kapanış tırnakları hoş görülür)."""
    stripped = text.rstrip()
    while stripped and stripped[-1] in CLOSERS:
        stripped = stripped[:-1].rstrip()
    return bool(stripped) and stripped[-1] in SENTENCE_END
