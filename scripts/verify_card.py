#!/usr/bin/env python
"""Veri kartındaki sayıları `state.sqlite`'tan yeniden üret ve karşılaştır.

    python scripts/verify_card.py [--db work/full-1/db/state.sqlite]

Kart yayımlanan tek belgedir, manifestler ise yayından sonra silinebilir
(`work/full-1` bugün yalnızca veritabanını taşıyor). Bu betik kartı
veritabanıyla karşılaştırır ve arada kalan hiçbir dosyaya güvenmez:
yineleme işareti, politika kararı ve train/dev/test/rest bölmesi hattın
kendi koduyla (`kiraat.dedupe`, `kiraat.scoring`, `kiraat.split`) yeniden
hesaplanır. Her denetim PASS/FAIL basar; bir tanesi bile düşerse 1 döner.

Kapsam dışı olan tek şey konuşmacı kümeleri: kümeleme kayıt başına gömme
dosyalarını (`work/<koşu>/speaker/*.npz`) ister, veritabanında bu
dosyaların yalnızca yolu vardır. Kartın konuşmacı sayıları
`scripts/cluster_speakers.py` ile üretilir.
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from kiraat.config import Config  # noqa: E402
from kiraat.dedupe import mark_duplicates  # noqa: E402
from kiraat.scoring import Policy, annotate  # noqa: E402
from kiraat.split import (SplitConfig, assign_sources, source_leakage,  # noqa: E402
                          text_leakage, trim_to_quota)

SAAT = 3600.0
_SAYI = re.compile(r"-?[\d.,]*\d")


def sayi(s: str) -> float:
    """Karttaki bir hücreden sayıyı çek (İngilizce biçim: 1,840,404 / 3,105.7)."""
    m = _SAYI.search(s.replace("**", ""))
    if not m:
        raise ValueError(f"sayı yok: {s!r}")
    return float(m.group().replace(",", ""))


def satirlar(metin: str, baslik: str, son: str) -> list[list[str]]:
    """`baslik` ile `son` arasındaki tablo satırlarını hücrelere ayır."""
    govde = metin.split(baslik, 1)[1].split(son)[0]
    out = []
    for line in govde.splitlines():
        line = line.strip()
        if not line.startswith("|") or set(line) <= set("|- "):
            continue
        out.append([h.strip() for h in line.strip("|").split("|")])
    return out


def klipleri_oku(db_path: Path) -> list[dict]:
    db = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    q = ("select id, source_id, channel, duration, text, flags_json, metrics_json "
         "from clips")
    out = []
    for cid, sid, ch, dur, text, fj, mj in db.execute(q):
        m = json.loads(mj)
        out.append({"id": cid, "source_id": sid, "channel": ch, "duration": dur,
                    "text": text or "", "flags": json.loads(fj), "metrics": m,
                    # yineleme kimliği ölçümlerden okunur (dedupe.identity)
                    **{k: m.get(k) for k in ("loudness_lufs", "rms_dbfs", "peak_dbfs")}})
    return out


def bolmele(clips: list[dict], cfg: Config) -> dict[str, str]:
    """`scripts/make_splits.py` ile aynı sıra: ata → sızıntı → kota → rest."""
    scfg = SplitConfig(**cfg.section("split"))
    aday = [c for c in clips if c["recommended"]]
    hours: dict[int, float] = defaultdict(float)
    channel_of: dict[int, str] = {}
    for c in aday:
        hours[c["source_id"]] += c["duration"] / SAAT
        channel_of[c["source_id"]] = c["channel"]
    sources = [{"id": sid, "channel": ch} for sid, ch in sorted(channel_of.items())]

    split_of = assign_sources(sources, hours, scfg)
    assert not source_leakage(split_of)
    leaked = text_leakage(aday, split_of)
    aday = [c for c in aday
            if split_of.get(c["source_id"], "train") == "train"
            or c["id"] not in leaked[split_of[c["source_id"]]]]
    kept = trim_to_quota(aday, split_of, scfg, len({s["channel"] for s in sources}))
    aday = [c for c in aday
            if split_of.get(c["source_id"], "train") == "train" or c["id"] in kept]

    bolme = {c["id"]: split_of.get(c["source_id"], "train") for c in aday}
    return {c["id"]: bolme.get(c["id"], "rest") for c in clips}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--db", default="work/full-1/db/state.sqlite")
    p.add_argument("--config", default="configs/default.yaml")
    p.add_argument("--card", default="docs/DATASET_CARD.md")
    args = p.parse_args()

    cfg = Config.load(args.config)
    kart = Path(args.card).read_text(encoding="utf-8")
    clips = klipleri_oku(Path(args.db))
    print(f"veritabanı: {len(clips)} klip okundu")

    dcfg = cfg.section("dedupe")
    if dcfg.get("enabled", True):
        clips = mark_duplicates(clips, identity_fields=tuple(dcfg["identity_fields"]))
    clips = annotate(clips, Policy.from_dict(cfg.section("recommended_subset")))
    split_of = bolmele(clips, cfg)

    # --- ölçümler -------------------------------------------------------
    n = len(clips)
    sec = sum(c["duration"] for c in clips)
    rec = [c for c in clips if c["recommended"]]
    rec_sec = sum(c["duration"] for c in rec)
    kelime = sum(c["metrics"].get("n_words") or 0 for c in clips)
    isaret = Counter(f for c in clips for f in c["flags"])
    dnsmos = [c["metrics"].get("dnsmos_ovrl") for c in clips]
    dn30 = sum(1 for v in dnsmos if v is not None and v >= 3.0)
    dn35 = sum(1 for v in dnsmos if v is not None and v >= 3.5)
    # Gerekçe metni eşiği kendi biçimiyle yazar ("speech_ratio<0.6"), kart
    # konfigdeki yazımı ("< 0.60") gösterir; karşılaştırma ölçüm adı üzerinden.
    gerekce: Counter = Counter()
    for c in clips:
        for r in c["exclusion_reasons"]:
            gerekce["isaret" if r.startswith("isaret") else re.split(r"[<>]", r)[0]] += 1

    bolme_klip: Counter = Counter()
    bolme_sec: Counter = Counter()
    bolme_kayit: dict[str, set] = defaultdict(set)
    for c in clips:
        s = split_of[c["id"]]
        bolme_klip[s] += 1
        bolme_sec[s] += c["duration"]
        bolme_kayit[s].add(c["source_id"])
    rest_onerilmeyen = sum(1 for c in clips if split_of[c["id"]] == "rest" and not c["recommended"])
    rest_onerilen = bolme_klip["rest"] - rest_onerilmeyen
    rest_onerilmeyen_sec = sum(c["duration"] for c in clips
                               if split_of[c["id"]] == "rest" and not c["recommended"])

    kanal: dict[str, dict] = defaultdict(lambda: {"klip": 0, "sec": 0.0, "rec": 0.0, "src": set()})
    for c in clips:
        k = kanal[c["channel"]]
        k["klip"] += 1
        k["sec"] += c["duration"]
        k["src"].add(c["source_id"])
        if c["recommended"]:
            k["rec"] += c["duration"]

    db = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
    kaynak = db.execute("select count(*) from sources").fetchone()[0]
    hatali = db.execute("select count(*) from sources where error is not null").fetchone()[0]
    klipli = len({c["source_id"] for c in clips})

    # --- karşılaştırma --------------------------------------------------
    dusen = 0
    kontroller: list[str] = []

    def kontrol(ad: str, kart_deger: float, hesap: float, tol: float = 0.0) -> None:
        nonlocal dusen
        ok = abs(kart_deger - hesap) <= tol
        dusen += not ok
        kontroller.append(ad)
        bicim = ",.0f" if tol == 0 else ",.3f"
        print(f"  {'PASS' if ok else 'FAIL'}  {ad}: kart {kart_deger:{bicim}} | "
              f"veritabanı {hesap:{bicim}}")

    ozet = {r[0].strip("*` "): r[1] for r in satirlar(kart, "in the `channel` column.", "## Loading")}
    print("\nözet tablo")
    kontrol("klip", sayi(ozet["clips"]), n)
    kontrol("saat", sayi(ozet["duration"]), sec / SAAT, 0.05)
    kontrol("önerilen klip", sayi(ozet["recommended subset"]), len(rec))
    kontrol("önerilen saat", sayi(ozet["recommended subset"].split("/")[1]), rec_sec / SAAT, 0.05)
    kontrol("kanal", sayi(ozet["channels"]), len(kanal))
    kontrol("kayıt", sayi(ozet["source recordings"]), klipli)
    kontrol("kelime", sayi(ozet["words (ASR)"]), kelime)

    print(f"\nkaynak: {kaynak} indirildi, {hatali} okunamadı, {klipli} klip üretti")

    print("\nbölmeler")
    for row in satirlar(kart, "| split | clips | hours |", "`train`, `dev` and `test`"):
        ad = row[0].strip("*` ")
        if ad in ("train", "dev", "test", "rest"):
            kontrol(f"{ad} klip", sayi(row[1]), bolme_klip[ad])
            kontrol(f"{ad} saat", sayi(row[2]), bolme_sec[ad] / SAAT, 0.05)
            if row[3] != "—":
                kontrol(f"{ad} kayıt", sayi(row[3]), len(bolme_kayit[ad]))
            kontrol(f"{ad} kanal", sayi(row[4]),
                    len({c["channel"] for c in clips if split_of[c["id"]] == ad}))
        elif ad == "total":
            kontrol("toplam klip", sayi(row[1]), n)

    rest = satirlar(kart, "| what is in `rest` |", "The `recordings` column")
    print("\n`rest` dökümü")
    kontrol("önerilmeyen klip", sayi(rest[0][1]), rest_onerilmeyen)
    kontrol("önerilmeyen saat", sayi(rest[0][2]), rest_onerilmeyen_sec / SAAT, 0.05)
    kontrol("kullanılmayan önerilen klip", sayi(rest[1][1]), rest_onerilen)
    kontrol("kullanılmayan önerilen saat", sayi(rest[1][2]),
            (bolme_sec["rest"] - rest_onerilmeyen_sec) / SAAT, 0.05)
    yalniz_rest = len({c["source_id"] for c in clips} -
                      {s for b in ("train", "dev", "test") for s in bolme_kayit[b]})
    kontrol("kliplerinin tamamı rest'te olan kayıt",
            sayi(kart.split("recordings have all of their clips in `rest`")[0].split("and ")[-1]),
            yalniz_rest)

    print("\npolitika")
    dis = satirlar(kart, "| rule | clips excluded |", "Flag frequencies")
    for row in dis:
        anahtar = "isaret" if row[0] == "flag present" else row[0].strip("`").split()[0]
        kontrol(row[0], sayi(row[1]), gerekce[anahtar])
    kontrol("dışlanan klip", sayi(kart.split("This leaves out ")[1]), n - len(rec))
    kontrol("dışlanan saat", sayi(kart.split("This leaves out ")[1].split("(")[1]),
            (sec - rec_sec) / SAAT, 0.05)

    print("\nişaretler")
    for ad, adet in re.findall(r"`(\w+)`\s+([\d,]+)\s*\(\d", kart.split("Flag frequencies")[1]):
        kontrol(ad, sayi(adet), isaret[ad])

    print("\nDNSMOS")
    kontrol("≥ 3,0 payı", sayi(kart.split("of clips have `dnsmos_ovrl ≥ 3.0`")[0].split("**")[-2]),
            100 * dn30 / n, 0.05)
    kontrol("≥ 3,5 payı", sayi(kart.split("the share is ")[1]), 100 * dn35 / n, 0.05)

    print("\nkanal künyesi")
    for row in satirlar(kart, "| channel | recordings | clips | hours |", "The speaker column"):
        ad = row[0].strip("*` ")
        if ad == "total":
            continue
        k = kanal[ad]
        kontrol(f"{ad} kayıt", sayi(row[1]), len(k["src"]))
        kontrol(f"{ad} klip", sayi(row[2]), k["klip"])
        kontrol(f"{ad} saat", sayi(row[3]), k["sec"] / SAAT, 0.05)
        kontrol(f"{ad} önerilen saat", sayi(row[4]), k["rec"] / SAAT, 0.05)

    print("\nkapsam dışı (veritabanından üretilemez, kendi betiğiyle üretilir):"
          "\n  konuşmacı kümeleri — kayıt başına gömme dosyaları gerekir"
          " (scripts/cluster_speakers.py)"
          "\n  bölütleme ablasyonu — ikinci bir kol koşturulur"
          " (scripts/ablate_segmentation.py)"
          "\n  indirme boyutu, hizalama sınırı yüzdeleri — kendi ölçümleri")
    print(f"\n{len(kontroller)} denetim: "
          f"{'HEPSİ GEÇTİ' if not dusen else str(dusen) + ' DÜŞTÜ'}")
    return 1 if dusen else 0


if __name__ == "__main__":
    raise SystemExit(main())
