"""v1 kliplerinde müzik ölçümünü sına.

AudioSet skorunun bantlarından örnek çekip ayrıştırma tabanlı dB ölçüsüyle
karşılaştırır. Amaç, yeni sütunun gerçekten arka plan müziğini ölçtüğünü
klip düzeyinde görmek.
"""

from __future__ import annotations

import argparse
import json
import random
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from kiraat.stages.music import MusicMeasurer, has_background_music, load_audio

BANDS = [(0.0, 0.01), (0.05, 0.15), (0.20, 0.30), (0.40, 0.50), (0.60, 0.71)]

parser = argparse.ArgumentParser()
parser.add_argument("--manifests", nargs="+", required=True)
parser.add_argument("--per-band", type=int, default=3)
parser.add_argument("--external", default=None)
parser.add_argument("--seed", type=int, default=42)
parser.add_argument("--out", default=None, help="olcumleri jsonl olarak yaz")
parser.add_argument("--db", default=None,
                    help="klip dosyasi yoksa kaynak kayittan kesmek icin v1 durum veritabani")
args = parser.parse_args()

SOURCE_PATH: dict[str, str] = {}
if args.db:
    con = sqlite3.connect(f"file:{args.db}?mode=ro&immutable=1", uri=True)
    # manifestodaki source_id 'source-<hex>' bicimindedir; kayit yolunu
    # klip yolundaki src<NNNNN> dizininden degil, sources tablosundan aliriz.
    for sid, path in con.execute("select id, path from sources"):
        SOURCE_PATH[str(sid)] = path
    con.close()


def clip_audio(row) -> str | None:
    """Klip dosyasi varsa onu, yoksa kaynak kayittan kesilmis gecici dosyayi dondur."""
    if Path(row["audio"]).exists():
        return row["audio"]
    src = row["audio"]
    # work/clips/<kanal>/src<NNNNN>/... yolundan kaynak numarasini cikar
    marker = [p for p in Path(src).parts if p.startswith("src")]
    if not marker or not SOURCE_PATH:
        return None
    numeric = str(int(marker[0][3:]))
    path = SOURCE_PATH.get(numeric)
    if not path or not Path(path).exists():
        return None
    out = Path(tempfile.gettempdir()) / f"probe-{row['id'][:24].replace('/', '_')}.wav"
    start = float(row["source_start_sec"])
    dur = float(row["source_end_sec"]) - start
    cmd = ["ffmpeg", "-nostdin", "-loglevel", "error", "-y", "-ss", f"{start:.3f}",
           "-t", f"{dur:.3f}", "-i", path, "-ac", "1", "-ar", "44100", str(out)]
    if subprocess.run(cmd).returncode != 0 or not out.exists():
        return None
    return str(out)

buckets: dict[tuple[float, float], list[dict]] = {b: [] for b in BANDS}
rng = random.Random(args.seed)
for path in args.manifests:
    for line in open(path, encoding="utf-8"):
        row = json.loads(line)
        score = row.get("quality_music_score")
        if score is None:
            continue
        for band in BANDS:
            if band[0] <= score < band[1] and len(buckets[band]) < args.per_band * 40:
                buckets[band].append(row)

MEASURED: list[dict] = []
measurer = MusicMeasurer(external_model=args.external)
measurer.setup()
print(f"ayristirici kaynaklari: {measurer._sep_sources}\n", file=sys.stderr)

header = f"{'v1 skor':>8} {'audioset':>9} {'muzik/konusma dB':>17} {'muzik?':>7} {'dis model':>10}  klip"
print(header)
print("-" * len(header))
for band in BANDS:
    rows = buckets[band]
    if not rows:
        continue
    picked = 0
    for row in rng.sample(rows, len(rows)):
        if picked >= args.per_band:
            break
        audio = clip_audio(row)
        if audio is None:
            continue
        picked += 1
        wave, sr = load_audio(audio)
        m = measurer.measure(wave, sr)
        m["id"], m["channel"], m["v1_music_score"] = row["id"], row["channel"], row["quality_music_score"]
        MEASURED.append(m)
        db = m["music_to_speech_db"]
        ext = m.get("music_prob_external")
        print(
            f"{row['quality_music_score']:8.3f} {m['music_score_audioset']:9.3f} "
            f"{db:17.1f} {('EVET' if has_background_music(db) else 'hayir'):>7} "
            f"{(f'{ext:.3f}' if ext is not None else '-'):>10}  {row['id'][:28]} [{row['channel']}]"
        )


# ---------------------------------------------------------------- korelasyon
def spearman(xs: list[float], ys: list[float]) -> float:
    """Sıra korelasyonu; bağlar ortalama sıra ile ele alınır."""
    def ranks(values: list[float]) -> list[float]:
        order = sorted(range(len(values)), key=lambda i: values[i])
        out = [0.0] * len(values)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
                j += 1
            mean_rank = (i + j) / 2.0
            for k in range(i, j + 1):
                out[order[k]] = mean_rank
            i = j + 1
        return out

    rx, ry = ranks(xs), ranks(ys)
    n = len(xs)
    mx, my = sum(rx) / n, sum(ry) / n
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = (sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry)) ** 0.5
    return num / den if den else float("nan")


if MEASURED:
    db = [m["music_to_speech_db"] for m in MEASURED]
    print()
    print(f"n = {len(MEASURED)} klip")
    print(f"  audioset skoru  vs muzik/konusma dB : rho = "
          f"{spearman([m['music_score_audioset'] for m in MEASURED], db):+.3f}")
    if any("music_prob_external" in m for m in MEASURED):
        ext = [m.get("music_prob_external", 0.0) for m in MEASURED]
        print(f"  dis sinif. olas. vs muzik/konusma dB : rho = {spearman(ext, db):+.3f}")
    audible = [m for m in MEASURED if m["music_to_speech_db"] > -30.0]
    print(f"  duyulur muzik (> -30 dB): {len(audible)}/{len(MEASURED)}")
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            for m in MEASURED:
                fh.write(json.dumps(m, ensure_ascii=False) + "\n")
