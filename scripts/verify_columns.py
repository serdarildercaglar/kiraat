"""Bir koşunun sütunlarını bağımsız yoldan yeniden hesaplayıp manifest/DB ile karşılaştır.

    python scripts/verify_columns.py --work work/sample-5c [--n-audio 300] [--seed 1]

Her denetim PASS/FAIL ve sayılarla raporlanır; FAIL varsa 1 döner. Denetimler:
şema uyuşması, kimlik/sıra/süre tutarlılığı, ses dosyası (hız, kanal, süre,
yeniden hesaplanan tepe/RMS/kırpılma), metin değişmezleri (büyük harf
başlangıcı, n_words, okunuş alanı), ölçüm aralıkları ve birbirleriyle
tutarlılığı, kelime güveni ve hizalama skorunun kelime dosyalarından yeniden
hesaplanması, komşu boşlukları, işaret ↔ ölçüm eşleşmesi, politika kararının
konfigden yeniden hesaplanması, DB ↔ manifest eşitliği.
"""

from __future__ import annotations

import argparse
import collections
import json
import random
import re
import sqlite3
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from kiraat import schema  # noqa: E402
from kiraat.config import Config  # noqa: E402
from kiraat.segment import Word, attach_clitics  # noqa: E402
from kiraat.stages.clip_qc import level_metrics  # noqa: E402
from kiraat.text.turkish import is_lower_start  # noqa: E402

parser = argparse.ArgumentParser()
parser.add_argument("--work", default="work/sample-5c")
parser.add_argument("--config", default="configs/default.yaml")
parser.add_argument("--n-audio", type=int, default=300, help="ses yeniden hesaplaması için rastgele klip sayısı")
parser.add_argument("--seed", type=int, default=1)
args = parser.parse_args()

WORK = Path(args.work)
cfg = Config.load(args.config)
con = sqlite3.connect(f"file:{WORK / 'db' / 'state.sqlite'}?mode=ro", uri=True)
con.row_factory = sqlite3.Row
manifest = [json.loads(l) for l in (WORK / "manifests" / "clips.jsonl").open(encoding="utf-8") if l.strip()]
by_id = {r["id"]: r for r in manifest}
db_clips = {r["id"]: dict(r) for r in con.execute("select * from clips")}
sources = {r["id"]: dict(r) for r in con.execute("select * from sources")}
for s in sources.values():
    s["meta"] = json.loads(s["meta_json"] or "{}")

results: list[tuple[str, bool, str]] = []


def check(name: str, bad: list, total: int, note: str = "") -> None:
    ok = not bad
    ex = "" if ok else "  örn: " + "; ".join(str(b) for b in bad[:3])
    results.append((name, ok, f"{len(bad)}/{total} hatalı{(' — ' + note) if note else ''}{ex}"))


def resolve(p: str) -> Path:
    q = Path(p)
    return q if q.is_absolute() else ROOT / q


# ---------------------------------------------------------------- A. şema
missing, unknown = schema.check_manifest(manifest)
check("şema: manifest sütunları", sorted(missing | unknown), len(schema.COLUMNS),
      f"eksik={sorted(missing)} fazla={sorted(unknown)}" if (missing or unknown) else "")

# ---------------------------------------------------------------- B. kimlik, sıra, süre
bad = [r["id"] for r in manifest if not re.fullmatch(r"src\d{5}-\d{5}", r["id"])]
check("kimlik biçimi", bad, len(manifest))
check("kimlik tekil", [k for k, n in collections.Counter(r["id"] for r in manifest).items() if n > 1], len(manifest))
bad = [r["id"] for r in manifest if abs(r["duration"] - (r["end"] - r["start"])) > 0.002 or r["start"] < 0 or r["end"] <= r["start"]]
check("duration = end − start, start ≥ 0", bad, len(manifest))
per_src = collections.defaultdict(list)
for r in manifest:
    per_src[r["source_id"]].append(r)
bad, bad_overlap, bad_bound = [], [], []
for sid, rows in per_src.items():
    rows.sort(key=lambda r: db_clips[r["id"]]["idx"])
    idxs = [db_clips[r["id"]]["idx"] for r in rows]
    if idxs != list(range(len(rows))):
        bad.append(sid)
    for a, b in zip(rows, rows[1:]):
        if b["start"] < a["end"] - 0.001:
            bad_overlap.append((a["id"], b["id"], round(a["end"] - b["start"], 3)))
    dur = sources[sid]["duration"] or 0
    for r in rows:
        if r["end"] > dur + 0.01:
            bad_bound.append((r["id"], r["end"], dur))
check("idx kaynak içinde 0..n−1 ardışık", bad, len(per_src))
check("komşu klipler örtüşmüyor", bad_overlap, len(manifest))
check("klip kaynak süresinin içinde", bad_bound, len(manifest))

# ---------------------------------------------------------------- C. ses dosyası
rng = random.Random(args.seed)
sample = rng.sample(manifest, min(args.n_audio, len(manifest)))
bad_exist, bad_fmt, bad_dur, bad_level = [], [], [], []
for r in sample:
    p = resolve(r["audio"])
    if not p.exists():
        bad_exist.append(r["id"]); continue
    info = sf.info(str(p))
    if info.samplerate != 24000 or info.channels != 1 or info.subtype != "PCM_16" or info.format != "FLAC":
        bad_fmt.append((r["id"], info.samplerate, info.channels, info.subtype, info.format))
    if abs(info.duration - r["duration"]) > 0.01:
        bad_dur.append((r["id"], round(info.duration, 3), r["duration"]))
    wave, _ = sf.read(str(p), dtype="float32")
    lm = level_metrics(wave)
    if abs(lm["peak_dbfs"] - r["peak_dbfs"]) > 0.05 or abs(lm["rms_dbfs"] - r["rms_dbfs"]) > 0.05 or abs(lm["clip_ratio"] - r["clip_ratio"]) > 1e-4:
        bad_level.append((r["id"], lm, (r["peak_dbfs"], r["rms_dbfs"], r["clip_ratio"])))
n = len(sample)
check("ses dosyası var", bad_exist, n)
check("ses biçimi 24 kHz mono FLAC PCM_16", bad_fmt, n)
check("ses süresi = duration (±10 ms)", bad_dur, n)
check("peak/rms/clip_ratio yeniden hesap (±0,05 dB)", bad_level, n)

# ---------------------------------------------------------------- D. metin
check("text boş değil", [r["id"] for r in manifest if not (r["text"] or "").strip()], len(manifest))
# Değişmez: iç noktalamadan/boşluktan bölünmüş parçalar (forced_split, gap_split)
# dışında hiçbir klip küçük harfle başlamaz; o parçalar zaten önerilen alt kümede değildir.
whole = [r for r in manifest if not ({"forced_split", "gap_split"} & set(r["flags"]))]
check("text küçük harfle başlamıyor (forced_split/gap_split dışında; cümle sınırı değişmezi)",
      [(r["id"], r["text"][:30]) for r in whole if is_lower_start(r["text"] or "")], len(whole))
split_lower = [r for r in manifest if ({"forced_split", "gap_split"} & set(r["flags"])) and is_lower_start(r["text"] or "")]
check("küçük harfle başlayan bölünmüş parçalar önerilmiyor", [(r["id"],) for r in split_lower if r["recommended"]], len(split_lower))
check("n_words = text kelime sayısı",
      [(r["id"], r["n_words"], len(r["text"].split())) for r in manifest if r["n_words"] != len(r["text"].split())], len(manifest))
plain = [r for r in manifest if not re.search(r"\d|%|₺|\$|€", r["text"]) and not re.search(r"\b(vb|vs|vd|örn|bkz|yy|dr|prof|doç|sn|hz|no|tel|cad|sok)\.", r["text"], re.I)]
check("text_spoken = text (sayı/kısaltma yoksa)", [r["id"] for r in plain if r["text_spoken"] != r["text"]], len(plain))
digits = [r for r in manifest if re.search(r"\d", r["text"])]
alnum = re.compile(r"[A-Za-zÇĞİÖŞÜçğıöşü]\d|\d[A-Za-zÇĞİÖŞÜçğıöşü]")   # MI6, M5, 3G: normalizasyon kapsamı dışı (açık madde)
pure = [r for r in digits if not alnum.search(r["text"])]
check("text_spoken rakamsız (sayı varsa çevrilmiş; harf+rakam belirteçleri hariç)", [(r["id"], r["text_spoken"]) for r in pure if re.search(r"\d", r["text_spoken"] or "")], len(pure))
results.append(("bilgi: harf+rakam belirteçli klip (MI6, M5 — okunuşa çevrilmiyor)", True, f"{len(digits) - len(pure)} klip"))

# ---------------------------------------------------------------- E. ölçüm aralıkları ve iç tutarlılık
def rng_bad(key, lo, hi):
    return [(r["id"], r[key]) for r in manifest if r.get(key) is not None and not (lo <= r[key] <= hi)]
check("speech_ratio ∈ [0,1]", rng_bad("speech_ratio", 0, 1), len(manifest))
check("word_confidence ∈ [0,1], min ≤ mean",
      rng_bad("word_confidence", 0, 1) + [(r["id"],) for r in manifest if r["word_confidence"] is not None and r["word_confidence"] > r["word_confidence_mean"] + 1e-6], len(manifest))
check("align_score ∈ [0,1], min ≤ mean",
      rng_bad("align_score_min", 0, 1) + [(r["id"],) for r in manifest if r.get("align_score_min") is not None and r["align_score_min"] > r["align_score_mean"] + 1e-6], len(manifest))
spoken = [r for r in manifest if r["speech_ratio"] > 0]   # konuşma yoksa baş = son = süre (tanım)
check("sessizlikler ≤ duration (konuşmalı kliplerde)",
      [(r["id"],) for r in spoken if max(r["internal_silence_sec"], r["leading_silence_sec"], r["trailing_silence_sec"]) > r["duration"] + 1e-3
       or r["leading_silence_sec"] + r["trailing_silence_sec"] > r["duration"] + 1e-3], len(spoken))
check("speech_ratio ≈ 1 − (baş+son sessizlik)/süre üst sınırı",
      [(r["id"], r["speech_ratio"]) for r in spoken if r["speech_ratio"] > 1 - (r["leading_silence_sec"] + r["trailing_silence_sec"]) / r["duration"] + 0.02], len(spoken))
results.append(("bilgi: konuşma bulunmayan klip (speech_ratio = 0)", True, f"{len(manifest) - len(spoken)} klip"))
check("müzik: ayrıştırılmamışsa −80 ve skor < eleme eşiği; ayrıştırılmışsa skor ≥ eşik ve stem var",
      [(r["id"], r["music_to_speech_db"], r["music_score_audioset"]) for r in manifest
       if (not r["music_db_separated"] and (r["music_to_speech_db"] != -80.0 or r["music_score_audioset"] > 0.05 + 5e-5 or "music_stem_db" in r))
       or (r["music_db_separated"] and (r["music_score_audioset"] < 0.05 - 5e-5 or "music_stem_db" not in r))], len(manifest))
sep = [r for r in manifest if r["music_db_separated"]]
def stem_db(r):
    s = r["music_stem_db"]; acc = sum(10 ** (s[k] / 10) for k in ("drums", "bass", "other"))
    return max(10 * np.log10(acc) - s["vocals"], -80.0)
# eşlik dalga toplamının RMS'i, stem güçlerinin toplamından faz farkı kadar sapar (ölçülen en çok ~4 dB); bilgi
_dev = [abs(stem_db(r) - r["music_to_speech_db"]) for r in sep]
results.append(("bilgi: music_to_speech_db ile stem güç toplamı farkı (faz)", True,
                f"{len(sep)} ayrıştırılmış klip, |fark| medyan {np.median(_dev) if _dev else 0:.2f} dB, maks {max(_dev) if _dev else 0:.2f} dB"))

# ---------------------------------------------------------------- F. kelime dosyalarından yeniden hesap
bad_conf, bad_align, bad_gap, bad_span_text, bad_cover, tot = [], [], [], [], [], 0
for sid, rows in per_src.items():
    src = sources[sid]
    raw = [json.loads(l) for l in resolve(src["meta"]["words"]).open(encoding="utf-8")]
    aligned_path = src["meta"].get("aligned")
    aligned = [json.loads(l) for l in resolve(aligned_path).open(encoding="utf-8")] if aligned_path else None
    words = attach_clitics([Word(w["text"], w["start"], w["end"], w.get("prob")) for w in raw])
    ascore = attach_clitics([Word(w["text"], 0.0, 0.0, w.get("align_score")) for w in aligned]) if aligned else None
    for r in rows:
        tot += 1
        a, b = json.loads(db_clips[r["id"]]["meta_json"])["word_span"]
        probs = [w.prob for w in words[a:b] if w.prob is not None]
        if probs and (abs(min(probs) - r["word_confidence"]) > 0.0015 or abs(float(np.mean(probs)) - r["word_confidence_mean"]) > 0.0015):
            bad_conf.append((r["id"], r["word_confidence"], round(min(probs), 3)))
        if ascore is not None and r.get("align_score_min") is not None:
            sc = [w.prob for w in ascore[a:b] if w.prob is not None]
            if sc and (abs(min(sc) - r["align_score_min"]) > 0.0015 or abs(float(np.mean(sc)) - r["align_score_mean"]) > 0.0015):
                bad_align.append((r["id"], r["align_score_min"], round(min(sc), 3)))
        if " ".join(w.text for w in words[a:b]) != r["text_raw"]:
            bad_span_text.append((r["id"], r["text_raw"][:40]))
        # komşu boşlukları: bölütleme hizalayıcı damgalarını kullanıyorsa onlardan
        tw = attach_clitics([Word(w["text"], w.get("align_start", w["start"]), w.get("align_end", w["end"]), None) for w in (aligned or raw)])
        if r["start"] > tw[a].start + 0.05 or r["end"] < tw[b - 1].end - 0.05:
            bad_cover.append((r["id"], round(r["start"] - tw[a].start, 2), round(tw[b - 1].end - r["end"], 2)))
        lead = round(tw[a].start - tw[a - 1].end, 3) if a > 0 else None
        trail = round(tw[b].start - tw[b - 1].end, 3) if b < len(tw) else None
        if (lead is None) != (r["lead_gap_sec"] is None) or (trail is None) != (r["trail_gap_sec"] is None) \
                or (lead is not None and abs(lead - r["lead_gap_sec"]) > 0.002) or (trail is not None and abs(trail - r["trail_gap_sec"]) > 0.002):
            bad_gap.append((r["id"], r["lead_gap_sec"], lead, r["trail_gap_sec"], trail))
check("word_confidence(min/mean) = ASR kelime olasılıklarından yeniden hesap", bad_conf, tot)
check("klip kendi kelimelerini kapsıyor (start ≤ ilk kelime +50 ms, end ≥ son kelime −50 ms)", bad_cover, tot)
check("align_score(min/mean) = hizalama dosyasından yeniden hesap", bad_align, tot)
check("text_raw = kelime aralığının birleşimi", bad_span_text, tot)
check("lead/trail_gap = komşu kelime boşluğu (None ↔ kaydın ilk/son kelimesi)", bad_gap, tot)

# ---------------------------------------------------------------- G. işaret ↔ ölçüm
seg_min = float(cfg.get("segment.min_sec", 1.5)); seg_max = float(cfg.get("segment.max_sec", 15.0))
inaud = float(cfg.get("music.inaudible_db", -30.0)); amin = cfg.get("music.audioset_min", None)
def music_rule(r):
    return r["music_to_speech_db"] > inaud and (amin is None or r["music_score_audioset"] >= float(amin))
check(f"background_music ⇔ music_to_speech_db > {inaud}" + (f" ve audioset ≥ {amin}" if amin is not None else ""),
      [(r["id"], r["music_to_speech_db"], r["music_score_audioset"]) for r in manifest if ("background_music" in r["flags"]) != music_rule(r)], len(manifest))
check("duplicate ⇔ duplicate_of dolu", [(r["id"],) for r in manifest if ("duplicate" in r["flags"]) != bool(r["duplicate_of"])], len(manifest))
check("duplicate_of geçerli bir klip ve aynı metin", [(r["id"], r["duplicate_of"]) for r in manifest if r["duplicate_of"] and (r["duplicate_of"] not in by_id or by_id[r["duplicate_of"]]["text"].lower() != r["text"].lower())], len(manifest))
check(f"oversize → duration > {seg_max}", [(r["id"], r["duration"]) for r in manifest if "oversize" in r["flags"] and r["duration"] <= seg_max], len(manifest))
shorts = [r for r in manifest if "short" in r["flags"]]
check(f"short → kelime süresi < {seg_min} (pay eklenmeden)", [(r["id"], r["duration"]) for r in shorts if r["duration"] - 0.4 >= seg_min], len(shorts))
unflag_short = [r for r in manifest if "short" not in r["flags"] and r["duration"] < seg_min]
results.append((f"bilgi: short işaretsiz ama duration < {seg_min}", True, f"{len(unflag_short)} klip (pay/sınır iyileştirme sonrası kısalanlar; işaret payı eklenmeden verilir)"))
check("flags şemadaki adlardan", [(r["id"], f) for r in manifest for f in r["flags"] if f not in {"forced_split", "gap_split", "short", "oversize", "background_music", "duplicate", "boilerplate", "unreadable_audio"}], len(manifest))

# ---------------------------------------------------------------- H. politika yeniden hesap
policy = cfg.policy()
bad = []
for r in manifest:
    metrics = {k: r.get(k) for k in schema.BY_NAME if schema.BY_NAME[k].stage in ("segment", "align", "clip_qc", "music") and k in r}
    ok, reasons = policy.evaluate(metrics, r["flags"])
    if ok != r["recommended"] or sorted(reasons) != sorted(r["exclusion_reasons"]) or r["policy_version"] != policy.version:
        bad.append((r["id"], r["recommended"], ok, r["exclusion_reasons"], list(reasons)))
check(f"recommended/exclusion_reasons = politika v{policy.version} ile yeniden hesap", bad, len(manifest))
check("recommended → exclusion_reasons boş", [(r["id"],) for r in manifest if r["recommended"] and r["exclusion_reasons"]], len(manifest))

# ---------------------------------------------------------------- I. kaynak düzeyi
bad = []
for sid, s in sources.items():
    m = s["meta"]; cont = m.get("container_duration") or 0
    trunc = bool(cont) and (s["duration"] or 0) < 0.95 * cont
    if trunc != ("truncated_source" in m.get("source_flags", [])):
        bad.append((sid, s["duration"], cont))
    rows = per_src.get(sid, [])
    if rows and any(r["source_sample_rate"] != s["source_sample_rate"] or r["channel"] != s["channel"] for r in rows):
        bad.append((sid, "klip kaynak alanları uyuşmuyor"))
check("truncated_source ⇔ çözülen süre < 0,95·kapsayıcı; klip kaynak alanları", bad, len(sources))

# ---------------------------------------------------------------- J. DB ↔ manifest
check("DB klip sayısı = manifest", [] if set(db_clips) == set(by_id) else [(len(db_clips), len(by_id))], 1)
bad = []
for cid, d in db_clips.items():
    r = by_id.get(cid)
    if not r:
        continue
    dm = json.loads(d["metrics_json"] or "{}")
    for k, v in dm.items():
        if k in r and r[k] != v:
            bad.append((cid, k, v, r[k]))
    if (d["text"], d["start"], d["end"]) != (r["text"], r["start"], r["end"]):
        bad.append((cid, "text/start/end"))
check("DB ölçümleri/metin/sınırlar = manifest", bad, len(db_clips))

# ---------------------------------------------------------------- rapor
fails = 0
print(f"{WORK}: {len(manifest)} klip, {len(sources)} kaynak, ses örneği {n}")
for name, ok, info in results:
    fails += not ok
    print(f"  {'PASS' if ok else 'FAIL'}  {name}: {info}")
print(f"{'HATA YOK' if not fails else str(fails) + ' denetim FAIL'}")
sys.exit(1 if fails else 0)
