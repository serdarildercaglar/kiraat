"""Kanal düzeyinde künye/anons madenciliğini sına.

Her kanaldan birkaç kaydın ilk ve son dakikası ASR'ye verilir, kanal
içinde tekrar eden kelime dizileri madenlenir ve gözle denetlenmek üzere
basılır. Bulunanlar `probe_segment.py`nin okuyacağı JSON'a yazılır.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from kiraat.boilerplate import mine
from kiraat.config import Config

V1_DB = "/mnt/310C8DBF109E2BFC/projects/turkish-tts/voxcpm/work/db/state-v2.sqlite"

parser = argparse.ArgumentParser()
parser.add_argument("--config", default="configs/default.yaml")
parser.add_argument("--channels", nargs="+",
                    default=["BirDinle", "dinleyiniz", "ses-arşiv", "anahtarca", "idea_stüdyo"])
parser.add_argument("--per-channel", type=int, default=8)
parser.add_argument("--edge-sec", type=float, default=60.0, help="baştan ve sondan alınan süre")
parser.add_argument("--out", default=None)
parser.add_argument("--asr-model", default="large-v3")
args = parser.parse_args()

cfg = Config.load(args.config)
bp = cfg.section("boilerplate")
out_root = Path(args.out or Path(cfg.get("paths.work_root")) / "probe_boilerplate")
out_root.mkdir(parents=True, exist_ok=True)

_MODEL = None


def transcribe_words(wav: Path, cache: Path) -> list[str]:
    global _MODEL
    if cache.exists():
        return [json.loads(l)["text"] for l in cache.open(encoding="utf-8")]
    from faster_whisper import WhisperModel

    if _MODEL is None:
        _MODEL = WhisperModel(args.asr_model, device="cuda", compute_type="float16")
    segs, _ = _MODEL.transcribe(str(wav), language="tr", beam_size=5, temperature=0.0,
                                condition_on_previous_text=False, word_timestamps=True,
                                vad_filter=True)
    words = [{"text": w.word.strip(), "start": round(w.start, 3), "end": round(w.end, 3)}
             for s in segs for w in (s.words or ()) if w.word.strip()]
    with cache.open("w", encoding="utf-8") as fh:
        for w in words:
            fh.write(json.dumps(w, ensure_ascii=False) + "\n")
    return [w["text"] for w in words]


def decode(src: str, dst: Path, start: float, seconds: float) -> None:
    if dst.exists():
        return
    cmd = ["ffmpeg", "-nostdin", "-loglevel", "error", "-y", "-ss", f"{start:.3f}", "-t", f"{seconds:.3f}",
           "-i", src, "-ac", "1", "-ar", "16000", str(dst)]
    if subprocess.run(cmd).returncode != 0:
        raise RuntimeError(" ".join(cmd))


con = sqlite3.connect(f"file:{V1_DB}?mode=ro&immutable=1", uri=True)
found: dict[str, list[list[str]]] = {}
for channel in args.channels:
    rows = con.execute(
        "select id, path, duration from sources where channel=? and state='DONE' and duration>300 "
        "order by id limit ?", (channel, args.per_channel)).fetchall()
    cdir = out_root / channel
    cdir.mkdir(exist_ok=True)
    recordings: dict[str, list[str]] = {}
    for sid, path, duration in rows:
        head, tail = cdir / f"src{sid:05d}-head.wav", cdir / f"src{sid:05d}-tail.wav"
        decode(path, head, 0.0, args.edge_sec)
        decode(path, tail, max(duration - args.edge_sec, 0.0), args.edge_sec)
        tokens = transcribe_words(head, cdir / f"src{sid:05d}-head.jsonl")
        tokens += ["<...>"]  # baş ile son arasında n-gram oluşmasın
        tokens += transcribe_words(tail, cdir / f"src{sid:05d}-tail.jsonl")
        recordings[str(sid)] = tokens
    mined = mine(recordings, min_recordings=int(bp["min_recordings"]), min_words=int(bp["min_words"]),
                 max_words=int(bp["max_words"]), head_words=None, tail_words=None)
    print(f"\n== {channel}: {len(rows)} kayıt, {len(mined)} ifade")
    for phrase, count in mined[:25]:
        print(f"  {count:2d}/{len(rows)}  {' '.join(phrase)}")
    found[channel] = [list(p) for p, _ in mined]

    # Her kaydın ilk 15 kelimesi: künyenin nasıl göründüğünü göstermek için.
    print("  kayıt başları:")
    for sid, toks in list(recordings.items())[:4]:
        print(f"    src{int(sid):05d}: {' '.join(toks[:15])}")

json.dump(found, (out_root / "boilerplate.json").open("w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"\nyazıldı: {out_root / 'boilerplate.json'}")
