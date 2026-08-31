"""Ölçüm sütunlarının depo içi analizi: manifest → sayılar, defter malzemesi.

    python scripts/analyze_metrics.py --manifest work/sample-25d/manifests/clips.jsonl \
        [--listen-out work/sample-25d/listen-music.txt]

Dört bölüm üretir; hepsi yalnızca manifest sütunlarından hesaplanır:

  1. Müzik ölçümünün tekrarı (defter, koşulacak deney 2): AudioSet skoru ile
     ayrıştırma tabanlı dB arasındaki Spearman korelasyonu, bu depoda
     üretilmiş kliplerle. 28 Ağu 2026'daki +0,799 v1 kliplerinde ölçülmüştü
     ve "yeniden koşulmalı" damgası taşıyordu.
  2. Müzik işaretinin kanal dağılımı (açık madde 15'in girdisi).
  3. duration/n_words aykırılığı (30 Ağu literatür kaydı, yapılacak 1):
     LibriTTS'in ses-metin uyuşmazlığı sinyali; dağılım ve kuyruklar.
  4. Yeni sütunların (loudness_lufs, dnsmos_*) kanal dağılımı ve politika
     what-if'i: v4'te kaldırılan dnsmos_ovrl ≥ 3,0 kuralı bugün kaç klip
     dışlardı — yalnızca sayım, kural konmaz.

`--listen-out` verilirse madde 15 için kör dinleme aday kimlikleri yazılır:
işaret yığılan kanallardan, dB bantlarına dengelenmiş örneklem
(`scripts/listen_ui.py --questions music --ids-file <dosya>` ile sayfa üretilir).
"""

from __future__ import annotations

import argparse
import collections
import json
import random
import statistics

parser = argparse.ArgumentParser()
parser.add_argument("--manifest", required=True)
parser.add_argument("--listen-out", default=None)
parser.add_argument("--listen-channels", nargs="+",
                    default=["Peri_Mia", "SESLİKİTAPEVİ", "sesli-kitaplar"])
parser.add_argument("--listen-n", type=int, default=36)
parser.add_argument("--seed", type=int, default=17)
args = parser.parse_args()

rows = [json.loads(l) for l in open(args.manifest, encoding="utf-8")]
if not rows:
    raise SystemExit("manifest boş")


def spearman(xs: list[float], ys: list[float]) -> float:
    """Spearman rho; bağlarda ortalama sıra. scipy'siz, saf hesap."""
    def ranks(v: list[float]) -> list[float]:
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
                j += 1
            avg = (i + j) / 2 + 1
            for k in range(i, j + 1):
                r[order[k]] = avg
            i = j + 1
        return r
    rx, ry = ranks(xs), ranks(ys)
    mx, my = statistics.mean(rx), statistics.mean(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = (sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry)) ** 0.5
    return num / den if den else 0.0


def med(v):  # boş listeye dayanıklı
    return statistics.median(v) if v else None


def q(values, p):
    s = sorted(values)
    return s[min(int(p * len(s)), len(s) - 1)] if s else None


print(f"manifest: {args.manifest} — {len(rows)} klip, {sum(r['duration'] for r in rows)/3600:.2f} saat\n")

# ---------------------------------------------------------------- 1. müzik korelasyonu
sep = [r for r in rows if r.get("music_db_separated")]
print("1) MÜZİK ÖLÇÜMÜNÜN TEKRARI (deney 2)")
print(f"   ayrıştırıcı koşan klip: {len(sep)}/{len(rows)} (music_db_separated)")
if len(sep) >= 10:
    rho = spearman([r["music_score_audioset"] for r in sep],
                   [r["music_to_speech_db"] for r in sep])
    print(f"   Spearman(AudioSet, dB) = {rho:+.3f}   (28 Ağu, v1 klipleri: +0,799 — 'yeniden koşulmalı' idi)")
flagged = [r for r in rows if "background_music" in r["flags"]]
print(f"   background_music işareti: {len(flagged)} klip ({100*len(flagged)/len(rows):.1f}%)")

# ---------------------------------------------------------------- 2. işaretin kanal dağılımı
print("\n2) MÜZİK İŞARETİNİN KANAL DAĞILIMI (madde 15 girdisi)")
by_ch = collections.defaultdict(list)
for r in rows:
    by_ch[r["channel"]].append(r)
konsantre = []
for ch, rs in sorted(by_ch.items(), key=lambda kv: -sum("background_music" in r["flags"] for r in kv[1])):
    n = sum("background_music" in r["flags"] for r in rs)
    if n:
        rec = sum(1 for r in rs if r["recommended"])
        konsantre.append(ch)
        print(f"   {ch:28s} {n:4d}/{len(rs):4d} işaretli ({100*n/len(rs):5.1f}%)  önerilen {100*rec/len(rs):5.1f}%")
if not konsantre:
    print("   işaretli klip yok")

# ---------------------------------------------------------------- 3. duration/n_words
print("\n3) duration / n_words AYKIRILIĞI")
spw = [(r["duration"] / r["n_words"], r) for r in rows if r.get("n_words")]
v = [x for x, _ in spw]
print(f"   kelime başına süre: med {med(v):.3f} s, p1 {q(v,.01):.3f}, p99 {q(v,.99):.3f}, maks {max(v):.3f}")
tail = sorted(spw, key=lambda t: -t[0])[:8]
print("   en yavaş 8 klip (dinleme adayı — uyuşmazlık ya da uzun sessizlik):")
for x, r in tail:
    print(f"     {r['id']}  {x:.2f} s/kelime  dur={r['duration']:.1f}  n={r['n_words']}  {r['text'][:48]!r}")
hizli = sorted(spw, key=lambda t: t[0])[:4]
print("   en hızlı 4 klip:")
for x, r in hizli:
    print(f"     {r['id']}  {x:.2f} s/kelime  dur={r['duration']:.1f}  n={r['n_words']}  {r['text'][:48]!r}")

# ---------------------------------------------------------------- 4. yeni sütunlar
print("\n4) YENİ SÜTUNLAR")
lufs = [r["loudness_lufs"] for r in rows if r.get("loudness_lufs") is not None]
ch_med = {ch: med([r["loudness_lufs"] for r in rs if r.get("loudness_lufs") is not None])
          for ch, rs in by_ch.items()}
ch_med = {k: v for k, v in ch_med.items() if v is not None}
if not lufs:
    print("   loudness_lufs yok (clip_qc v3 öncesi manifest)")
if lufs:
    print(f"   loudness_lufs: n={len(lufs)}, med {med(lufs):.1f}, p5 {q(lufs,.05):.1f}, p95 {q(lufs,.95):.1f}"
          f"  → klip düzeyi yayılım (p95-p5) {q(lufs,.95)-q(lufs,.05):.1f} LU")
if lufs and len(ch_med) > 1:
    print(f"   kanal medyanları: {min(ch_med.values()):.1f} … {max(ch_med.values()):.1f} LUFS"
          f" (aralık {max(ch_med.values())-min(ch_med.values()):.1f} LU; v1'de 18,4 LU idi — DESIGN #9)")
for k in ("dnsmos_sig", "dnsmos_bak", "dnsmos_ovrl"):
    vals = [r[k] for r in rows if r.get(k) is not None]
    if vals:
        print(f"   {k}: n={len(vals)}, med {med(vals):.2f}, p5 {q(vals,.05):.2f}, p95 {q(vals,.95):.2f}")
ovrl = [(r["dnsmos_ovrl"], r) for r in rows if r.get("dnsmos_ovrl") is not None]
if ovrl:
    would = [r for x, r in ovrl if x < 3.0 and r["recommended"]]
    rec_n = sum(1 for r in rows if r["recommended"])
    print(f"   what-if: dnsmos_ovrl ≥ 3,0 kuralı bugün önerilen {rec_n} klipten "
          f"{len(would)} tanesini dışlardı ({100*len(would)/max(rec_n,1):.1f}%) — kural KONMADI, sayım.")
    wch = collections.Counter(r["channel"] for r in would)
    if wch:
        print("   dışlananların kanal dağılımı (ilk 6): " +
              ", ".join(f"{c} {n}" for c, n in wch.most_common(6)))
    kat = {"≥4,0": sum(1 for x, _ in ovrl if x >= 4.0),
           "3,8–4,0": sum(1 for x, _ in ovrl if 3.8 <= x < 4.0),
           "3,6–3,8": sum(1 for x, _ in ovrl if 3.6 <= x < 3.8),
           "3,0–3,6": sum(1 for x, _ in ovrl if 3.0 <= x < 3.6),
           "<3,0": sum(1 for x, _ in ovrl if x < 3.0)}
    print("   WenetSpeech4TTS katman sayımı (Premium ≥4,0 / Standard ≥3,8 / Basic ≥3,6): " +
          ", ".join(f"{k}: {n}" for k, n in kat.items()))

# ---------------------------------------------------------------- dinleme örneklemi
if args.listen_out:
    rng = random.Random(args.seed)
    cands = [r for r in rows if r["channel"] in args.listen_channels]
    # Üst bant açık uçlu: music_to_speech_db pozitif olabilir (müzik
    # konuşmadan gürse); 0,1'de kesmek tam da dinlenmesi gereken en gür
    # klipleri örneklemden düşürüyordu (31 Ağu incelemesi).
    bands = [(-80.1, -40.0), (-40.0, -33.0), (-33.0, -25.0), (-25.0, float("inf"))]
    picked = []
    per = max(args.listen_n // (len(bands) * len(args.listen_channels)), 1)
    for ch in args.listen_channels:
        for lo, hi in bands:
            pool = [r for r in cands if r["channel"] == ch and lo < r.get("music_to_speech_db", -80) <= hi]
            picked += rng.sample(pool, min(per, len(pool)))
    with open(args.listen_out, "w", encoding="utf-8") as fh:
        fh.write(" ".join(r["id"] for r in picked) + "\n")
    dist = collections.Counter(r["channel"] for r in picked)
    print(f"\n5) DİNLEME ÖRNEKLEMİ → {args.listen_out}: {len(picked)} klip, "
          + ", ".join(f"{c} {n}" for c, n in dist.items())
          + " (dB bantlarına dengeli; scripts/listen_ui.py --questions music --ids-file ile sayfa üret)")
