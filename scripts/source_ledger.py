"""Kaynak defteri: koşu veritabanındaki her kaynak kaydın akıbeti.

Envanter 2.700 dosya sayar, koşu veritabanı 2.699 kaynak, klip veren kayıt
2.680'dir. Bu betik aradaki farkı kayıt kayıt yazar: her kaynağın kimliği,
kanalı, dosya adı, süresi ve durumu (`clips`, `no_asr_words`,
`decode_failure`). Yalnızca veritabanını okur; ses dosyası gerekmez.

    python scripts/source_ledger.py --db work/full-1/db/state.sqlite \\
        --out docs/source_ledger.csv
"""

from __future__ import annotations

import argparse
import collections
import csv
import json
import sqlite3
from pathlib import PurePosixPath

FIELDS = ("source_id", "channel", "file_name", "container", "duration_sec",
          "source_sample_rate", "status", "n_clips", "clip_hours")


def status_of(error: str | None, meta: dict, n_clips: int) -> str:
    if error:
        return "decode_failure"
    if n_clips:
        return "clips"
    if meta.get("n_words") == 0:
        return "no_asr_words"
    return "no_clips"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--db", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    con = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
    clips = {sid: (n, sec) for sid, n, sec in con.execute(
        "SELECT source_id, COUNT(*), SUM(duration) FROM clips GROUP BY source_id")}
    rows = []
    for sid, path, channel, ext, duration, sr, error, meta_json in con.execute(
            "SELECT id, path, channel, ext, duration, source_sample_rate, error, meta_json "
            "FROM sources ORDER BY id"):
        n, sec = clips.get(sid, (0, 0.0))
        rows.append({
            "source_id": sid,
            "channel": channel,
            "file_name": PurePosixPath(path).name,
            "container": ext.lstrip("."),
            "duration_sec": "" if duration is None else round(duration, 3),
            "source_sample_rate": sr or "",
            "status": status_of(error, json.loads(meta_json or "{}"), n),
            "n_clips": n,
            "clip_hours": round(sec / 3600, 4),
        })

    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)

    by_status = collections.Counter(r["status"] for r in rows)
    hours = collections.defaultdict(float)
    for r in rows:
        hours[r["status"]] += (r["duration_sec"] or 0) / 3600
    print(f"{len(rows)} kaynak -> {args.out}")
    for s, n in by_status.most_common():
        print(f"  {s:15s} {n:5d}  {hours[s]:8.1f} kaynak saati")


if __name__ == "__main__":
    main()
