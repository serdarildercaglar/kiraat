"""Ham korpusun envanteri: her dosyanın ffprobe ile ölçülmüş künyesi.

Hattın bugüne kadarki bütün sayıları örnek koşulardan geliyordu ve örnekler
kayıt başına 20 dakikayla sınırlıydı. Bu betik ham kaynağın kendisini ölçer:
süre, kodek, örnekleme hızı, kanal sayısı, bit hızı, dosya boyutu — hepsi
dosya dosya. Çıktı `work/inventory.jsonl`; rapor bu dosyadan üretilir, yani
ölçüm bir kez yapılır ve tekrar tekrar okunabilir.

Uzantı listesi dışında kalan ses dosyaları da taranır ve raporda ayrı
gösterilir: hattın sessizce atladığı malzemenin görünmesi gerekiyor.

    python scripts/inventory.py                 # ölç ve raporla
    python scripts/inventory.py --report-only   # var olan envanterden raporla
"""

from __future__ import annotations

import argparse
import collections
import concurrent.futures as cf
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from kiraat.config import Config

#: Taranacak uzantılar: ses olma ihtimali olan her şey. Konfigdeki liste
#: buna eklenir, yani envanter her zaman hattın aldığından geniş tarar ve
#: dışarıda kalan varsa raporlar.
AUDIO_EXT = {".m4a", ".m4aa", ".m4b", ".mp3", ".mp2", ".wav", ".flac", ".opus",
             ".ogg", ".oga", ".webm", ".weba", ".aac", ".wma", ".aiff", ".aif",
             ".alac", ".ape", ".wv", ".caf", ".au", ".amr", ".mka", ".mp4",
             ".m4v", ".mkv", ".mov", ".avi", ".ts", ".3gp", ".wmv", ".flv", ".mpg"}


def probe(path: str) -> dict[str, Any]:
    """ffprobe künyesi. Okunamayan dosya `error` alanıyla döner, atlanmaz."""
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries",
             "stream=codec_name,sample_rate,channels,bit_rate:format=duration,bit_rate,format_name",
             "-of", "json", path],
            capture_output=True, text=True, timeout=300)
    except subprocess.TimeoutExpired:
        return {"error": "ffprobe zaman aşımı"}
    if out.returncode != 0:
        return {"error": (out.stderr or "ffprobe hata").strip().splitlines()[-1][:200]}
    info = json.loads(out.stdout or "{}")
    stream = (info.get("streams") or [{}])[0]
    fmt = info.get("format") or {}
    if not stream:
        return {"error": "ses akışı yok"}
    dur = float(fmt.get("duration") or 0.0)
    return {
        "codec": stream.get("codec_name"),
        "sample_rate": int(stream.get("sample_rate") or 0),
        "channels": int(stream.get("channels") or 0),
        "stream_bit_rate": int(stream.get("bit_rate") or 0) or None,
        "format_bit_rate": int(fmt.get("bit_rate") or 0) or None,
        "format_name": fmt.get("format_name"),
        "duration": round(dur, 3),
        "error": None if dur > 0 else "süre okunamadı",
    }


def scan(root: Path, jobs: int, exts: set[str] = AUDIO_EXT) -> list[dict[str, Any]]:
    files: list[Path] = []
    other: list[Path] = []
    for dirpath, _, names in os.walk(root):
        for name in names:
            p = Path(dirpath) / name
            (files if p.suffix.lower() in exts else other).append(p)
    rows: list[dict[str, Any]] = []
    with cf.ThreadPoolExecutor(jobs) as ex:
        for p, info in zip(files, ex.map(lambda q: probe(str(q)), files)):
            rel = p.relative_to(root)
            rows.append({"path": str(p), "channel": rel.parts[0] if len(rel.parts) > 1 else "",
                         "name": p.name, "ext": p.suffix.lower(),
                         "size": p.stat().st_size, **info})
    for p in other:
        rows.append({"path": str(p), "channel": p.relative_to(root).parts[0]
                     if len(p.relative_to(root).parts) > 1 else "",
                     "name": p.name, "ext": p.suffix.lower(), "size": p.stat().st_size,
                     "duration": 0.0, "error": "ses dosyası değil (uzantı)"})
    return rows


def quantiles(values: list[float], qs: tuple[float, ...]) -> list[float]:
    if not values:
        return [0.0] * len(qs)
    s = sorted(values)
    return [s[min(int(q * len(s)), len(s) - 1)] for q in qs]


def report(rows: list[dict[str, Any]], cfg_exts: set[str]) -> None:
    taranan = AUDIO_EXT | cfg_exts
    ok = [r for r in rows if not r.get("error") and r.get("duration", 0) > 0]
    bad = [r for r in rows if r.get("error") and r["ext"] in taranan]
    nonaudio = [r for r in rows if r["ext"] not in taranan]
    hours = sum(r["duration"] for r in ok) / 3600
    print(f"envanter: {len(rows)} dosya, {len(ok)} okunabilir ses, {hours:.1f} saat, "
          f"{sum(r['size'] for r in rows)/1e9:.1f} GB")

    outside = [r for r in ok if r["ext"] not in cfg_exts]
    print(f"hattın alacağı: {len([r for r in ok if r['ext'] in cfg_exts])} dosya; "
          f"uzantı listesi dışında kalan {len(outside)} dosya, "
          f"{sum(r['duration'] for r in outside)/3600:.2f} saat")

    d = [r["duration"] for r in ok]
    p = quantiles(d, (0.05, 0.25, 0.5, 0.75, 0.9, 0.95, 0.99))
    print(f"süre (dk): p5 {p[0]/60:.1f}  p25 {p[1]/60:.1f}  med {p[2]/60:.1f}  "
          f"p75 {p[3]/60:.1f}  p90 {p[4]/60:.1f}  p95 {p[5]/60:.1f}  p99 {p[6]/60:.1f}  "
          f"maks {max(d)/60:.1f}")

    print("\nsüre bandı        kayıt      saat    payı")
    bands = [(0, 600, "< 10 dk"), (600, 1800, "10–30 dk"), (1800, 3600, "30–60 dk"),
             (3600, 2 * 3600, "1–2 saat"), (2 * 3600, 4 * 3600, "2–4 saat"),
             (4 * 3600, 8 * 3600, "4–8 saat"), (8 * 3600, 10 ** 9, "8 saat+")]
    for lo, hi, label in bands:
        sel = [r["duration"] for r in ok if lo <= r["duration"] < hi]
        print(f"  {label:14s} {len(sel):6d} {sum(sel)/3600:9.1f} {100*sum(sel)/3600/hours:6.1f}%")

    print("\nkanal                       kayıt      saat    pay  en uzun  medyan")
    per: dict[str, list[dict[str, Any]]] = collections.defaultdict(list)
    for r in ok:
        per[r["channel"]].append(r)
    for ch, rs in sorted(per.items(), key=lambda kv: -sum(x["duration"] for x in kv[1])):
        h = sum(x["duration"] for x in rs) / 3600
        med = quantiles([x["duration"] for x in rs], (0.5,))[0]
        print(f"  {ch:26s} {len(rs):5d} {h:9.1f} {100*h/hours:5.1f}% "
              f"{max(x['duration'] for x in rs)/3600:7.2f}sa {med/60:6.1f}dk")

    def dist(key: str, fmt=lambda v: str(v)) -> None:
        c = collections.Counter(r.get(key) for r in ok)
        h = collections.Counter()
        for r in ok:
            h[r.get(key)] += r["duration"] / 3600
        print(f"\n{key}:")
        for v, n in c.most_common():
            print(f"  {fmt(v):>12s}  {n:5d} dosya  {h[v]:8.1f} saat")

    dist("codec")
    dist("sample_rate", lambda v: f"{v} Hz")
    dist("channels", lambda v: f"{v} kanal")
    dist("ext")

    # Bit hızı dosya boyutundan hesaplanır: bu m4a'larda ffprobe'un akış
    # düzeyi `bit_rate` alanı anlamsız değerler veriyor (0,1–0,7 kb/s),
    # kapsayıcının alanı ve boyut/süre ise birbirini tutuyor.
    kbps = sorted(8 * r["size"] / r["duration"] / 1000 for r in ok)
    q = quantiles(kbps, (0.05, 0.5, 0.95))
    print(f"\nbit hızı, boyut/süre (kb/s): p5 {q[0]:.0f}  med {q[1]:.0f}  p95 {q[2]:.0f}")

    if bad:
        print(f"\nokunamayan ses dosyası: {len(bad)}")
        for r in bad:
            print(f"  {r['error'][:60]:60s} {r['path']}")
    if nonaudio:
        print(f"\nses olmayan dosya: {len(nonaudio)}")
        for r in nonaudio[:10]:
            print(f"  {r['path']}")

    print("\nen uzun 15 kayıt:")
    for r in sorted(ok, key=lambda x: -x["duration"])[:15]:
        print(f"  {r['duration']/3600:6.2f} sa  {r['channel']:22s} {r['name'][:70]}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/default.yaml")
    ap.add_argument("--out", default="work/inventory.jsonl")
    ap.add_argument("--jobs", type=int, default=16)
    ap.add_argument("--report-only", action="store_true")
    args = ap.parse_args()

    cfg = Config.load(args.config)
    root = Path(cfg.get("paths.raw_root"))
    out = Path(args.out)
    if args.report_only:
        rows = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()]
    else:
        rows = scan(root, args.jobs, AUDIO_EXT | set(cfg.get("sources.extensions")))
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("w", encoding="utf-8") as fh:
            for r in sorted(rows, key=lambda x: x["path"]):
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(f"envanter yazıldı: {out}")
    report(rows, set(cfg.get("sources.extensions")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
