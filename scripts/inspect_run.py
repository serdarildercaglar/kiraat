"""Bir koşunun durum deposunu ve manifestosunu gözle denetlenebilir kıl.

    python scripts/inspect_run.py [--work work/sample-24] [--edges 2]

Kaynak başına: süre, kapsayıcı süresi, kesiklik, kelime/dk, klip sayısı,
klip saati, hata. Kanal başına: madenlenen boilerplate ifadeleri. Kaynak
başına ilk/son klipler (künye sızması burada görünür).
"""

from __future__ import annotations

import argparse
import collections
import json
import sqlite3
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--work", default="work/sample-24")
parser.add_argument("--edges", type=int, default=2, help="kaynak başına gösterilecek ilk/son klip sayısı")
args = parser.parse_args()

work = Path(args.work)
con = sqlite3.connect(f"file:{work / 'db' / 'state.sqlite'}?mode=ro", uri=True)
con.row_factory = sqlite3.Row

print(f"{'kaynak':9s} {'kanal':24s} {'süre':>7s} {'kaps.':>7s} {'kel/dk':>6s} {'klip':>5s} {'saat':>5s}  işaret/hata")
tot_dur = tot_clip_h = 0.0
sources = con.execute("select * from sources order by channel collate nocase, id").fetchall()
for s in sources:
    m = json.loads(s["meta_json"])
    n, h = con.execute("select count(*), coalesce(sum(duration),0) from clips where source_id=?", (s["id"],)).fetchone()
    dur = s["duration"] or 0.0
    tot_dur += dur
    tot_clip_h += h / 3600
    wpm = (m.get("n_words") or 0) / (dur / 60) if dur else 0
    note = ",".join(m.get("source_flags", [])) + ((" HATA: " + s["error"][:60]) if s["error"] else "")
    print(f"src{s['id']:05d}  {s['channel']:24s} {dur/60:6.1f}m {(m.get('container_duration') or 0)/60:6.1f}m {wpm:6.0f} {n:5d} {h/3600:5.2f}  {note}")
print(f"toplam: {len(sources)} kaynak, ses {tot_dur/3600:.1f} saat, klip {tot_clip_h:.2f} saat "
      f"(%{100*tot_clip_h/(tot_dur/3600):.0f} verim)" if tot_dur else "")

print("\nkanal başına boilerplate:")
for p in sorted((work / "boilerplate").glob("*.json")):
    phrases = json.load(p.open(encoding="utf-8"))
    n_rec = con.execute("select count(*) from sources where channel=?", (p.stem,)).fetchone()[0]
    print(f"  {p.stem:24s} {n_rec} kayıt, {len(phrases)} ifade" + (": " + " | ".join(" ".join(x) for x in phrases[:6]) if phrases else ""))

print(f"\nkaynak başına ilk/son {args.edges} klip:")
for s in sources:
    rows = con.execute('select start, "end", text, flags_json from clips where source_id=? order by idx', (s["id"],)).fetchall()
    if not rows:
        continue
    print(f"  src{s['id']:05d} [{s['channel']}] {Path(s['path']).name[:70]}")
    picks = rows[:args.edges] + ([None] if len(rows) > 2 * args.edges else []) + rows[-args.edges:] if len(rows) > args.edges else rows
    for r in picks:
        if r is None:
            print("      …")
            continue
        flags = json.loads(r["flags_json"])
        print(f"      [{r['start']:8.1f}–{r['end']:8.1f}] {('{' + ','.join(flags) + '} ') if flags else ''}{r['text'][:105]}")

manifest = work / "manifests" / "clips.jsonl"
if manifest.exists():
    rows = [json.loads(l) for l in manifest.open(encoding="utf-8")]
    bp = [r for r in rows if "boilerplate" in r["flags"]]
    print(f"\nboilerplate işaretli klip: {len(bp)}")
    for r in bp[:12]:
        print(f"  [{r['channel']}] {r['text'][:100]}")
    dup = [r for r in rows if r.get("duplicate_of")]
    print(f"yineleme işaretli klip: {len(dup)}")
    top = collections.Counter(r["text"] for r in rows).most_common(6)
    print("en sık metinler:", [(t[:50], n) for t, n in top if n > 1])
