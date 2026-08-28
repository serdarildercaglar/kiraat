"""Yinelenen klip ayıklama.

Kural kullanıcının koyduğu kuraldır ve doğrudur: aynı metin **aynı sesle**
tekrar ediyorsa yinelemedir, aynı metin **farklı sesle** okunuyorsa prozodi
çeşitliliği açısından değerlidir ve tutulur. v1 bunu hiç uygulamadığı için
yayımlanan `train` havuzunda aynı kayıt içinde 281, aynı kanal içinde 4.027
fazladan kopya kaldı.

Yineleme burada da silinmez, işaretlenir: `duplicate_of` alanına korunan
klibin kimliği yazılır ve politika o klipleri önerilen alt kümeden düşürür.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any, Callable, Iterable, Sequence

from .text.turkish import lower

_PUNCT = re.compile(r"[^\w\s]", re.UNICODE)


def dedupe_key(text: str) -> str:
    """Karşılaştırma anahtarı: küçük harf, noktalamasız, tek boşluklu."""
    normalized = unicodedata.normalize("NFC", text)
    return re.sub(r"\s+", " ", _PUNCT.sub(" ", lower(normalized))).strip()


def mark_duplicates(
    clips: Sequence[dict[str, Any]],
    *,
    speaker_field: str = "speaker_id",
    text_field: str = "text",
    score: Callable[[dict[str, Any]], float] | None = None,
) -> list[dict[str, Any]]:
    """Aynı (metin, konuşmacı) çiftini yineleme olarak işaretle.

    Her grupta `score` en yüksek olan klip korunur; skor verilmezse en uzun
    süreli klip korunur. Korunan klip `duplicate_of=None` alır, diğerleri
    korunanın kimliğini ve `duplicate` işaretini alır.
    """
    if score is None:
        def score(clip: dict[str, Any]) -> float:
            return float(clip.get("duration", 0.0))

    groups: dict[tuple[str, str], list[int]] = {}
    for i, clip in enumerate(clips):
        key = (dedupe_key(clip.get(text_field, "")), str(clip.get(speaker_field) or ""))
        if not key[0]:
            continue
        groups.setdefault(key, []).append(i)

    keeper_of: dict[int, str | None] = {}
    for indexes in groups.values():
        if len(indexes) == 1:
            keeper_of[indexes[0]] = None
            continue
        best = max(indexes, key=lambda i: (score(clips[i]), -i))
        for i in indexes:
            keeper_of[i] = None if i == best else clips[best]["id"]

    out: list[dict[str, Any]] = []
    for i, clip in enumerate(clips):
        keeper = keeper_of.get(i)
        flags = list(clip.get("flags", ()))
        if keeper is not None and "duplicate" not in flags:
            flags.append("duplicate")
        out.append({**clip, "flags": flags, "duplicate_of": keeper})
    return out


def duplicate_summary(clips: Iterable[dict[str, Any]]) -> dict[str, int]:
    """Kaç klip yineleme olarak işaretlendi, kaç grup etkilendi."""
    marked = [c for c in clips if c.get("duplicate_of")]
    return {"duplicates": len(marked), "kept_groups": len({c["duplicate_of"] for c in marked})}
