"""Bölütleme ablasyonu: cümle hizalı kesim ile sessizlik hizalı kesim.

Aynı kayıtlar, aynı kelime zaman damgaları, aynı süre ayarları; değişen tek
şey kesimin nerede yapıldığı. Cümle kolu tam koşunun ürettiği kliplerdir
(veritabanından okunur, yeniden üretilmez); taban kol `kiraat.segment_vad`
ile burada üretilir — VAD'ın konuşma bölgeleri, sessizliklerde kesilir.

Ölçülenler, iki kol için de aynı tanımla:

  cümle ortasından başlayan klip   metin küçük harfle başlıyor
  cümle ortasında biten klip       metin cümle sonu noktalamasıyla bitmiyor
  süre dağılımı                    medyan, %5–%95, tavana dayanan klip payı
  hizalama güveni                  klip başına asgari/ortalama align_score

Kullanım (önce küçük, sonra ölçek):

    python scripts/ablate_segmentation.py --per-channel 1 --limit 5
    python scripts/ablate_segmentation.py --per-channel 8
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import statistics as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from kiraat.config import Config
from kiraat.segment import Word, attach_clitics
from kiraat.segment_vad import segment_vad
from kiraat.stages.asr import load_words
from kiraat.text.turkish import has_sentence_end, is_lower_start


_VAD = None


def speech_regions(audio: str, vad_opts: dict) -> list[tuple[float, float]]:
    """Silero VAD konuşma bölgeleri (saniye). Hattaki `vad` ayarlarıyla.

    Tek süreçte 76× gerçek zaman ölçüldü (6 Eyl 2026, 160 dk'lık kayıt:
    14 s yükleme + 112 s VAD), o yüzden kayıtlar süreç havuzuna dağıtılır.
    """
    import torch
    import torchaudio
    from silero_vad import get_speech_timestamps, load_silero_vad

    global _VAD
    if _VAD is None:
        torch.set_num_threads(2)
        _VAD = load_silero_vad()
    wave, sr = torchaudio.load(audio)
    wave = wave.mean(dim=0)
    if sr != 16000:
        wave = torchaudio.functional.resample(wave, sr, 16000)
    ts = get_speech_timestamps(
        wave, _VAD, sampling_rate=16000, return_seconds=True,
        threshold=float(vad_opts.get("threshold", 0.5)),
        min_speech_duration_ms=int(vad_opts.get("min_speech_duration_ms", 250)),
        min_silence_duration_ms=int(vad_opts.get("min_silence_duration_ms", 300)),
        speech_pad_ms=int(vad_opts.get("speech_pad_ms", 100)),
    )
    return [(t["start"], t["end"]) for t in ts]


def vad_arm(job: tuple) -> tuple[int, list[dict]]:
    """Bir kaydın taban kol klipleri; işçi süreçlerinde koşar."""
    sid, audio, aligned, vad_opts, seg_cfg = job
    raw = load_words(aligned)
    words = attach_clitics([Word(w["text"], w.get("align_start", w["start"]),
                                 w.get("align_end", w["end"]), w.get("align_score"))
                            for w in raw])
    rows = []
    for c in segment_vad(speech_regions(audio, vad_opts), words, seg_cfg):
        a, b = c.word_span
        sc = [w.prob for w in words[a:b] if w.prob is not None]
        rows.append({"duration": round(c.end - c.start, 3), "text": c.text.strip(),
                     "align_score_mean": round(st.mean(sc), 4) if sc else None,
                     "align_score_min": round(min(sc), 4) if sc else None,
                     "flags": list(c.flags)})
    return sid, rows


def stats(clips: list[dict], cfg) -> dict:
    if not clips:
        return {}
    durs = sorted(c["duration"] for c in clips)
    lower = [c for c in clips if c["text"] and is_lower_start(c["text"])]
    unfinished = [c for c in clips if c["text"] and not has_sentence_end(c["text"])]
    # İşaretsiz kırık: klibin kırık olduğunu söyleyen hiçbir işaret yok, yani
    # kusur kullanıcıya görünmüyor ve önerilen alt kümeden düşmüyor. Cümle
    # kolunda kırık klipler `forced_split`/künye işaretlerini taşır; taban
    # kolda yalnızca `hard_cut` vardır ve kırıkların çoğu işaretsizdir.
    unflagged_lower = [c for c in lower if not c["flags"]]
    unflagged_unfinished = [c for c in unfinished if not c["flags"]]
    at_cap = [c for c in clips if c["duration"] >= cfg.max_sec - 0.05]
    scores = [c["align_score_mean"] for c in clips if c.get("align_score_mean") is not None]
    mins = [c["align_score_min"] for c in clips if c.get("align_score_min") is not None]
    return {
        "klip": len(clips),
        "saat": round(sum(durs) / 3600, 3),
        "cümle_ortasından_başlayan": len(lower),
        "cümle_ortasından_başlayan_%": round(100 * len(lower) / len(clips), 2),
        "cümle_ortasında_biten": len(unfinished),
        "cümle_ortasında_biten_%": round(100 * len(unfinished) / len(clips), 2),
        "işaretsiz_kırık_başlangıç": len(unflagged_lower),
        "işaretsiz_kırık_başlangıç_%": round(100 * len(unflagged_lower) / len(clips), 2),
        "işaretsiz_kırık_bitiş_%": round(100 * len(unflagged_unfinished) / len(clips), 2),
        "iki_ucu_kırık": sum(1 for c in clips if c["text"] and is_lower_start(c["text"])
                             and not has_sentence_end(c["text"])),
        "süre_medyan": round(st.median(durs), 2),
        "süre_p05": round(durs[int(0.05 * len(durs))], 2),
        "süre_p95": round(durs[int(0.95 * len(durs))], 2),
        "tavana_dayanan_%": round(100 * len(at_cap) / len(clips), 2),
        "align_score_ort": round(st.mean(scores), 4) if scores else None,
        "align_score_min_ort": round(st.mean(mins), 4) if mins else None,
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--config", default="configs/default.yaml")
    p.add_argument("--work-root", default="work/full-1")
    p.add_argument("--per-channel", type=int, default=1, help="kanal başına kaç kayıt")
    p.add_argument("--limit", type=int, default=0, help="toplam kayıt sınırı (0: sınırsız)")
    p.add_argument("--seed", type=int, default=20260906)
    p.add_argument("--workers", type=int, default=8)
    p.add_argument("--out", default=None)
    args = p.parse_args()

    cfg = Config.load(args.config)
    seg_cfg = cfg.segment_config()
    vad_opts = dict(cfg.section("vad"))
    work = Path(args.work_root)
    db = sqlite3.connect(f"file:{work}/db/state.sqlite?mode=ro", uri=True)

    import random
    rng = random.Random(args.seed)
    by_channel: dict[str, list] = {}
    for sid, ch, meta in db.execute("select id, channel, meta_json from sources where error is null"):
        by_channel.setdefault(ch, []).append((sid, json.loads(meta)))
    chosen = []
    for ch in sorted(by_channel):
        rows = sorted(by_channel[ch])
        rng.shuffle(rows)
        chosen += [(ch, sid, meta) for sid, meta in rows[: args.per_channel]]
    if args.limit:
        chosen = chosen[: args.limit]

    jobs = []
    meta_of = {}
    for ch, sid, meta in chosen:
        aligned = meta.get("aligned")
        if not aligned or not Path(aligned).exists():
            print(f"  atlandı (hizalama yok): src{sid:05d}")
            continue
        meta_of[sid] = (ch, meta)
        jobs.append((sid, meta["audio"], aligned, vad_opts, seg_cfg))

    cumle: list[dict] = []
    vad: list[dict] = []
    per_source = []
    from concurrent.futures import ProcessPoolExecutor

    with ProcessPoolExecutor(max(1, args.workers)) as pool:
        for done, (sid, v_rows) in enumerate(pool.map(vad_arm, jobs), 1):
            ch, _ = meta_of[sid]
            k_rows = []
            for dur, text, metrics, flags in db.execute(
                    "select duration, text, metrics_json, flags_json from clips where source_id=?", (sid,)):
                m = json.loads(metrics)
                k_rows.append({"duration": dur, "text": text or "",
                               "align_score_mean": m.get("align_score_mean"),
                               "align_score_min": m.get("align_score_min"),
                               "flags": json.loads(flags)})
            cumle += k_rows
            vad += v_rows
            per_source.append({"source_id": sid, "channel": ch,
                               "cümle": stats(k_rows, seg_cfg), "vad": stats(v_rows, seg_cfg)})
            print(f"  [{done}/{len(jobs)}] src{sid:05d} {ch}: cümle {len(k_rows)} klip / vad {len(v_rows)} klip",
                  flush=True)

    out = {"kayıt": len(per_source), "cümle": stats(cumle, seg_cfg), "vad": stats(vad, seg_cfg),
           "kaynak_başına": per_source}
    dst = Path(args.out or (work / "ablation" / "segmentation.json"))
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"\n{len(per_source)} kayıt | ölçüm: {dst}\n")
    keys = [k for k in out["cümle"]]
    w = max(len(k) for k in keys)
    print(f"{'':{w}}  {'cümle hizalı':>14}  {'sessizlik hizalı':>16}")
    for k in keys:
        print(f"{k:{w}}  {str(out['cümle'][k]):>14}  {str(out['vad'][k]):>16}")


if __name__ == "__main__":
    main()
