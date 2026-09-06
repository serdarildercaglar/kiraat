"""train/dev/test bölmesini kur ve sızıntıyı denetle.

Girdi `export`in manifestidir; çıktı bölme dosyaları ve denetim raporudur.
Bölme kayıt düzeyinde ve kanal dengeli yapılır (`kiraat/split.py`), sonra
`train` ile metni örtüşen dev/test klipleri değerlendirme kümesinden
düşürülür.

    python scripts/make_splits.py --manifest work/full-1/manifests/clips.jsonl
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from kiraat.config import Config
from kiraat.split import SplitConfig, assign_sources, source_leakage, text_leakage, trim_to_quota


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--config", default="configs/default.yaml")
    p.add_argument("--manifest", default="work/full-1/manifests/clips.jsonl")
    p.add_argument("--out", default=None, help="varsayılan: manifestin yanı")
    p.add_argument("--all-clips", action="store_true",
                   help="önerilen alt küme yerine bütün klipler üzerinden böl")
    args = p.parse_args()

    cfg = Config.load(args.config)
    scfg = SplitConfig(**cfg.section("split"))
    manifest = Path(args.manifest)
    out_dir = Path(args.out) if args.out else manifest.parent

    clips = []
    for line in manifest.open(encoding="utf-8"):
        r = json.loads(line)
        if args.all_clips or r["recommended"]:
            clips.append(r)
    print(f"aday klip: {len(clips)}")

    hours: dict[int, float] = defaultdict(float)
    channel_of: dict[int, str] = {}
    for c in clips:
        hours[c["source_id"]] += c["duration"] / 3600
        channel_of[c["source_id"]] = c["channel"]
    sources = [{"id": sid, "channel": ch} for sid, ch in sorted(channel_of.items())]

    split_of = assign_sources(sources, hours, scfg)
    assert not source_leakage(split_of)

    # Sıra önemli: önce sızan klipler düşürülür, sonra kalan havuz kanal
    # başına saat hedefine indirilir. Tersi olursa sızıntı temizliği hedefin
    # altını oyar (10 saatlik hedef 8,5 saate düşüyordu).
    leaked = text_leakage(clips, split_of)
    print(f"metin sızıntısı: test {len(leaked['test'])} klip, dev {len(leaked['dev'])} klip "
          f"(train ile aynı cümle) → değerlendirme kümesinden düşürüldü")
    clips = [c for c in clips
             if split_of.get(c["source_id"], "train") == "train"
             or c["id"] not in leaked[split_of[c["source_id"]]]]

    n_channels = len({s["channel"] for s in sources})
    kept = trim_to_quota(clips, split_of, scfg, n_channels)
    clips = [c for c in clips
             if split_of.get(c["source_id"], "train") == "train" or c["id"] in kept]
    print(f"kanal başına hedefe indirildikten sonra aday klip: {len(clips)}")

    counts: dict[str, Counter] = {s: Counter() for s in ("train", "dev", "test")}
    secs: dict[str, float] = defaultdict(float)
    kanal: dict[str, Counter] = {s: Counter() for s in ("train", "dev", "test")}
    files = {s: (out_dir / f"split-{s}.jsonl").open("w", encoding="utf-8")
             for s in ("train", "dev", "test")}
    dropped = sum(len(v) for v in leaked.values())
    for c in clips:
        split = split_of.get(c["source_id"], "train")
        counts[split][c["channel"]] += 1
        kanal[split][c["channel"]] += 1
        secs[split] += c["duration"]
        files[split].write(json.dumps({**c, "split": split}, ensure_ascii=False) + "\n")
    for fh in files.values():
        fh.close()

    # Denetim: bölmeler arası metin örtüşmesi artık sıfır olmalı.
    kalan = text_leakage(clips, split_of)
    report = {
        "config": {"test_hours": scfg.test_hours, "dev_hours": scfg.dev_hours, "seed": scfg.seed},
        "aday_klip": len(clips),
        "düşürülen_sızıntı_klibi": dropped,
        "bölmeler": {s: {"klip": sum(counts[s].values()), "saat": round(secs[s] / 3600, 3),
                         "kayıt": sum(1 for v in split_of.values() if v == s),
                         "kanal": len(kanal[s])} for s in ("train", "dev", "test")},
        "kanal_başına_klip": {s: {k: round(v, 1) for k, v in sorted(kanal[s].items())}
                              for s in ("dev", "test")},
        "kalan_metin_sızıntısı": {s: len(v) for s, v in kalan.items()},
        "kayıt_sızıntısı": source_leakage(split_of),
    }
    (out_dir / "splits.json").write_text(json.dumps(report, ensure_ascii=False, indent=1),
                                         encoding="utf-8")
    for s in ("train", "dev", "test"):
        b = report["bölmeler"][s]
        print(f"  {s:5} {b['klip']:>9} klip  {b['saat']:>9.2f} sa  {b['kayıt']:>5} kayıt  "
              f"{b['kanal']:>3} kanal")
    print(f"kalan metin sızıntısı: {report['kalan_metin_sızıntısı']} | rapor: {out_dir/'splits.json'}")


if __name__ == "__main__":
    main()
