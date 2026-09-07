"""`internal_silence_sec` / `speech_ratio` kuralları metin–ses uyuşmazlığı mı eliyor?

İki kural, yalnız başlarına 10.915 klibi (23,4 saat) önerilen alt kümeden
düşürüyor. Bunlar gerçekten kusurlu mu, yoksa yalnızca içinde uzun duraklama
olan sağlam klipler mi? Kulak kullanılamadığı için ölçüt nesnel: **klibin
kendi sesi tek başına yeniden yazıya çevrilir ve klibin metniyle
karşılaştırılır.** Sınır kaymışsa (klipte metinde olmayan ses ya da metinde
olup seste olmayan kelime) CER yükselir; klip sağlamsa kontrol grubuyla aynı
çıkar.

Kontrol grubu şart: ASR kusursuz değildir, "iyi CER"i o tanımlar.

    python scripts/probe_silence_rule.py --n 200
"""

from __future__ import annotations

import argparse
import json
import random
import re
import statistics as st
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from kiraat.text.turkish import lower  # noqa: E402

DIGIT = re.compile(r"\d")
PUNCT = re.compile(r"[^\w\s]", re.UNICODE)
RULES = {"internal_silence_sec>1.0", "speech_ratio<0.6"}


def norm(text: str) -> str:
    t = unicodedata.normalize("NFC", text or "")
    return re.sub(r"\s+", " ", PUNCT.sub(" ", lower(t))).strip()


def cer(ref: str, hyp: str) -> float:
    """Karakter hata oranı (Levenshtein / referans uzunluğu)."""
    r, h = norm(ref), norm(hyp)
    if not r:
        return 0.0 if not h else 1.0
    prev = list(range(len(h) + 1))
    for i, rc in enumerate(r, 1):
        cur = [i]
        for j, hc in enumerate(h, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (rc != hc)))
        prev = cur
    return prev[-1] / len(r)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--manifest", default="work/full-1/manifests/clips.jsonl")
    p.add_argument("--n", type=int, default=200, help="grup başına klip")
    p.add_argument("--seed", type=int, default=20260907)
    p.add_argument("--device", default="cuda:0")
    p.add_argument("--out", default="work/full-1/ablation/silence_rule.json")
    args = p.parse_args()

    gruplar: dict[str, list] = {"elenmiş-rakamlı": [], "elenmiş-rakamsız": [], "kontrol": []}
    for line in open(args.manifest, encoding="utf-8"):
        r = json.loads(line)
        e = set(r["exclusion_reasons"])
        if r["recommended"]:
            gruplar["kontrol"].append(r)
        elif e and e <= RULES:
            gruplar["elenmiş-rakamlı" if DIGIT.search(r.get("text") or "")
                    else "elenmiş-rakamsız"].append(r)
    rng = random.Random(args.seed)
    örnek = {k: rng.sample(v, min(args.n, len(v))) for k, v in gruplar.items()}
    for k, v in örnek.items():
        print(f"{k}: {len(v)} klip (havuz {len(gruplar[k])})")

    from faster_whisper import WhisperModel

    from kiraat.config import Config
    cfg = Config.load("configs/default.yaml")
    model = WhisperModel("large-v3", device=args.device.split(":")[0],
                         device_index=int(args.device.split(":")[1]) if ":" in args.device else 0,
                         compute_type="float16",
                         download_root=None)

    out = {}
    for grup, klipler in örnek.items():
        satır = []
        for r in klipler:
            segs, _ = model.transcribe(r["audio"], language="tr", beam_size=5, temperature=0.0,
                                       condition_on_previous_text=False, word_timestamps=False)
            hyp = " ".join(s.text for s in segs).strip()
            c = min(cer(r["text"], hyp), cer(r.get("text_spoken") or r["text"], hyp))
            satır.append({"id": r["id"], "cer": round(c, 4), "duration": r["duration"],
                          "internal_silence_sec": r.get("internal_silence_sec"),
                          "speech_ratio": r.get("speech_ratio"),
                          "text": r["text"], "asr": hyp})
        out[grup] = satır
        v = sorted(x["cer"] for x in satır)
        print(f"\n{grup}: CER medyan {st.median(v):.4f} | ortalama {st.mean(v):.4f} | "
              f"p90 {v[int(.9*(len(v)-1))]:.4f} | CER=0 payı %{100*sum(1 for x in v if x==0)/len(v):.1f} | "
              f"CER>0,20 payı %{100*sum(1 for x in v if x>0.20)/len(v):.1f}")

    dst = Path(args.out); dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nayrıntı: {dst}")


if __name__ == "__main__":
    main()
