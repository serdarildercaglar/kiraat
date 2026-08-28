"""Aşama sözleşmesi.

v1'in aşamaları yalnızca klip düzeyindeydi, çünkü kesim ilk adımdı. v2'de
kesim ASR'den sonra gelir, dolayısıyla iki ayrı sözleşme gerekir:

  SourceStage   kayıt düzeyinde çalışır (çözme, VAD, uzun form ASR, hizalama,
                bölütleme). Klipleri üreten aşamalar bunlardır.
  ClipStage     klip düzeyinde çalışır ve yalnızca **ölçüm üretir**. Hiçbir
                klip aşaması karar veremez; karar `scoring.Policy`nin işidir.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Mapping, Sequence

_REGISTRY: dict[str, type["Stage"]] = {}


class Stage(ABC):
    name: str = ""
    version: str = "1"
    gpu: bool = False
    depends_on: tuple[str, ...] = ()

    def __init__(self, cfg: Any):
        self.cfg = cfg
        self.opts: Mapping[str, Any] = cfg.section(self.name) if self.name else {}

    def setup(self) -> None:
        pass

    def teardown(self) -> None:
        pass


class SourceStage(Stage):
    """Bir kaydı işler; klip üretebilir."""

    @abstractmethod
    def process_source(self, source: Mapping[str, Any]) -> Sequence[Mapping[str, Any]]:
        raise NotImplementedError


class ClipStage(Stage):
    """Klipleri ölçer. Dönüş değeri yalnızca ölçümdür — karar değil.

    Sözleşme: dönen her sözlük `{"id": ..., "metrics": {...}, "flags": [...]}`
    biçimindedir. Bir klip aşaması `recommended`, `decision` ya da eşdeğeri
    bir alan yazamaz; yazarsa `validate_output` hata verir.
    """

    FORBIDDEN_FIELDS = frozenset({"recommended", "decision", "accept", "reject"})

    @abstractmethod
    def process_clips(self, clips: Sequence[Mapping[str, Any]]) -> Sequence[Mapping[str, Any]]:
        raise NotImplementedError

    @classmethod
    def validate_output(cls, rows: Sequence[Mapping[str, Any]]) -> None:
        for row in rows:
            if "id" not in row:
                raise ValueError(f"{cls.name}: cikti satirinda 'id' yok")
            forbidden = cls.FORBIDDEN_FIELDS & set(row)
            if forbidden:
                raise ValueError(
                    f"{cls.name}: klip asamasi karar veremez, yasak alan: "
                    f"{', '.join(sorted(forbidden))}"
                )


def register(cls: type[Stage]) -> type[Stage]:
    if not cls.name:
        raise ValueError("Stage.name bos olamaz")
    if cls.name in _REGISTRY:
        raise ValueError(f"Tekrarlanan stage adi: {cls.name}")
    _REGISTRY[cls.name] = cls
    return cls


def get_stage(name: str) -> type[Stage]:
    try:
        return _REGISTRY[name]
    except KeyError as exc:
        raise KeyError(f"Bilinmeyen stage {name!r}; mevcut: {', '.join(_REGISTRY) or '-'}") from exc


def stage_names() -> list[str]:
    return list(_REGISTRY)
