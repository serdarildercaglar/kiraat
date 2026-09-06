"""Taban kol: sessizlik hizalı bölütleme (ablasyon için).

Hattın kesimi cümle sınırındadır; bunun bir kazanç olduğunu iddia etmek
için karşısına ölçülebilir bir alternatif konmalı. Bu modül o alternatifi
uygular: VAD'ın bulduğu konuşma bölgeleri, aradaki sessizliklerde kesilir.
Alanın uzun süre varsayılanı budur ve `kiraat/segment.py`'nin yerine
geçtiği yöntemdir.

Karşılaştırma yalnız kesim ölçütünü yalıtsın diye taban kol, cümle kolunun
**aynı** `SegmentConfig`'ini kullanır: aynı asgari/hedef/tavan süre, aynı
birleştirme boşluğu, aynı paylar. Değişen tek şey, kesimin nerede
yapıldığıdır — sessizlikte mi, cümle sonunda mı.

Metin kesimden sonra atanır: kelime damgasının orta noktası klibin içine
düşüyorsa kelime o klibindir. Böylece iki kol aynı kelime damgalarını
paylaşır ve metin farkı yalnızca sınırların yerinden doğar.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .segment import Word


@dataclass(frozen=True)
class VadClip:
    start: float
    end: float
    text: str
    word_span: tuple[int, int]
    flags: tuple[str, ...] = ()


def segment_by_silence(regions: Sequence[tuple[float, float]], cfg) -> list[tuple[float, float, tuple[str, ...]]]:
    """Konuşma bölgelerini sessizliklerde kes.

    Bölgeler `max_join_gap_sec`'ten kısa boşluklarla ayrılıyorsa aynı klipte
    birleşir; boşluk bundan büyükse ya da klip `max_sec` tavanını aşacaksa
    orada kesilir. Tek başına tavanı aşan bir konuşma bölgesi (nefessiz
    okuma) tavanda SERT kesilir ve `hard_cut` işareti alır — cümle
    ortasından kesmenin taban koldaki karşılığı budur.

    `min_sec`'ten kısa kalan parça atılır; cümle kolunda da öyle olur.
    """
    out: list[tuple[float, float, tuple[str, ...]]] = []

    def emit(start: float, end: float, flags: tuple[str, ...] = ()) -> None:
        while end - start > cfg.max_sec:
            out.append((start, start + cfg.max_sec, flags + ("hard_cut",)))
            start += cfg.max_sec
        if end - start >= cfg.min_sec:
            out.append((start, end, flags))

    cur_start: float | None = None
    cur_end = 0.0
    for start, end in regions:
        if cur_start is None:
            cur_start, cur_end = start, end
            continue
        gap = start - cur_end
        if gap > cfg.max_join_gap_sec or end - cur_start > cfg.max_sec:
            emit(cur_start, cur_end)
            cur_start, cur_end = start, end
        else:
            cur_end = end
    if cur_start is not None:
        emit(cur_start, cur_end)
    return out


def assign_words(spans: Sequence[tuple[float, float, tuple[str, ...]]],
                 words: Sequence[Word]) -> list[VadClip]:
    """Kelimeleri kliplere orta noktalarına göre dağıt; metni oradan kur."""
    clips: list[VadClip] = []
    i = 0
    for start, end, flags in spans:
        while i < len(words) and (words[i].start + words[i].end) / 2 < start:
            i += 1
        a = i
        j = i
        while j < len(words) and (words[j].start + words[j].end) / 2 <= end:
            j += 1
        if j > a:
            clips.append(VadClip(start, end, " ".join(w.text for w in words[a:j]), (a, j), flags))
        i = j
    return clips


def segment_vad(regions: Sequence[tuple[float, float]], words: Sequence[Word], cfg,
                pad: bool = True) -> list[VadClip]:
    """Sessizlik hizalı klipler; cümle kolundaki paylarla aynı paylarla."""
    spans = segment_by_silence(regions, cfg)
    if pad:
        spans = [(max(0.0, s - cfg.lead_pad_sec), e + cfg.trail_pad_sec, f) for s, e, f in spans]
    return assign_words(spans, words)
