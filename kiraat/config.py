"""Konfig yükleme ve doğrulama.

Tek bir YAML dosyası hattın tamamını tanımlar; hiçbir eşik koda gömülmez.
v1'in bu kısmı doğruydu ve korundu. Eklenen tek şey doğrulama: eşikler
sessizce yanlış tipte olamaz ve bilinmeyen bölüm adı hata verir.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import yaml

from .scoring import Policy
from .segment import SegmentConfig

#: Bilinen üst düzey bölümler. Yeni bir aşama eklendiğinde buraya da eklenir;
#: yazım hatası olan bir bölüm sessizce yok sayılmasın diye.
SECTIONS = frozenset(
    {"paths", "runtime", "sources", "prepare", "vad", "asr", "align", "segment",
     "clip_qc", "dnsmos", "speaker", "events", "music", "boilerplate", "text", "dedupe",
     "recommended_subset", "export"}
)


class ConfigError(ValueError):
    pass


@dataclass(frozen=True)
class Config:
    data: Mapping[str, Any]

    @classmethod
    def load(cls, path: str | Path) -> "Config":
        raw = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
        if not isinstance(raw, dict):
            raise ConfigError(f"{path}: kok nesne sozluk olmali")
        unknown = set(raw) - SECTIONS
        if unknown:
            raise ConfigError(f"{path}: bilinmeyen bolum(ler): {', '.join(sorted(unknown))}")
        return cls(raw)

    def get(self, dotted: str, default: Any = None) -> Any:
        node: Any = self.data
        for part in dotted.split("."):
            if not isinstance(node, Mapping) or part not in node:
                return default
            node = node[part]
        return node

    def section(self, name: str) -> Mapping[str, Any]:
        value = self.data.get(name, {})
        if not isinstance(value, Mapping):
            raise ConfigError(f"{name}: sozluk olmali")
        return value

    def segment_config(self) -> SegmentConfig:
        opts = self.section("segment")
        allowed = SegmentConfig.__dataclass_fields__
        unknown = set(opts) - set(allowed)
        if unknown:
            raise ConfigError(f"segment: bilinmeyen anahtar(lar): {', '.join(sorted(unknown))}")
        return SegmentConfig(**{k: float(v) for k, v in opts.items()})

    def policy(self) -> Policy:
        return Policy.from_dict(self.section("recommended_subset"))
