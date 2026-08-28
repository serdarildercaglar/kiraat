"""Skor tabanlı çıktı sözleşmesi — kapı değil, skor.

v1'in en pahalı yapısal hatası ACCEPT/REVIEW ikilisiydi: doğrulanmamış bir
sınıflandırıcı 981 saati ve korpusun kanal çeşitliliğini kullanılamaz hale
getirdi, üstelik kör dinleme denetiminde o sınıflandırıcının 131 işaretli
klipte sıfır doğru pozitifi çıktı.

v2 hiçbir klibi elemez. Her klip her ölçümüyle yayımlanır; yanına, konfigden
okunan ve sürümlenen bir politikanın ürettiği `recommended` bayrağı ile onu
üreten gerekçeler konur. Politika değişince veri yeniden üretilmez, yalnızca
bayrak yeniden hesaplanır — ve kullanıcı kendi eşiğini koyabilir.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping


@dataclass(frozen=True)
class Rule:
    """Tek bir ölçüm veya işaret koşulu."""

    metric: str | None = None
    min: float | None = None
    max: float | None = None
    flag_absent: tuple[str, ...] = ()
    #: Ölçüm hiç yoksa kural geçilmiş sayılır mı. Varsayılan hayır: eksik
    #: ölçüm sessizce kabul edilmez, gerekçe olarak raporlanır.
    allow_missing: bool = False

    def check(self, metrics: Mapping[str, Any], flags: Iterable[str]) -> str | None:
        """Kural sağlanıyorsa None, sağlanmıyorsa gerekçe döner."""
        if self.flag_absent:
            present = sorted(set(self.flag_absent) & set(flags))
            return f"isaret:{','.join(present)}" if present else None
        if self.metric is None:
            raise ValueError("Rule ya metric ya flag_absent tanimlamali")
        if self.metric not in metrics or metrics[self.metric] is None:
            return None if self.allow_missing else f"eksik_olcum:{self.metric}"
        value = float(metrics[self.metric])
        if self.min is not None and value < self.min:
            return f"{self.metric}<{self.min}"
        if self.max is not None and value > self.max:
            return f"{self.metric}>{self.max}"
        return None

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "Rule":
        return cls(
            metric=raw.get("metric"),
            min=raw.get("min"),
            max=raw.get("max"),
            flag_absent=tuple(raw.get("flag_absent", ())),
            allow_missing=bool(raw.get("allow_missing", False)),
        )


@dataclass(frozen=True)
class Policy:
    """Önerilen alt kümeyi tanımlayan, sürümlenmiş kural listesi."""

    version: str
    rules: tuple[Rule, ...] = field(default=())

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "Policy":
        return cls(
            version=str(raw.get("version", "0")),
            rules=tuple(Rule.from_dict(r) for r in raw.get("rules", ())),
        )

    def evaluate(
        self, metrics: Mapping[str, Any], flags: Iterable[str] = ()
    ) -> tuple[bool, tuple[str, ...]]:
        """(önerilir mi, gerekçeler). Gerekçe listesi boşsa klip önerilir."""
        flags = tuple(flags)
        reasons = tuple(
            reason for reason in (rule.check(metrics, flags) for rule in self.rules) if reason
        )
        return (not reasons, reasons)


def annotate(records: Iterable[dict[str, Any]], policy: Policy) -> list[dict[str, Any]]:
    """Kayıtlara `recommended` ve `exclusion_reasons` ekle. Hiçbir kayıt düşmez."""
    out: list[dict[str, Any]] = []
    for record in records:
        ok, reasons = policy.evaluate(record.get("metrics", {}), record.get("flags", ()))
        out.append({**record, "recommended": ok, "exclusion_reasons": list(reasons),
                    "policy_version": policy.version})
    return out
