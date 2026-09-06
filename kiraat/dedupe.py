"""Yinelenen klip ayıklama.

Kural kullanıcının koyduğu kuraldır (6 Eyl 2026): aynı metin **aynı sesle**
tekrar ediyorsa yinelemedir; aynı metin **farklı bir okumayla** geçiyorsa
prozodi çeşitliliği açısından değerlidir ve tutulur. Okuyanın kim olduğu
değil, sesin aynı ses olup olmadığı belirler — aynı cümlenin iki ayrı
okuması aynı kişiden de gelse iki ayrı prozodidir.

"Aynı ses" ölçüyle tanımlanır: `dedupe.identity_fields` alanlarının hepsi
birebir tutuyorsa klip aynı kaydın kopyasıdır. Alanlar sesin kendisini
ölçenlerdir (süre, LUFS, RMS, tepe); `word_confidence` ve sessizlik
payları kasten dışarıdadır, çünkü onlar klibin çevresindeki bağlamı ölçer
ve aynı jenerik sesi bölümden bölüme farklı gösterirler.

Ölçüm (6 Eyl 2026, `work/full-1` manifesti, 1.840.404 klip): ölçülen
BÜTÜN değerlerin birebir tuttuğu tek bir çift bile yok — kural harfiyen
uygulanırsa hiçbir klip yineleme değildir. Ses ölçümleriyle 598 klip
yinelemedir; bunlar kanalların her bölüme koyduğu jenerik cümleleridir.
Eski (metin + kanal) anahtarı 72.839 klip işaretliyordu, yani 62,5 bini
aslında ayrı okumaydı ve önerilen alt kümeden boşuna düşüyordu.

Kanal anahtara girmez: ses ölçümleri birebir tutuyorsa aynı kaydın
kopyasıdır, hangi kanalda durduğu bunu değiştirmez.

Yineleme burada da silinmez, işaretlenir: `duplicate_of` alanına korunan
klibin kimliği yazılır ve politika o klipleri önerilen alt kümeden düşürür.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any, Callable, Iterable, Mapping, Sequence

from .text.turkish import lower

_PUNCT = re.compile(r"[^\w\s]", re.UNICODE)

#: Sesin kimliğini taşıyan ölçümler. Konfigdeki `dedupe.identity_fields`
#: bunu geçersiz kılar; buradaki liste yalnızca aşamasız kullanım içindir.
IDENTITY_FIELDS = ("duration", "loudness_lufs", "rms_dbfs", "peak_dbfs")


def dedupe_key(text: str) -> str:
    """Karşılaştırma anahtarı: küçük harf, noktalamasız, tek boşluklu."""
    normalized = unicodedata.normalize("NFC", text)
    return re.sub(r"\s+", " ", _PUNCT.sub(" ", lower(normalized))).strip()


def identity(clip: Mapping[str, Any], fields: Sequence[str]) -> tuple | None:
    """Klibin ses kimliği; alanlardan biri bile ölçülmemişse `None`.

    `None` dönen klip hiçbir grupla eşleşmez: kimliği kurulamayan klip
    yineleme sayılmaz (okunamayan ses, eksik ölçüm)."""
    values: list[Any] = []
    for f in fields:
        v = clip.get(f)
        if v is None:
            v = clip.get("metrics", {}).get(f)
        if v is None:
            return None
        values.append(v)
    return tuple(values)


def mark_duplicates(
    clips: Sequence[dict[str, Any]],
    *,
    identity_fields: Sequence[str] = IDENTITY_FIELDS,
    text_field: str = "text",
    score: Callable[[dict[str, Any]], float] | None = None,
) -> list[dict[str, Any]]:
    """Aynı metni aynı sesle tekrarlayan klipleri yineleme olarak işaretle.

    Her grupta `score` en yüksek olan klip korunur; skor verilmezse en uzun
    süreli klip korunur (grup içindeki süreler zaten birebir aynıdır, bu
    yüzden pratikte ilk klip korunur). Korunan klip `duplicate_of=None`
    alır, diğerleri korunanın kimliğini ve `duplicate` işaretini alır.
    """
    if score is None:
        def score(clip: dict[str, Any]) -> float:
            return float(clip.get("duration", 0.0))

    groups: dict[tuple[str, tuple], list[int]] = {}
    for i, clip in enumerate(clips):
        text_key = dedupe_key(clip.get(text_field, "") or "")
        ident = identity(clip, identity_fields)
        if not text_key or ident is None:
            continue
        groups.setdefault((text_key, ident), []).append(i)

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
