"""Kör dinleme sayfası üret.

`probe_segment.py` manifestosundan klip örnekler, kanal ve sistemi gizler,
kimlikleri opak sıra numarasına çevirir ve tek dosyalık bir HTML üretir
(sesler opus olarak gömülü). Sıra numarası → gerçek kimlik eşlemesi
`key.json` dosyasında kalır; cevaplar `answers-N.json` olarak yapıştırılınca
`--score` ile eşleştirilip özetlenir.

Dinleyicinin işi üç soru: klip cümle başında mı başlıyor, cümle bitince mi
bitiyor, başta/sonda kelime kesik mi.
"""

from __future__ import annotations

import argparse
import base64
import collections
import json
import random
import subprocess
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--manifest", default="work/probe_segment/manifest.jsonl")
parser.add_argument("--out", default="work/probe_segment/listen")
parser.add_argument("--n-kiraat", type=int, default=24)
parser.add_argument("--n-v1", type=int, default=8)
parser.add_argument("--prefer-small-gap", type=float, default=None,
                    help="kiraat kliplerinde önce baş/son boşluğu bu değerin altında olanları seç (s)")
parser.add_argument("--seed", type=int, default=11)
parser.add_argument("--score", default=None, help="cevap JSON'u; sayfa üretmek yerine skorla")
parser.add_argument("--audit-name", default="boundary-v2")
parser.add_argument("--questions", choices=["boundary", "music"], default="boundary")
args = parser.parse_args()

QUESTION_SETS = {
    "boundary": {
        "q": [
            {"k": "start", "label": "Başlangıç", "hint": "cümle başında mı başlıyor?",
             "opts": [["evet", "Cümle başı"], ["hayir", "Ortadan giriyor", "neg"]]},
            {"k": "end", "label": "Bitiş", "hint": "cümle bitince mi bitiyor?",
             "opts": [["evet", "Cümle sonu"], ["hayir", "Yarım kalıyor", "neg"]]},
            {"k": "cut", "label": "Kesik kelime", "hint": "başta ya da sonda kelime kesilmiş mi?",
             "opts": [["yok", "Yok"], ["bas", "Başta", "neg"], ["son", "Sonda", "neg"], ["iki", "İkisi de", "neg"]]},
        ],
        "intro": (
            "<div class=\"eyebrow\">Ne yapmalı</div>"
            "<p>Aşağıda __COUNT__ klip var; hangi kanaldan ve hangi sistemden kesildiği gizli. Her klibi bir kez dinle ve üç soruya cevap ver. Cevapların tarayıcıda saklanır; ara verip dönebilirsin.</p>"
            "<ol><li><strong>Başlangıç:</strong> klip bir cümlenin başında mı başlıyor?</li>"
            "<li><strong>Bitiş:</strong> klip cümle bitince mi bitiyor?</li>"
            "<li><strong>Kesik kelime:</strong> ilk ya da son kelimenin bir parçası kesilmiş mi?</li></ol>"
            "<p>Bittiğinde en alttaki <strong>Sonuçları kopyala</strong> düğmesine bas ve çıkan metni sohbete yapıştır.</p>"
        ),
    },
    "music": {
        "q": [
            {"k": "music", "label": "Arka plan müziği", "hint": "konuşmanın altında müzik duyuluyor mu?",
             "opts": [["yok", "Yok"], ["hafif", "Hafif, fark edilir"], ["belirgin", "Belirgin", "neg"], ["baskin", "Baskın", "neg"]]},
            {"k": "train", "label": "Eğitime girsin mi?", "hint": "bu klip bir TTS modelinin öğrenmesini ister misin?",
             "opts": [["evet", "Evet"], ["hayir", "Hayır", "neg"]]},
        ],
        "intro": (
            "<div class=\"eyebrow\">Ne yapmalı</div>"
            "<p>Aşağıda __COUNT__ klip var; kanal ve ölçülen müzik düzeyi gizli. Soru bu kez sınır değil, <strong>arka plan müziği</strong>: konuşmanın altında müzik var mı, varsa ne kadar; ve bu klibi bir TTS modelinin öğrenmesini ister misin?</p>"
            "<p>Kulaklıkla dinle; \"hafif\" fark edilir ama rahatsız etmez demek, \"belirgin\" müzik açıkça duyuluyor, \"baskın\" konuşmayla yarışıyor.</p>"
            "<p>Bittiğinde <strong>Sonuçları kopyala</strong> düğmesine bas ve çıkan metni sohbete yapıştır.</p>"
        ),
    },
}

out = Path(args.out)
out.mkdir(parents=True, exist_ok=True)

if args.score:
    key = json.load((out / "key.json").open(encoding="utf-8"))
    ans = json.load(open(args.score, encoding="utf-8"))["answers"]
    man = {r["id"]: r for r in map(json.loads, open(args.manifest, encoding="utf-8"))}
    tot: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    for n in sorted(ans, key=int):
        a, k = ans[n], key[n]
        r = man[k["id"]]
        c = tot[k["system"]]
        c["n"] += 1
        c["start_bad"] += a.get("start") == "hayir"
        c["end_bad"] += a.get("end") == "hayir"
        c["cut"] += a.get("cut") in ("bas", "son", "iki")
        if a.get("start") == "hayir" or a.get("end") == "hayir" or a.get("cut") in ("bas", "son", "iki") or a.get("note"):
            print(f"{n:>2} {k['system']:7} {k['channel']:12} başı={a.get('start','-'):5} sonu={a.get('end','-'):5} "
                  f"kesik={a.get('cut','-'):4} boşluk={r.get('lead_gap')}/{r.get('trail_gap')} {a.get('note','')[:60]}")
            print(f"     [{r['start']:.2f}–{r['end']:.2f}] {r['flags']} {r['text'][:130]}")
    print()
    for s, c in tot.items():
        print(f"{s}: n={c['n']} kırık başlangıç={c['start_bad']} kırık bitiş={c['end_bad']} kesik kelime={c['cut']}")
    raise SystemExit

rows = [json.loads(l) for l in open(args.manifest, encoding="utf-8")]
# Hat manifestosu (python -m kiraat run çıktısı) 'system' taşımaz: hepsi kiraat;
# lead/trail boşlukları ölçüm adlarıyla gelir.
for r in rows:
    r.setdefault("system", "kiraat")
    r.setdefault("lead_gap", r.get("lead_gap_sec"))
    r.setdefault("trail_gap", r.get("trail_gap_sec"))
rng = random.Random(args.seed)
kiraat = [r for r in rows if r["system"] == "kiraat" and r.get("audio")]
v1 = [r for r in rows if r["system"] == "v1" and r.get("audio")]
if args.prefer_small_gap is not None:
    risky = [r for r in kiraat
             if any(x is not None and x < args.prefer_small_gap for x in (r.get("lead_gap"), r.get("trail_gap")))]
    rest = [r for r in kiraat if r not in risky]
    rng.shuffle(risky); rng.shuffle(rest)
    pick_k = (risky + rest)[: args.n_kiraat]
else:
    pick_k = rng.sample(kiraat, min(args.n_kiraat, len(kiraat)))
pick_v = rng.sample(v1, min(args.n_v1, len(v1))) if v1 else []
sample = pick_k + pick_v
rng.shuffle(sample)

items, key = [], {}
for i, r in enumerate(sample, 1):
    ogg = out / f"{r['id']}.ogg"
    if not ogg.exists():
        subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-y", "-i", r["audio"],
                        "-c:a", "libopus", "-b:a", "40k", str(ogg)], check=True)
    b64 = base64.b64encode(ogg.read_bytes()).decode()
    items.append({"n": i, "dur": round(r["end"] - r["start"], 1), "text": r["text"],
                  "data": "data:audio/ogg;base64," + b64})
    key[str(i)] = {"id": r["id"], "system": r["system"], "channel": r["channel"], "flags": r["flags"],
                   "music_to_speech_db": r.get("music_to_speech_db"), "music_score_audioset": r.get("music_score_audioset")}
json.dump(key, (out / "key.json").open("w", encoding="utf-8"), ensure_ascii=False, indent=1)

template = Path(__file__).with_name("listen_template.html").read_text(encoding="utf-8")
qs = QUESTION_SETS[args.questions]
page = (template.replace("__DATA__", json.dumps(items, ensure_ascii=False))
        .replace("__QUESTIONS__", json.dumps(qs["q"], ensure_ascii=False))
        .replace("__INTRO__", qs["intro"])
        .replace("__AUDIT__", args.audit_name).replace("__COUNT__", str(len(items))))
(out / "index.html").write_text(page, encoding="utf-8")
print(f"{len(items)} klip ({len(pick_k)} kiraat, {len(pick_v)} v1), "
      f"{sum(i['dur'] for i in items)/60:.1f} dk, {len(page)/1e6:.1f} MB → {out/'index.html'}")
