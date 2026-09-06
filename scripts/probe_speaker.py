"""Konuşmacı gömmeleri: eşiği ve küme sayısını VERİDEN çıkarmak için ölçüm.

v1'in kusuru (`docs/DESIGN.md` madde 8) küme sayısını 64'te sabitlemekti:
iki baskın kanalda tavan doldu ve küme başına ~2.500 klip yığıldı, yani
"konuşmacı" alanı konuşmacıyı göstermez oldu. Burada önce ölçülen şey,
eşiğin nereden geleceği:

  kayıt içi benzerlik     aynı kaydın klipleri arasındaki kosinüs benzerliği
                          — "aynı konuşmacı"nın ölçülmüş üst sınırı
  kayıtlar arası          aynı kanalın iki ayrı kaydı (çoğu kez aynı
                          seslendiren) ve iki ayrı kanalın kayıtları

Eşik bu iki dağılımın ayrıştığı yerden alınır; kümeleme eşikle yapılır,
küme sayısı verilmez.

    python scripts/probe_speaker.py --per-channel 4 --clips 12
"""

from __future__ import annotations

import argparse
import json
import random
import sqlite3
import statistics as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

MODEL = "speechbrain/spkrec-ecapa-voxceleb"
#: Ağırlık revizyonu sabitlenir; `asr.revision` ile aynı gerekçe (yeniden
#: üretilebilirlik). Değişirse bütün gömmeler sessizce değişir.
REVISION = "5c0be3875fda05e81f3c004ed8c7c06be308de1e"


def load_encoder(device: str):
    from speechbrain.inference.speaker import EncoderClassifier

    return EncoderClassifier.from_hparams(
        source=MODEL, savedir="models/ecapa", run_opts={"device": device})


def embed(encoder, paths: list[str], sr: int = 16000, batch: int = 8):
    """Kliplerden L2-normalleştirilmiş gömme; klip başına tek vektör.

    Klipler uzunluğa göre sıralanıp toplu verilir (dolgu israfı en az) ve
    `wav_lens` ile gerçek uzunluk modele bildirilir. Toplu çıkarım tek tek
    çıkarımla BİREBİR aynı değildir — ölçüldü (6 Eyl 2026, 16 klip):
    kosinüs benzerliği en kötü 0,99981, en büyük mutlak bileşen farkı
    0,0043. Fark, dolgunun öznitelik normalizasyonuna sızmasından; küme
    eşiği 0,48 dolayında olduğu için karara etkisi yok, ama gömme
    yayımlanacaksa hangi yolla üretildiği kayda geçmeli.
    """
    import torch
    import torchaudio

    waves = []
    for p in paths:
        wave, file_sr = torchaudio.load(p)
        wave = wave.mean(dim=0)
        if file_sr != sr:
            wave = torchaudio.functional.resample(wave, file_sr, sr)
        waves.append(wave)
    order = sorted(range(len(waves)), key=lambda i: len(waves[i]))
    out: dict[int, "torch.Tensor"] = {}
    for start in range(0, len(order), batch):
        idx = order[start:start + batch]
        chunk = [waves[i] for i in idx]
        n = max(len(w) for w in chunk)
        padded = torch.stack([torch.nn.functional.pad(w, (0, n - len(w))) for w in chunk])
        lens = torch.tensor([len(w) / n for w in chunk])
        with torch.no_grad():
            e = encoder.encode_batch(padded, wav_lens=lens).squeeze(1)
        e = torch.nn.functional.normalize(e, dim=-1).cpu()
        for k, i in enumerate(idx):
            out[i] = e[k]
    return torch.stack([out[i] for i in range(len(waves))]) if out else None


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", default="work/full-1")
    p.add_argument("--per-channel", type=int, default=4,
                   help="kanal başına kaç kayıt (0: hepsi)")
    p.add_argument("--clips", type=int, default=12, help="kayıt başına gömülecek klip")
    p.add_argument("--min-sec", type=float, default=3.0)
    p.add_argument("--device", default="cuda:0")
    p.add_argument("--seed", type=int, default=20260906)
    p.add_argument("--out", default=None)
    args = p.parse_args()

    import torch

    work = Path(args.work_root)
    db = sqlite3.connect(f"file:{work}/db/state.sqlite?mode=ro", uri=True)
    rng = random.Random(args.seed)

    by_channel: dict[str, list[int]] = {}
    for sid, ch in db.execute("select id, channel from sources where error is null"):
        by_channel.setdefault(ch, []).append(sid)
    chosen: list[tuple[str, int]] = []
    for ch in sorted(by_channel):
        rows = sorted(by_channel[ch])
        rng.shuffle(rows)
        chosen += [(ch, sid) for sid in (rows if args.per_channel == 0 else rows[: args.per_channel])]

    encoder = load_encoder(args.device)
    recs = []
    for ch, sid in chosen:
        rows = [r for r in db.execute(
            "select id, audio, duration from clips where source_id=? and duration>=? "
            "and flags_json='[]' order by id", (sid, args.min_sec))]
        if len(rows) < args.clips:
            continue
        picked = [rows[i] for i in sorted(rng.sample(range(len(rows)), args.clips))]
        embs = embed(encoder, [r[1] for r in picked])
        recs.append({"source_id": sid, "channel": ch, "emb": embs})
        print(f"  src{sid:05d} {ch}: {len(picked)} klip gömüldü", flush=True)

    # 1) Kayıt içi benzerlik: aynı kaydın klipleri.
    within = []
    for r in recs:
        e = r["emb"]
        sims = (e @ e.T)[torch.triu(torch.ones(len(e), len(e)), diagonal=1) == 1]
        r["center"] = torch.nn.functional.normalize(e.mean(0), dim=-1)
        r["within_mean"] = float(sims.mean())
        r["within_min"] = float(sims.min())
        within += sims.tolist()

    # 2) Kayıtlar arası: aynı kanal / farklı kanal.
    centers = torch.stack([r["center"] for r in recs])
    sim = centers @ centers.T
    same_channel, other_channel = [], []
    for i in range(len(recs)):
        for j in range(i + 1, len(recs)):
            (same_channel if recs[i]["channel"] == recs[j]["channel"] else other_channel).append(
                float(sim[i, j]))

    def q(v, p_):
        v = sorted(v)
        return round(v[int(p_ * (len(v) - 1))], 4)

    print(f"\nkayıt: {len(recs)} | kanal: {len({r['channel'] for r in recs})}")
    print(f"{'dağılım':22} {'n':>7} {'p05':>8} {'p50':>8} {'p95':>8}")
    for name, v in (("kayıt içi (klip-klip)", within),
                    ("aynı kanal (kayıt-kayıt)", same_channel),
                    ("farklı kanal", other_channel)):
        if not v:
            print(f"{name:22} {'—':>7}  (bu örneklemde çift yok)")
            continue
        print(f"{name:22} {len(v):>7} {q(v,0.05):>8} {q(v,0.5):>8} {q(v,0.95):>8}")

    out = {
        "model": MODEL, "revision": REVISION, "kayıt": len(recs),
        "kayıt_içi": {"p05": q(within, .05), "p50": q(within, .5), "p95": q(within, .95)},
        "aynı_kanal": {"p05": q(same_channel, .05), "p50": q(same_channel, .5),
                       "p95": q(same_channel, .95)} if same_channel else None,
        "farklı_kanal": {"p05": q(other_channel, .05), "p50": q(other_channel, .5),
                         "p95": q(other_channel, .95)},
        "kayıt_başına": [{"source_id": r["source_id"], "channel": r["channel"],
                          "within_mean": round(r["within_mean"], 4),
                          "within_min": round(r["within_min"], 4)} for r in recs],
    }
    dst = Path(args.out or (work / "ablation" / "speaker_probe.json"))
    dst.parent.mkdir(parents=True, exist_ok=True)
    torch.save({"centers": centers, "meta": [(r["source_id"], r["channel"]) for r in recs]},
               dst.with_suffix(".pt"))
    dst.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nölçüm: {dst} | merkezler: {dst.with_suffix('.pt')}")


if __name__ == "__main__":
    main()
