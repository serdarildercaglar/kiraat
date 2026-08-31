"""Cümle hizalı bölütlemeyi gerçek kayıtlarda sına — v1 klipleriyle yan yana.

Birkaç kaydın ilk N dakikası uzun formda ASR'ye verilir (kelime zaman
damgalı), kelimeler `kiraat.segment.segment` ile cümle sınırında kesilir ve
aynı pencere için v1'in sessizlikte kestiği kliplerle aynı ölçülerle
karşılaştırılır: cümle ortasından başlayan klip oranı, cümle sonu
noktalamasıyla bitmeyen klip oranı, süre dağılımı.

İki sistemin klipleri de dinlenebilir olarak kesilir; sınır temizliği
(kelime kesilmiş mi) kulakla denetlenir; dinleme sayfası `scripts/listen_ui.py` ile üretilir.

Not: Hizalama aşaması henüz yok; kelime zaman damgaları Whisper'ın kendi
çapraz-dikkat hizalamasından geliyor. Konfigdeki zorlamalı hizalayıcı
bağlandığında bu betik onun çıktısıyla yeniden koşulmalı.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import statistics
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from kiraat.config import Config
from kiraat.boilerplate import find_spans
from kiraat.boundaries import envelope, refine_boundaries
from kiraat.segment import Word, attach_clitics, segment
from kiraat.text.turkish import has_sentence_end, is_lower_start

V1_ROOT = Path("/mnt/310C8DBF109E2BFC/projects/turkish-tts/voxcpm/work")
DEFAULT_SOURCES = [2, 1016, 1355, 528, 1130]  # BirDinle, dinleyiniz, ses-arşiv, anahtarca, idea_stüdyo

parser = argparse.ArgumentParser()
parser.add_argument("--config", default="configs/default.yaml")
parser.add_argument("--sources", nargs="+", type=int, default=DEFAULT_SOURCES,
                    help="v1 durum veritabanındaki kaynak kimlikleri")
parser.add_argument("--minutes", type=float, default=6.0)
parser.add_argument("--out", default=None, help="varsayılan: <work_root>/probe_segment")
parser.add_argument("--db", default=str(V1_ROOT / "db" / "state-v2.sqlite"))
parser.add_argument("--asr-model", default="large-v3")
parser.add_argument("--no-cut", action="store_true", help="klip dosyalarını kesme")
parser.add_argument("--no-refine", action="store_true", help="ses tabanlı sınır iyileştirmesini kapat")
parser.add_argument("--boilerplate", default=None,
                    help="probe_boilerplate.py çıktısı; varsayılan <work_root>/probe_boilerplate/boilerplate.json")
args = parser.parse_args()

cfg = Config.load(args.config)
seg_cfg = cfg.segment_config()
out_root = Path(args.out or Path(cfg.get("paths.work_root")) / "probe_segment")
out_root.mkdir(parents=True, exist_ok=True)
window = args.minutes * 60.0
bp_path = Path(args.boilerplate or Path(cfg.get("paths.work_root")) / "probe_boilerplate" / "boilerplate.json")
BOILERPLATE: dict[str, list[list[str]]] = json.load(bp_path.open(encoding="utf-8")) if bp_path.exists() else {}
if BOILERPLATE:
    print(f"boilerplate ifadeleri: {bp_path} ({sum(map(len, BOILERPLATE.values()))} ifade)")
target_sr = int(cfg.get("prepare.target_sr", 24000))


# ------------------------------------------------------------------ yardımcılar
def run(cmd: list[str]) -> None:
    if subprocess.run(cmd).returncode != 0:
        raise RuntimeError(" ".join(cmd))


def decode(src: str, dst: Path, sr: int, seconds: float) -> None:
    if dst.exists():
        return
    run(["ffmpeg", "-nostdin", "-loglevel", "error", "-y", "-t", f"{seconds:.3f}",
         "-i", src, "-ac", "1", "-ar", str(sr), str(dst)])


def cut(src_wav: Path, dst: Path, start: float, end: float) -> None:
    if dst.exists():
        return
    run(["ffmpeg", "-nostdin", "-loglevel", "error", "-y", "-ss", f"{start:.3f}",
         "-t", f"{end - start:.3f}", "-i", str(src_wav), str(dst)])


def transcribe(wav: Path, cache: Path) -> list[dict]:
    """Kelime zaman damgalı uzun form ASR; sonuç önbelleğe yazılır."""
    if cache.exists():
        return [json.loads(l) for l in cache.open(encoding="utf-8")]
    from faster_whisper import WhisperModel

    global _MODEL
    if "_MODEL" not in globals():
        _MODEL = WhisperModel(args.asr_model, device="cuda", compute_type="float16")
    asr, vad = cfg.section("asr"), cfg.section("vad")
    segments, _ = _MODEL.transcribe(
        str(wav),
        language=asr.get("language", "tr"),
        beam_size=5,
        temperature=float(asr.get("temperature", 0.0)),
        condition_on_previous_text=bool(asr.get("condition_on_previous_text", False)),
        word_timestamps=True,
        vad_filter=True,
        vad_parameters=dict(
            threshold=float(vad.get("threshold", 0.5)),
            min_speech_duration_ms=int(vad.get("min_speech_duration_ms", 250)),
            min_silence_duration_ms=int(vad.get("min_silence_duration_ms", 300)),
            speech_pad_ms=int(vad.get("speech_pad_ms", 100)),
        ),
    )
    words: list[dict] = []
    for seg in segments:
        for w in seg.words or ():
            tok = w.word.strip()
            if tok:
                words.append({"text": tok, "start": round(w.start, 3), "end": round(w.end, 3),
                              "prob": round(w.probability, 4)})
    with cache.open("w", encoding="utf-8") as fh:
        for w in words:
            fh.write(json.dumps(w, ensure_ascii=False) + "\n")
    return words


def v1_clips(source_id: int) -> list[dict]:
    """v1'in bu kayıt için yayımladığı klipler (train+review+validation), pencere içindekiler."""
    marker = f"src{source_id:08d}/"
    rows: list[dict] = []
    for split in ("train", "validation", "review"):
        path = V1_ROOT / "manifests" / f"hf_{split}.jsonl"
        with path.open(encoding="utf-8") as fh:
            for line in fh:
                if marker not in line:
                    continue
                row = json.loads(line)
                if float(row["source_end_sec"]) <= window:
                    rows.append({"start": float(row["source_start_sec"]),
                                 "end": float(row["source_end_sec"]),
                                 "text": row["text"], "split": split,
                                 "decision": row.get("decision"),
                                 "reasons": row.get("review_reasons", [])})
    rows.sort(key=lambda r: r["start"])
    return rows


def measure(clips: list[dict]) -> dict:
    n = len(clips)
    if not n:
        return {"n": 0}
    durs = sorted(c["end"] - c["start"] for c in clips)
    lower = [is_lower_start(c["text"]) for c in clips]
    noend = [not has_sentence_end(c["text"]) for c in clips]
    q = lambda p: durs[min(int(p * n), n - 1)]
    return {
        "n": n,
        "lower_start": sum(lower), "no_end": sum(noend),
        "both": sum(a and b for a, b in zip(lower, noend)),
        "dur_med": statistics.median(durs), "dur_p5": q(0.05), "dur_p95": q(0.95),
        "hours": sum(durs) / 3600.0,
    }


def fmt(m: dict) -> str:
    if not m["n"]:
        return "  (klip yok)"
    n = m["n"]
    return (f"  n={n:4d}  küçük harfle başlayan {m['lower_start']:3d} (%{100*m['lower_start']/n:4.1f})"
            f"  cümle sonu olmayan {m['no_end']:3d} (%{100*m['no_end']/n:4.1f})"
            f"  süre med {m['dur_med']:.1f}s [p5 {m['dur_p5']:.1f}, p95 {m['dur_p95']:.1f}]"
            f"  toplam {m['hours']*60:.1f} dk")


# ------------------------------------------------------------------------ koşu
con = sqlite3.connect(f"file:{args.db}?mode=ro&immutable=1", uri=True)
manifest = out_root / "manifest.jsonl"
all_k: list[dict] = []
all_v: list[dict] = []
totals = {"kiraat": [], "v1": []}

with manifest.open("w", encoding="utf-8") as mf:
    for sid in args.sources:
        row = con.execute("select path, channel, duration from sources where id=?", (sid,)).fetchone()
        if not row:
            print(f"kaynak {sid} yok", file=sys.stderr)
            continue
        path, channel, duration = row
        sdir = out_root / f"src{sid:05d}"
        sdir.mkdir(exist_ok=True)
        wav16, wav24 = sdir / "asr16k.wav", sdir / f"src{target_sr}.wav"
        decode(path, wav16, 16000, window)
        decode(path, wav24, target_sr, window)

        words_raw = transcribe(wav16, sdir / "words.jsonl")
        words = attach_clitics([Word(w["text"], w["start"], w["end"], w["prob"]) for w in words_raw])
        probs = [w.prob for w in words]
        spans = find_spans([w.text for w in words], map(tuple, BOILERPLATE.get(channel, [])))
        clips = segment(words, seg_cfg, boilerplate=spans)
        if not args.no_refine:
            import soundfile as sf

            audio, sr = sf.read(str(wav24), dtype="float32", always_2d=True)
            # Sınır eşikleri konfigden (31 Ağu 2026): prob, hattın keseceği
            # kliplerin aynısını göstermek zorunda; kod varsayılanı değil.
            rc = cfg.refine_config()
            clips = refine_boundaries(clips, words, envelope(audio.mean(axis=1), sr, rc), seg_cfg, rc)

        k_rows = []
        for i, c in enumerate(clips):
            a, b = c.word_span
            wp = probs[a:b]
            rec = {"id": f"src{sid:05d}-k{i:03d}", "system": "kiraat", "source_id": sid,
                   "channel": channel, "start": c.start, "end": c.end, "text": c.text,
                   "flags": [f for f in c.flags if not f.startswith("snapped")],
                   "snapped": [f for f in c.flags if f.startswith("snapped")],
                   "asr_end": words[b - 1].end,
                   "lead_gap": round(words[a].start - words[a - 1].end, 3) if a > 0 else None,
                   "trail_gap": round(words[b].start - words[b - 1].end, 3) if b < len(words) else None,
                   "word_prob_min": round(min(wp), 3) if wp else None,
                   "word_prob_mean": round(sum(wp) / len(wp), 3) if wp else None,
                   "lower_start": is_lower_start(c.text), "no_end": not has_sentence_end(c.text)}
            if not args.no_cut:
                rec["audio"] = str(sdir / f"k{i:03d}.flac")
                cut(wav24, Path(rec["audio"]), c.start, c.end)
            k_rows.append(rec)
        v_rows = []
        for i, c in enumerate(v1_clips(sid)):
            rec = {"id": f"src{sid:05d}-v{i:03d}", "system": "v1", "source_id": sid,
                   "channel": channel, "start": c["start"], "end": c["end"], "text": c["text"],
                   "flags": [c["split"]] + list(c["reasons"]),
                   "lower_start": is_lower_start(c["text"]), "no_end": not has_sentence_end(c["text"])}
            if not args.no_cut:
                rec["audio"] = str(sdir / f"v{i:03d}.flac")
                cut(wav24, Path(rec["audio"]), c["start"], c["end"])
            v_rows.append(rec)
        for rec in k_rows + v_rows:
            mf.write(json.dumps(rec, ensure_ascii=False) + "\n")

        print(f"\n== [{channel}] {Path(path).name}  (ilk {args.minutes:g} dk / {duration/60:.0f} dk, "
              f"{len(words)} kelime)")
        print("kiraat:" + fmt(measure(k_rows)))
        print("v1    :" + fmt(measure(v_rows)))
        flags = {}
        for r in k_rows:
            for f in r["flags"]:
                flags[f] = flags.get(f, 0) + 1
        if flags:
            print("  kiraat işaretleri:", ", ".join(f"{k}={v}" for k, v in sorted(flags.items())))
        for r in k_rows:
            if "boilerplate" in r["flags"]:
                print(f"  boilerplate: [{r['start']:7.2f}–{r['end']:7.2f}] {r['text']}")
        print("  kiraat örnek klipler:")
        for r in k_rows[:4]:
            print(f"    [{r['start']:7.2f}–{r['end']:7.2f}] {r['text']}")
        bad = [r for r in v_rows if r["lower_start"]][:3]
        if bad:
            print("  v1'de cümle ortasından başlayan örnekler:")
            for r in bad:
                print(f"    [{r['start']:7.2f}–{r['end']:7.2f}] {r['text'][:110]}")
        all_k += k_rows
        all_v += v_rows

print("\n== TOPLAM")
print("kiraat:" + fmt(measure(all_k)))
print("v1    :" + fmt(measure(all_v)))
if all_k:
    pm = [r["word_prob_min"] for r in all_k if r["word_prob_min"] is not None]
    print(f"  kiraat klip başına asgari kelime olasılığı: med {statistics.median(pm):.3f}, "
          f"<0.40 olan klip {sum(p < 0.40 for p in pm)}/{len(pm)}  (Whisper'ın kendi olasılığı; hizalayıcı yok)")
print(f"\nmanifest: {manifest}")
