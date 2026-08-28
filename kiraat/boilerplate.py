"""Kanal düzeyinde künye ve anons madenciliği.

v1'de "Son Seslendiren Vasfiye Sarıkaya" eğitim havuzuna 32 kez sızdı,
çünkü hat bu tür metinleri tanımıyordu. Bunlar bir kaydın içeriği değil,
kanalın kalıbıdır: aynı kanalın kayıtlarında, çoğunlukla kaydın başında ve
sonunda, kelimesi kelimesine tekrar eder. Dolayısıyla tek bir kayıttan değil,
kanalın kayıtlarından öğrenilir.

  mine()        kanalın kayıtlarının baş/son bölgelerinde en az
                `min_recordings` ayrı kayıtta geçen en uzun kelime dizilerini
                bulur.
  find_spans()  bir kaydın kelime dizisinde bu ifadelerin geçtiği aralıkları
                verir; bölütleyici bu aralıkları ayrı klip yapar ve
                `boilerplate` işaretler. Silmez.
"""

from __future__ import annotations

from collections import Counter
from typing import Iterable, Mapping, Sequence

from .dedupe import dedupe_key

Phrase = tuple[str, ...]


def normalize_tokens(tokens: Iterable[str]) -> list[str]:
    """Karşılaştırma için: küçük harf, noktalamasız. Boş dize noktalama-only demektir."""
    return [dedupe_key(t) for t in tokens]


def _ngrams(norm: Sequence[str], min_n: int, max_n: int) -> set[Phrase]:
    toks = [t for t in norm if t]
    out: set[Phrase] = set()
    for n in range(min_n, max_n + 1):
        for i in range(len(toks) - n + 1):
            out.add(tuple(toks[i:i + n]))
    return out


def _contains(longer: Phrase, shorter: Phrase) -> bool:
    n = len(shorter)
    return any(longer[i:i + n] == shorter for i in range(len(longer) - n + 1))


def _merge_overlapping(kept: list[tuple[Phrase, int]]) -> list[tuple[Phrase, int]]:
    """Aynı kayıt sayısına sahip, uçları örtüşen ifadeleri tek ifadede birleştir.

    `max_words`'ten uzun bir kalıp (13 kelimelik jingle) iki örtüşen n-gram
    olarak gelir; birleştirilmezse eşleşme birini seçer ve baş kelime dışarıda
    kalır.
    """
    changed = True
    items = list(kept)
    while changed:
        changed = False
        for i in range(len(items)):
            for j in range(len(items)):
                if i == j or items[i][1] != items[j][1]:
                    continue
                a, b = items[i][0], items[j][0]
                for k in range(min(len(a), len(b)) - 1, 0, -1):   # a'nın sonu == b'nin başı
                    if a[-k:] == b[:k]:
                        merged = a + b[k:]
                        items[i] = (merged, items[i][1])
                        del items[j]
                        changed = True
                        break
                if changed:
                    break
            if changed:
                break
    return items


def mine(
    recordings: Mapping[str, Sequence[str]],
    *,
    min_recordings: int = 3,
    min_words: int = 3,
    max_words: int = 12,
    head_words: int | None = 80,
    tail_words: int | None = 80,
    min_ratio: float | None = None,
) -> list[tuple[Phrase, int]]:
    """Kayıt → belirteç dizisi eşlemesinden tekrar eden ifadeleri çıkar.

    Her kaydın yalnızca baş ve son bölgesi taranır (`head_words`/`tail_words`;
    None = tamamı). Eşik: en az `min_recordings` kayıt; `min_ratio` verilirse
    kanal kayıt sayısının o oranı (en az `min_recordings`) — üç kayıtlı
    kanalda 3/3 istemek çok katı, elli kayıtlı kanalda 3/50 çok gevşek.
    Dönen liste (ifade, kaç kayıtta) çiftleridir; aynı sayıda kayıtta geçen
    daha uzun bir ifadenin içinde kalan kısa ifadeler atılır, örtüşenler
    birleştirilir.
    """
    if min_ratio is not None:
        min_recordings = max(min_recordings, int(round(min_ratio * len(recordings))))
    doc_count: Counter[Phrase] = Counter()
    for tokens in recordings.values():
        norm = normalize_tokens(tokens)
        region: list[str] = []
        if head_words is None and tail_words is None:
            region = list(norm)
        else:
            if head_words:
                region += norm[:head_words]
            if tail_words:
                region += norm[-tail_words:] if len(norm) > (head_words or 0) else []
        for gram in _ngrams(region, min_words, max_words):
            doc_count[gram] += 1

    kept = [(g, c) for g, c in doc_count.items() if c >= min_recordings]
    kept.sort(key=lambda gc: (-len(gc[0]), -gc[1], gc[0]))
    maximal: list[tuple[Phrase, int]] = []
    for gram, count in kept:
        if any(count <= c2 and _contains(g2, gram) for g2, c2 in maximal):
            continue
        maximal.append((gram, count))
    merged = _merge_overlapping(maximal)
    merged.sort(key=lambda gc: (-len(gc[0]), -gc[1], gc[0]))
    final: list[tuple[Phrase, int]] = []
    for gram, count in merged:   # birleşme sonrası içeride kalanları at
        if any(count <= c2 and _contains(g2, gram) for g2, c2 in final):
            continue
        final.append((gram, count))
    final.sort(key=lambda gc: (-gc[1], -len(gc[0]), gc[0]))
    return final


def find_spans(tokens: Sequence[str], phrases: Iterable[Phrase]) -> list[tuple[int, int]]:
    """İfadelerin belirteç dizisinde geçtiği, çakışmayan [a, b) aralıkları."""
    norm = normalize_tokens(tokens)
    taken = [False] * len(norm)
    spans: list[tuple[int, int]] = []
    for phrase in sorted(set(map(tuple, phrases)), key=len, reverse=True):
        n = len(phrase)
        if n == 0:
            continue
        i = 0
        while i + n <= len(norm):
            if tuple(norm[i:i + n]) == phrase and not any(taken[i:i + n]):
                spans.append((i, i + n))
                for k in range(i, i + n):
                    taken[k] = True
                i += n
            else:
                i += 1
    return sorted(spans)
