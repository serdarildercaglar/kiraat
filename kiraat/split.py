"""train / dev / test bölmesi ve sızıntı denetimi.

Bölme **kayıt düzeyindedir**: bir kaydın klipleri tek bir bölmeye girer.
Klip düzeyinde bölmek, aynı kaydın akustiği ve okuma tarzı iki bölmeye
birden düştüğü için değerlendirmeyi şişirir; kayıt düzeyinde bölünce
değerlendirme, modelin hiç duymadığı bir kayıt üzerinde yapılır.

`test` ve `dev` **kanal dengelidir**: kanal başına eşit süre hedeflenir,
kanalın elinde o kadar yoksa eldeki kadarı alınır. Korpusun kanal payları
çok dengesiz (en büyük iki kanal saatlerin üçte birinden fazlası);
değerlendirme kümesi bu dengesizliği taşırsa raporlanan sayı iki kanalın
sayısı olur.

Sızıntı denetimi iki şeye bakar ve ikisi de kayda yazılır:

  kayıt sızıntısı   aynı kaynak birden çok bölmede — kurulum gereği olamaz,
                    yine de sınanır (sessizce bozulmasın)
  metin sızıntısı   `test`/`dev` klibinin normalleştirilmiş metni `train`'de
                    de geçiyor. Bu klipler değerlendirme kümesinden düşürülür;
                    `train` dokunulmadan kalır.

Metin anahtarı `dedupe.dedupe_key` ile aynıdır: küçük harf, noktalamasız.
"""

from __future__ import annotations

import hashlib
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence

from .dedupe import dedupe_key

SPLITS = ("train", "dev", "test")


@dataclass(frozen=True)
class SplitConfig:
    #: Bölme başına hedeflenen toplam süre (saat). Kalan her şey `train`.
    test_hours: float = 5.0
    dev_hours: float = 5.0
    #: Kanal başına hedef = hours / kanal sayısı. Bir kanal hedefi
    #: dolduramazsa açık kalır; başka kanaldan telafi edilmez (denge bozulur).
    seed: str = "kiraat-2026"


def _order(source_id: Any, channel: str, seed: str) -> str:
    """Kaynağın kanal içindeki belirlenimci sırası (tohumla karıştırma)."""
    return hashlib.sha256(f"{seed}:{channel}:{source_id}".encode()).hexdigest()


def assign_sources(sources: Sequence[Mapping[str, Any]], hours: Mapping[str, float],
                   cfg: SplitConfig) -> dict[int, str]:
    """Kaynakları bölmelere dağıt: kanal başına eşit süre, kayıt düzeyinde.

    `hours` kaynak kimliğinden o kaynağın (uygun kliplerinin) saatine.
    """
    by_channel: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for s in sources:
        by_channel[s["channel"]].append(s)
    n_channels = len(by_channel) or 1
    quota = {"test": cfg.test_hours / n_channels, "dev": cfg.dev_hours / n_channels}

    out: dict[int, str] = {}
    for channel, rows in sorted(by_channel.items()):
        rows = sorted(rows, key=lambda s: _order(s["id"], channel, cfg.seed))
        usable = [s for s in rows if hours.get(s["id"], 0.0) > 0]
        # Kanalın klipli kayıtlarından en az biri `train`'de kalır. Üç
        # kayıtlık bir kanal (bizimkütüphane, KitaplarinKedisi) aksi hâlde
        # eğitimden tamamen düşüyordu: dev ve test kanalı temsil ediyor ama
        # model o kanalı hiç görmüyordu.
        takeable = max(0, len(usable) - 1)
        taken = 0
        left = dict(quota)
        for s in rows:
            h = hours.get(s["id"], 0.0)
            if h <= 0:
                out[s["id"]] = "train"
                continue
            picked = None
            if taken < takeable:
                # Kotası en çok açık olan bölme alır; bu, test ve dev'i
                # sırayla doldurur. Önce test'i doldurmak, üç kayıtlık bir
                # kanalın dev'de hiç görünmemesi demekti.
                acik = [n for n in ("test", "dev") if left[n] > 0]
                if acik:
                    picked = max(acik, key=lambda n: (left[n], n == "test"))
                    left[picked] -= h
                    taken += 1
            out[s["id"]] = picked or "train"
    return out


def trim_to_quota(clips: Sequence[Mapping[str, Any]], split_of: Mapping[int, str],
                  cfg: SplitConfig, n_channels: int) -> set[str]:
    """Dev/test kliplerini kanal başına saat hedefine indir.

    Bölme kayıt düzeyindedir, ama kayıtlar saatlerce sürdüğü için bütün
    olarak alınırsa hedef aşılır (10 saatlik hedef 26 saate çıkıyordu).
    Hedefi aşan klipler `train`'e GEÇMEZ — geçseydi aynı kaydın klipleri iki
    bölmeye birden düşer ve bölmenin tek garantisi giderdi; kullanılmadan
    bırakılırlar ve raporda sayılırlar.

    Sıra belirlenimcidir: klip kimliğinin tohumlu özeti.
    """
    quota = {"test": cfg.test_hours / max(1, n_channels), "dev": cfg.dev_hours / max(1, n_channels)}
    left: dict[tuple[str, str], float] = {}
    kept: set[str] = set()
    ordered = sorted((c for c in clips if split_of.get(c["source_id"], "train") != "train"),
                     key=lambda c: _order(c["id"], c["channel"], cfg.seed))
    for c in ordered:
        split = split_of[c["source_id"]]
        key = (split, c["channel"])
        if key not in left:
            left[key] = quota[split]
        if left[key] <= 0:
            continue
        left[key] -= c["duration"] / 3600
        kept.add(c["id"])
    return kept


def text_leakage(clips: Iterable[Mapping[str, Any]], split_of: Mapping[int, str],
                 text_field: str = "text") -> dict[str, set[str]]:
    """`train` ile metni örtüşen dev/test klip kimlikleri."""
    train_keys: set[str] = set()
    others: list[tuple[str, str, str]] = []
    for c in clips:
        split = split_of.get(c["source_id"], "train")
        key = dedupe_key(c.get(text_field) or "")
        if not key:
            continue
        if split == "train":
            train_keys.add(key)
        else:
            others.append((split, c["id"], key))
    leaked: dict[str, set[str]] = {"dev": set(), "test": set()}
    for split, clip_id, key in others:
        if key in train_keys:
            leaked[split].add(clip_id)
    return leaked


def source_leakage(split_of: Mapping[int, str]) -> list[int]:
    """Birden çok bölmeye düşmüş kaynak — kurulum gereği boş olmalı."""
    seen: dict[int, set[str]] = defaultdict(set)
    for sid, split in split_of.items():
        seen[sid].add(split)
    return [sid for sid, splits in seen.items() if len(splits) > 1]
