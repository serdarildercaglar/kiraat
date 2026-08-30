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
    #: Çıktısını besleyen aşamalar. İki iş görür: belge ve sürüm zinciri —
    #: üst akıştaki bir aşamanın sürümü değişince bu aşamanınki de değişir.
    #: Bu olmadan `align` kod sürümü 2'ye çıkarken `align_score_*` sütunlarını
    #: yazan `segment` atlanıyordu ve düzeltme manifestoya hiç ulaşmıyordu.
    depends_on: tuple[str, ...] = ()
    #: Aşamanın KENDİ bölümü dışında okuduğu konfig bölümleri; kendi adı her
    #: zaman katılır. `asr` ve `clip_qc` `vad` bölümünü okuyordu ama sürümleri
    #: görmüyordu: eşik değişince hiçbir şey yeniden koşmuyor, konuşma ve
    #: sessizlik sütunları iki ayrı VAD ayarının karışımı oluyordu.
    config_sections: tuple[str, ...] = ()
    #: Kendi bölümünde sürümü etkilemeyen anahtarlar — yalnızca başarım
    #: ayarları. Unutulması güvenlidir: fazladan yeniden koşu olur, sessiz
    #: eskime olmaz. Tersi doğru değil, o yüzden varsayılan bölümün tamamıdır.
    version_ignore: tuple[str, ...] = ()

    @classmethod
    def hashed_sections(cls) -> tuple[str, ...]:
        """Sürüm özetine giren konfig bölümleri."""
        return tuple(sorted({cls.name, *cls.config_sections}))

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


class ChannelStage(Stage):
    """Kanal düzeyinde çalışır.

    Şimdilik tek örneği künye madenciliği ve yürütmesi
    `Pipeline.run_boilerplate` içinde duruyor; buradaki sınıf, aşamanın
    sürüm ve bağımlılık defterine girmesi için var — `segment` ona bağlı ve
    sürüm zincirinin onu çözebilmesi gerekiyor.
    """


class ClipStage(Stage):
    """Klipleri ölçer. Dönüş değeri yalnızca ölçümdür — karar değil.

    Sözleşme: dönen her sözlük `{"id": ..., "metrics": {...}, "flags": [...]}`
    biçimindedir. Bir klip aşaması `recommended`, `decision` ya da eşdeğeri
    bir alan yazamaz; yazarsa `validate_output` hata verir.
    """

    FORBIDDEN_FIELDS = frozenset({"recommended", "decision", "accept", "reject"})
    #: Aşamanın üretebileceği bütün ölçüm anahtarları ve işaretler. Aşama yeniden
    #: koşunca depo önce bunları siler, sonra yeni çıktıyı katar; böylece artık
    #: üretilmeyen bir sütun ya da kalkan bir işaret hayalet olarak kalmaz
    #: (29 Ağu 2026: dış model kapatıldığı hâlde `music_prob_external`
    #: manifestoda kaldı).
    produces_metrics: tuple[str, ...] = ()
    produces_flags: tuple[str, ...] = ()

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


def register(cls: type[Stage] | None = None, *, override: bool = False):
    """Aşamayı adıyla kaydet. `override=True` mevcut adın yerine geçer; yalnızca
    testlerde, gerçek aşamanın yerine sahtesini koymak için."""
    def _do(c: type[Stage]) -> type[Stage]:
        if not c.name:
            raise ValueError("Stage.name bos olamaz")
        if c.name in _REGISTRY and not override:
            raise ValueError(f"Tekrarlanan stage adi: {c.name}")
        _REGISTRY[c.name] = c
        return c
    return _do(cls) if cls is not None else _do


def get_stage(name: str) -> type[Stage]:
    try:
        return _REGISTRY[name]
    except KeyError as exc:
        raise KeyError(f"Bilinmeyen stage {name!r}; mevcut: {', '.join(_REGISTRY) or '-'}") from exc
