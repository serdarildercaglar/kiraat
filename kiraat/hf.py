"""Hugging Face yayını: şemadan türeyen sütun tipleri ve satır dönüşümü.

Yayımlanan sütunlar `kiraat/schema.py`'den türer — iki yerde ayrı ayrı
yazılmaz, çünkü ikisi kaçınılmaz olarak birbirinden ayrışır. Şemadaki
`local` işaretli sütunlar (yerel dosya yolları) yayımda ya dönüştürülür ya
düşer:

  `audio`        yerel FLAC yolu değil, gömülü sesin kendisi olur
  `source_id`    kayıt kimliği `srcNNNNN` biçiminde dizeye çevrilir
  `source_path`  ham dosyanın makinedeki yolu; yayımlanmaz

Ses 24 kHz FLAC'tir ve parquet parçalarının içine gömülür; veri kümesini
indiren `datasets` ile doğrudan açar, ayrıca ses dosyası indirmesi gerekmez.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterator

from . import schema

#: Yayımlanan bölmeler. `rest`, üç bölmeye girmeyen her klip: önerilmeyenler
#: ve kanal hedefi/sızıntı temizliği yüzünden dışarıda kalanlar. Korpusun
#: tamamı yayımlanır, hiçbir klip silinmez.
SPLITS = ("train", "dev", "test", "rest")
SAMPLE_RATE = 24000

#: Şema tipinden `datasets` tipine. `dict[string,float]` sütunu
#: (`music_stem_db`) kliplerin küçük bir kısmında var ve anahtar kümesi
#: sabit değil; yayımda JSON dizesine çevrilir.
#: Yayımda tipi değişen sütunlar. `source_id` veritabanı sayacı olarak
#: int'tir ama yayımda kayıt kimliği (`srcNNNNN`) olarak dizedir.
_OVERRIDE = {"source_id": "string"}

_DTYPE = {
    "string": "string",
    "int": "int32",
    "float": "float32",
    "bool": "bool",
    "list[string]": ["string"],
    "dict[string,float]": "string",
}


def published_columns() -> tuple[schema.Column, ...]:
    """Yayımlanan sütunlar: `source_path` düşer, gerisi kalır."""
    return tuple(c for c in schema.COLUMNS if c.name != "source_path")


def features(sample_rate: int = SAMPLE_RATE):
    """`datasets.Features`; ses sütunu `Audio`, gerisi şemadan."""
    from datasets import Audio, Features, Sequence, Value

    out: dict[str, Any] = {}
    for col in published_columns():
        dtype = _OVERRIDE.get(col.name, col.dtype)
        if dtype == "audio":
            out[col.name] = Audio(sampling_rate=sample_rate)
        elif dtype == "list[string]":
            out[col.name] = Sequence(Value("string"))
        else:
            out[col.name] = Value(_DTYPE[dtype])
    out["split"] = Value("string")
    return Features(out)


def storage_features(sample_rate: int = SAMPLE_RATE):
    """Ses baytları yazılırken kullanılan şema (Audio yerine bytes+path)."""
    from datasets import Features, Value

    out = dict(features(sample_rate))
    out["audio"] = Features({"bytes": Value("binary"), "path": Value("string")})
    return Features(out)


def to_row(clip: dict[str, Any], split: str) -> dict[str, Any]:
    """Manifest satırını yayın satırına çevir; eksik sütunlar boş kalır."""
    row: dict[str, Any] = {"split": split}
    for col in published_columns():
        name = col.name
        if name == "audio":
            row["audio"] = {"bytes": None, "path": clip["audio"]}
        elif name == "source_id":
            row["source_id"] = f"src{int(clip['source_id']):05d}"
        elif col.dtype == "dict[string,float]":
            v = clip.get(name)
            row[name] = json.dumps(v, ensure_ascii=False, sort_keys=True) if v else None
        else:
            row[name] = clip.get(name)
    return row


def iter_split(path: str | Path, split: str) -> Iterator[dict[str, Any]]:
    with Path(path).open(encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                yield to_row(json.loads(line), split)
