"""Klipleri kendi sesiyle yeniden yazıya çevirip metinle karşılaştır (CER).

`internal_silence_sec` / `speech_ratio` kuralları 10.915 klibi (23,4 saat)
önerilen alt kümeden düşürüyor. Örneklemde ölçüldü (7 Eyl 2026,
`scripts/probe_silence_rule.py`): bu kliplerin dörtte üçü metin–ses
uyuşması bakımından KUSURSUZ (CER = 0), ama içlerinde gerçek uyuşmazlık
taşıyanlar da var (%2–3,5'te CER > 0,20; kontrol grubunda %0). Yani kural
toptan kaldırılamaz, karar klip başına verilmeli.

Bu betik o kararın ölçümünü üretir: her klibin sesi tek başına ASR'den
geçirilir ve klibin `text` / `text_spoken` alanıyla karşılaştırılır; düşük
olan CER yazılır (ASR rakamı hem "1923" hem "bin dokuz yüz yirmi üç" diye
yazabilir, ikisi de doğrudur).

Çıktı satır satır JSONL'dir ve koşu kesilirse kaldığı yerden sürer.

    python scripts/recheck_clips.py --out work/full-1/ablation/recheck.jsonl
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.probe_silence_rule import DIGIT, RULES, cer  # noqa: E402


def select(manifest: str) -> list[dict]:
    """Yalnızca bu iki kural yüzünden elenen klipler."""
    out = []
    for line in open(manifest, encoding="utf-8"):
        r = json.loads(line)
        if r["recommended"]:
            continue
        e = set(r["exclusion_reasons"])
        if e and e <= RULES:
            out.append(r)
    return out


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--manifest", default="work/full-1/manifests/clips.jsonl")
    p.add_argument("--out", default="work/full-1/ablation/recheck.jsonl")
    p.add_argument("--device", default="cuda:0")
    p.add_argument("--beam", type=int, default=5)
    p.add_argument("--batch", type=int, default=0, help="0: klip klip; >0: toplu çıkarım")
    p.add_argument("--limit", type=int, default=0)
    args = p.parse_args()

    clips = select(args.manifest)
    dst = Path(args.out)
    dst.parent.mkdir(parents=True, exist_ok=True)
    done = set()
    if dst.exists():
        done = {json.loads(l)["id"] for l in dst.open(encoding="utf-8") if l.strip()}
    todo = [c for c in clips if c["id"] not in done]
    if args.limit:
        todo = todo[: args.limit]
    print(f"havuz {len(clips)} | bitmiş {len(done)} | koşacak {len(todo)}", flush=True)

    from faster_whisper import BatchedInferencePipeline, WhisperModel

    dev = args.device.split(":")
    model = WhisperModel("large-v3", device=dev[0],
                         device_index=int(dev[1]) if len(dev) > 1 else 0,
                         compute_type="float16")
    pipe = BatchedInferencePipeline(model=model) if args.batch else None

    t0 = time.time()
    with dst.open("a", encoding="utf-8") as fh:
        for i, r in enumerate(todo, 1):
            kw = dict(language="tr", beam_size=args.beam, temperature=0.0,
                      condition_on_previous_text=False, word_timestamps=False)
            if pipe is not None:
                segs, _ = pipe.transcribe(r["audio"], batch_size=args.batch, **kw)
            else:
                segs, _ = model.transcribe(r["audio"], **kw)
            hyp = " ".join(s.text for s in segs).strip()
            c = min(cer(r["text"], hyp), cer(r.get("text_spoken") or r["text"], hyp))
            fh.write(json.dumps({"id": r["id"], "cer": round(c, 4), "asr": hyp,
                                 "duration": r["duration"],
                                 "rakamlı": bool(DIGIT.search(r.get("text") or ""))},
                                ensure_ascii=False) + "\n")
            if i % 200 == 0:
                fh.flush()
                hız = i / (time.time() - t0)
                print(f"  {i}/{len(todo)} | {hız:.2f} klip/s | kalan "
                      f"{(len(todo) - i) / hız / 3600:.2f} saat", flush=True)
    print(f"bitti: {len(todo)} klip, {(time.time() - t0)/60:.1f} dk", flush=True)


if __name__ == "__main__":
    main()
