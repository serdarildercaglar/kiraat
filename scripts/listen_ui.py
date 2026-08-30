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
parser.add_argument("--questions", choices=["boundary", "music", "clipping", "transcript"], default="boundary")
parser.add_argument("--ids-file", default=None,
                    help="klipleri örneklemek yerine bu dosyadaki kimlikleri kullan "
                         "(work/<koşu>/listen-*.txt biçimi: boşlukla ayrılmış kimlikler)")
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
    "transcript": {
        "q": [
            {"k": "text", "label": "Metin", "hint": "yazılı metin, duyduğunla birebir aynı mı?",
             "opts": [["dogru", "Birebir doğru"], ["kucuk", "Küçük hata (ek, harf, noktalama)"],
                      ["kelime", "Bir kelime yanlış", "neg"], ["cok", "Birden çok kelime yanlış", "neg"]]},
            {"k": "train", "label": "Eğitime girsin mi?", "hint": "bu klip bir TTS modelinin öğrenmesini ister misin?",
             "opts": [["evet", "Evet"], ["hayir", "Hayır", "neg"]]},
        ],
        "intro": (
            "<div class=\"eyebrow\">Ne yapmalı</div>"
            "<p>Aşağıda __COUNT__ klip var; kanal ve ölçülen güven değeri gizli. Bu turda soru ses kalitesi değil, "
            "<strong>metnin doğruluğu</strong>: klibin altındaki yazı, duyduğun sözle birebir aynı mı?</p>"
            "<p>Önce oku, sonra dinle. Özel isimler ve nadir sözcükler önemli — asıl sınanan şey bunlar. "
            "&quot;Küçük hata&quot; anlamı bozmayan bir ek ya da harf farkı; &quot;bir kelime yanlış&quot; sözcüğün "
            "yerine başka bir sözcük yazılmış demek.</p>"
            "<p>Bittiğinde <strong>Sonuçları kopyala</strong> düğmesine bas ve çıkan metni sohbete yapıştır.</p>"
        ),
    },
    "clipping": {
        "q": [
            {"k": "clip", "label": "Kırpılma", "hint": "tepe noktalarında sertlik/çatırtı duyuluyor mu?",
             "opts": [["yok", "Yok"], ["hafif", "Hafif, fark edilir"], ["belirgin", "Belirgin", "neg"],
                      ["baskin", "Baskın, rahatsız edici", "neg"]]},
            {"k": "train", "label": "Eğitime girsin mi?", "hint": "bu klip bir TTS modelinin öğrenmesini ister misin?",
             "opts": [["evet", "Evet"], ["hayir", "Hayır", "neg"]]},
        ],
        "intro": (
            "<div class=\"eyebrow\">Ne yapmalı</div>"
            "<p>Aşağıda __COUNT__ klip var; kanal ve ölçülen kırpılma değeri gizli. Soru <strong>dijital kırpılma</strong>: "
            "sesin en yüksek noktalarında sertlik, çatırtı, boğuklaşma ya da &quot;bozuk hoparlör&quot; hissi var mı?</p>"
            "<p><strong>Gür ses kırpılma değildir.</strong> Bir kanal sadece yüksek seviyede kaydedilmiş olabilir; "
            "bu tek başına kusur sayılmaz. Aranan şey, dalga biçiminin tavana dayanmasından doğan bozulma.</p>"
            "<p>Kulaklıkla dinle. &quot;Hafif&quot; dikkat edince fark edilir ama rahatsız etmez; &quot;belirgin&quot; açıkça duyulur; "
            "&quot;baskın&quot; dinlemeyi rahatsız eder.</p>"
            "<p>Bittiğinde <strong>Sonuçları kopyala</strong> düğmesine bas ve çıkan metni sohbete yapıştır.</p>"
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

    if args.questions == "transcript":
        satir = []
        for n in sorted(ans, key=int):
            k, a = key[n], ans[n]
            satir.append((float(k["word_confidence"]), a.get("text", "-"), a.get("train", "-"),
                          k["channel"], n, a.get("note", ""), k.get("text", "")))
        satir.sort()
        print(f"{'word_conf':>10s} {'metin':>8s} {'eğitim':>7s}  kanal")
        for wc, tx, tr, ch, n, note, txt in satir:
            print(f"{wc:10.3f} {tx:>8s} {tr:>7s}  {ch:22s} {txt[:60]}" + (f"  — {note[:40]}" if note else ""))
        hatali = {"kelime", "cok"}
        adaylar = sorted({round(wc, 3) for wc, *_ in satir} | {0.6})
        print(f"\n{'eşik':>7s} {'kaçan':>6s} {'boşuna':>7s} {'hata':>5s}   (kaçan: metin yanlış ama geçiyor)")
        en_iyi = None
        for e in adaylar:
            kacan = sum(1 for wc, tx, *_ in satir if tx in hatali and wc >= e)
            bosuna = sum(1 for wc, tx, *_ in satir if tx not in hatali and wc < e)
            h = kacan + bosuna
            print(f"{e:7.3f} {kacan:6d} {bosuna:7d} {h:5d}" + ("   ← mevcut kural" if abs(e - 0.6) < 1e-9 else ""))
            if en_iyi is None or h < en_iyi[1]:
                en_iyi = (e, h)
        print(f"\nen az hatalı eşik: {en_iyi[0]:.3f} ({en_iyi[1]} hata / {len(satir)} klip)")
        print(f"eğitime girmesin denen: {sum(1 for s in satir if s[2] == 'hayir')}/{len(satir)}")
        raise SystemExit

    if args.questions == "clipping":
        # Müzik eşiği kararındaki yöntemin aynısı: cevapları ölçüme göre
        # sırala, her aday eşikte hata say (duyulan ama geçen + duyulmayan
        # ama elenen), en az hatalıyı bildir.
        satir = []
        for n in sorted(ans, key=int):
            k, a = key[n], ans[n]
            satir.append((float(k["clip_ratio"]), a.get("clip", "-"), a.get("train", "-"),
                          k["channel"], n, a.get("note", "")))
        satir.sort()
        print(f"{'clip_ratio':>11s} {'kırpılma':>10s} {'eğitim':>7s}  kanal")
        for cr, cl, tr, ch, n, note in satir:
            print(f"{cr:11.5f} {cl:>10s} {tr:>7s}  {ch}" + (f"   — {note[:50]}" if note else ""))
        duyulan = {"belirgin", "baskin"}
        adaylar = sorted({round(cr, 5) for cr, *_ in satir} | {0.002})
        print(f"\n{'eşik':>9s} {'kaçan':>6s} {'boşuna':>7s} {'hata':>5s}   (kaçan: duyuluyor ama geçiyor)")
        en_iyi = None
        for e in adaylar:
            kacan = sum(1 for cr, cl, *_ in satir if cl in duyulan and cr <= e)
            bosuna = sum(1 for cr, cl, *_ in satir if cl not in duyulan and cr > e)
            h = kacan + bosuna
            print(f"{e:9.5f} {kacan:6d} {bosuna:7d} {h:5d}" + ("   ← mevcut kural" if abs(e - 0.002) < 1e-9 else ""))
            if en_iyi is None or h < en_iyi[1]:
                en_iyi = (e, h)
        print(f"\nen az hatalı eşik: {en_iyi[0]:.5f} ({en_iyi[1]} hata / {len(satir)} klip)")
        egitim_hayir = [s for s in satir if s[2] == "hayir"]
        print(f"eğitime girmesin denen: {len(egitim_hayir)}/{len(satir)}"
              + (f", clip_ratio aralığı {min(s[0] for s in egitim_hayir):.5f}–{max(s[0] for s in egitim_hayir):.5f}"
                 if egitim_hayir else ""))
        raise SystemExit

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
if args.ids_file:
    # Hazır liste: bantlara göre dengelenmiş bir seçim dışarıda kurulmuş olur
    # (bkz. defter). Sıra yine karıştırılır ki bant sırası ele vermesin.
    want = Path(args.ids_file).read_text(encoding="utf-8").split()
    by_id = {r["id"]: r for r in rows}
    eksik = [i for i in want if i not in by_id]
    if eksik:
        raise SystemExit(f"manifestoda olmayan kimlik: {eksik[:5]}")
    rows = [by_id[i] for i in want]
    args.n_kiraat, args.n_v1 = len(rows), 0
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
                   "music_to_speech_db": r.get("music_to_speech_db"), "music_score_audioset": r.get("music_score_audioset"),
                   "clip_ratio": r.get("clip_ratio"), "peak_dbfs": r.get("peak_dbfs"), "rms_dbfs": r.get("rms_dbfs"),
                   "word_confidence": r.get("word_confidence"), "text": r.get("text"),
                   "recommended": r.get("recommended")}
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
