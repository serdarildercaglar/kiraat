#!/usr/bin/env python
"""`music` v4 → v5 sürüm göçü: ölçümü değişmeyen kliplerin kaydını korur.

v5'in tek farkı AST penceresinin klibin kuyruğunu da ölçmesi
(`MusicMeasurer.window_starts`). Klip penceresinden (10,24 s) kısaysa iki
uygulama **aynı tek pencereyi** üretir, dolayısıyla o kliplerin ölçümü
örnek örnek aynıdır ve yeniden koşmaları gereksizdir. Bu betik yalnızca o
kliplerin `done` satırını v5'e taşır; pencereden uzun her klip kayıtsız
kalır ve koşu onları yeniden ölçer.

Güvenlik payı: sınırın hemen altındaki klipler (`--margin-sec`, varsayılan
0,05 s) taşınmaz — yeniden örneklemenin örnek sayısını yuvarlaması sınırı
geçirebilir. Koşu durmuşken çalıştırılır.

    python scripts/migrate_music_v5.py work/full-1 [--apply]
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from kiraat import base  # noqa: E402
from kiraat.config import Config  # noqa: E402
from kiraat.pipeline import stage_version  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("work_root", type=Path)
    ap.add_argument("--config", default="configs/default.yaml")
    ap.add_argument("--margin-sec", type=float, default=0.05)
    ap.add_argument("--apply", action="store_true", help="yazmadan önce kuru koşu görülür")
    args = ap.parse_args()

    cfg = Config.load(args.config)
    yeni = stage_version(cfg, base.get_stage("music"))
    if not yeni.startswith("5+"):
        raise SystemExit(f"music sürümü 5 değil ({yeni}); betik güncel değil")
    window_sec = float(cfg.get("music.window_sec", 10.24))
    sinir = window_sec - args.margin_sec

    db = args.work_root / "db" / "state.sqlite"
    con = sqlite3.connect(db)
    eski = [r[0] for r in con.execute(
        "select distinct version from done where stage='music' and version<>?", (yeni,))]
    print(f"veri: {db}")
    print(f"sürüm: {', '.join(eski) or '(yok)'} → {yeni}")
    print(f"sınır: klip süresi ≤ {sinir:.4f} s (pencere {window_sec} s − pay {args.margin_sec} s)")

    tasinabilir, kalan = con.execute(
        "select sum(case when c.duration<=? then 1 else 0 end), "
        "       sum(case when c.duration>? then 1 else 0 end) "
        "from done d join clips c on c.id=d.key "
        "where d.kind='clip' and d.stage='music' and d.version<>?",
        (sinir, sinir, yeni)).fetchone()
    print(f"taşınacak (ölçümü değişmez): {tasinabilir or 0}")
    print(f"yeniden ölçülecek (pencereden uzun): {kalan or 0}")

    if not args.apply:
        print("\nkuru koşu; yazmak için --apply")
        return 0
    cur = con.execute(
        "update done set version=? where kind='clip' and stage='music' and version<>? "
        "and key in (select id from clips where duration<=?)", (yeni, yeni, sinir))
    con.commit()
    print(f"\ntaşındı: {cur.rowcount} satır")
    print("kalan v4 satırı:", con.execute(
        "select count(*) from done where stage='music' and version<>?", (yeni,)).fetchone()[0])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
