"""Manifestoyu gözle denetlenebilir kıl: sayılar, işaretler, dışlama gerekçeleri, örnekler.

    python scripts/report.py [work/manifests/clips.jsonl] [--examples 3]
"""

from __future__ import annotations

import argparse
import collections
import json
import random
import statistics

parser = argparse.ArgumentParser()
parser.add_argument("manifest", nargs="?", default="work/manifests/clips.jsonl")
parser.add_argument("--examples", type=int, default=3)
parser.add_argument("--seed", type=int, default=1)
args = parser.parse_args()

rows = [json.loads(l) for l in open(args.manifest, encoding="utf-8")]
if not rows:
    raise SystemExit("manifest boş")
rng = random.Random(args.seed)


def pct(a: int, b: int) -> str:
    return f"%{100 * a / b:.1f}" if b else "-"


def q(values: list[float], p: float) -> float:
    s = sorted(values)
    return s[min(int(p * len(s)), len(s) - 1)]


durs = [r["duration"] for r in rows]
rec = [r for r in rows if r["recommended"]]
print(f"klip {len(rows)}, {sum(durs)/3600:.2f} saat; önerilen {len(rec)} ({pct(len(rec), len(rows))}), {sum(r['duration'] for r in rec)/3600:.2f} saat")
print(f"süre: med {statistics.median(durs):.1f} s, p5 {q(durs,.05):.1f}, p95 {q(durs,.95):.1f}, >15 s: {sum(d>15 for d in durs)}")

print("\nkanal başına:")
for ch, grp in sorted(collections.defaultdict(list, {k: [r for r in rows if r['channel']==k] for k in {r['channel'] for r in rows}}).items()):
    g_rec = [r for r in grp if r["recommended"]]
    print(f"  {ch:24s} klip {len(grp):5d}  önerilen {len(g_rec):5d} ({pct(len(g_rec), len(grp))})  saat {sum(r['duration'] for r in grp)/3600:.2f}")

print("\nişaretler:")
for f, n in collections.Counter(f for r in rows for f in r["flags"]).most_common():
    print(f"  {f:18s} {n:5d} ({pct(n, len(rows))})")

print("\ndışlama gerekçeleri (bir klip birden çok taşıyabilir):")
for reason, n in collections.Counter(x for r in rows for x in r["exclusion_reasons"]).most_common():
    print(f"  {reason:32s} {n:5d} ({pct(n, len(rows))})")

for name in ("word_confidence", "align_score_min", "align_score_mean", "speech_ratio", "internal_silence_sec", "music_to_speech_db", "music_score_audioset", "rms_dbfs"):
    vals = [r[name] for r in rows if r.get(name) is not None]
    if vals:
        print(f"{name:22s} n={len(vals):5d}  med {statistics.median(vals):7.3f}  p5 {q(vals,.05):7.3f}  p95 {q(vals,.95):7.3f}")

lower = sum(1 for r in rows if r["text"] and r["text"][0].isalpha() and r["text"][0] == r["text"][0].lower() and r["text"][0] != r["text"][0].upper())
noend = sum(1 for r in rows if r["text"] and r["text"].rstrip("\"'»”’)]}")[-1:] not in {".", "!", "?", "…"})
print(f"\nküçük harfle başlayan {lower} ({pct(lower, len(rows))}), cümle sonu olmayan {noend} ({pct(noend, len(rows))})")
diff = sum(1 for r in rows if r.get("text_spoken") and r["text_spoken"] != r["text"])
print(f"text_spoken ≠ text: {diff} ({pct(diff, len(rows))});  text ≠ text_raw: {sum(1 for r in rows if r.get('text_raw') and r['text_raw'] != r['text'])}")

print(f"\nönerilen kliplerden {args.examples} örnek:")
for r in rng.sample(rec, min(args.examples, len(rec))):
    print(f"  [{r['channel']}] {r['duration']:.1f}s  {r['text'][:140]}")
print(f"\ndışlanan kliplerden {args.examples} örnek:")
excl = [r for r in rows if not r["recommended"]]
for r in rng.sample(excl, min(args.examples, len(excl))):
    print(f"  [{r['channel']}] {r['duration']:.1f}s  {r['exclusion_reasons']}  {r['text'][:110]}")
