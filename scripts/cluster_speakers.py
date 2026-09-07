"""Konuşmacı kümeleme: eşik veriden, küme sayısı verilmeden.

v1 küme sayısını 64'te sabitledi ve tavan doldu (`docs/DESIGN.md` madde 8).
Burada küme sayısı verilmez; birleştirme eşiği ölçülen iki dağılımdan
çıkarılır ve kümeler o eşikle oluşur:

  pozitif   aynı kaydın klibi ile o kaydın merkezi (aynı konuşmacı — tek
            seslendirenli kayıt varsayımı, kayıt içi tutarlılıkla sınanır)
  negatif   iki AYRI kanalın kayıt merkezleri (neredeyse kesin ayrı kişi)

Eşik, iki dağılımın eşit hata noktasıdır (EER). Kümeleme, kosinüs
uzaklığında ortalama bağlantılı birleştirmedir; her kayıt için kendi
kümesine ve en yakın diğer kümeye uzaklık (kenar payı) raporlanır.

    python scripts/cluster_speakers.py --centers work/full-1/ablation/speaker_probe.pt
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def eer_threshold(pos: list[float], neg: list[float]) -> tuple[float, float]:
    """Pozitif/negatif benzerliklerin eşit hata noktası ve oradaki hata."""
    cand = sorted(set(round(x, 3) for x in pos + neg))
    best, best_gap, best_err = 0.5, 9e9, 1.0
    for t in cand:
        fn = sum(1 for x in pos if x < t) / max(1, len(pos))    # aynı kişi, ayrı sayıldı
        fp = sum(1 for x in neg if x >= t) / max(1, len(neg))   # ayrı kişi, aynı sayıldı
        if abs(fn - fp) < best_gap:
            best, best_gap, best_err = t, abs(fn - fp), (fn + fp) / 2
    return best, best_err


def cluster(centers, threshold: float) -> list[int]:
    """Ortalama bağlantılı birleştirme; küme sayısı verilmez, eşik verilir."""
    import numpy as np
    from sklearn.cluster import AgglomerativeClustering

    x = centers.numpy() if hasattr(centers, "numpy") else np.asarray(centers)
    model = AgglomerativeClustering(n_clusters=None, metric="cosine", linkage="average",
                                    distance_threshold=1.0 - threshold)
    return model.fit_predict(x).tolist()


def margins(centers, labels: list[int]) -> list[float]:
    """Her kayıt için: kendi küme merkezine benzerlik − en yakın diğer kümeye."""
    import numpy as np

    x = centers.numpy() if hasattr(centers, "numpy") else np.asarray(centers)
    by = defaultdict(list)
    for i, k in enumerate(labels):
        by[k].append(i)
    cent = {k: x[idx].mean(0) / max(1e-9, np.linalg.norm(x[idx].mean(0))) for k, idx in by.items()}
    out = []
    for i, k in enumerate(labels):
        own = float(x[i] @ cent[k])
        others = [float(x[i] @ c) for kk, c in cent.items() if kk != k]
        out.append(round(own - max(others), 4) if others else None)
    return out


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--speaker-dir", default=None,
                   help="`speaker` aşamasının çıktıları (work/<koşu>/speaker); verilirse "
                        "merkezler ve kayıt içi tutarlılık oradan okunur")
    p.add_argument("--db", default="work/full-1/db/state.sqlite")
    p.add_argument("--centers", default="work/full-1/ablation/speaker_probe.pt")
    p.add_argument("--probe", default="work/full-1/ablation/speaker_probe.json")
    p.add_argument("--threshold", type=float, default=None, help="verilmezse EER'den")
    p.add_argument("--out", default=None)
    args = p.parse_args()

    import numpy as np
    import torch

    if args.speaker_dir:
        # `speaker` aşamasının çıktısı: kayıt başına bir .npz (merkez + klip
        # gömmeleri) ve veritabanında kanal + kayıt içi tutarlılık.
        import sqlite3
        db = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
        info = {}
        for sid, ch, mj in db.execute("select id, channel, meta_json from sources where error is null"):
            m = json.loads(mj)
            if m.get("speaker_embedding"):
                info[sid] = (ch, m.get("speaker_consistency"), m["speaker_embedding"])
        meta, cent, pos = [], [], []
        for sid in sorted(info):
            ch, cons, path = info[sid]
            z = np.load(path)
            meta.append((sid, ch))
            cent.append(z["center"])
            if cons is not None:
                pos.append(cons)
        centers = torch.from_numpy(np.stack(cent))
    else:
        blob = torch.load(args.centers)
        centers, meta = blob["centers"], blob["meta"]
        probe = json.loads(Path(args.probe).read_text(encoding="utf-8"))
        # Pozitif/negatif dağılımlar merkezlerden kurulur: pozitif = kayıt içi
        # klip-merkez, negatif = farklı kanal merkez-merkez.
        pos = [r["within_mean"] for r in probe["kayıt_başına"]]
    sim = (centers @ centers.T).numpy()
    # Negatifler: farklı kanalların kayıtları. Çift sayısı kayıt sayısının
    # karesiyle büyüdüğü için 200 binden fazlaysa tohumlu örneklenir.
    import random
    rng = random.Random(20260907)
    pairs = [(i, j) for i in range(len(meta)) for j in range(i + 1, len(meta))
             if meta[i][1] != meta[j][1]]
    if len(pairs) > 200000:
        pairs = rng.sample(pairs, 200000)
    neg = [float(sim[i, j]) for i, j in pairs]
    thr, err = (args.threshold, None) if args.threshold else eer_threshold(pos, neg)

    labels = cluster(centers, thr)
    marg = margins(centers, labels)
    sizes = Counter(labels)
    by_cluster = defaultdict(set)
    for (sid, ch), k in zip(meta, labels):
        by_cluster[k].add(ch)
    multi_channel = {k: sorted(v) for k, v in by_cluster.items() if len(v) > 1}
    per_channel_clusters = defaultdict(set)
    for (sid, ch), k in zip(meta, labels):
        per_channel_clusters[ch].add(k)

    print(f"kayıt: {len(meta)} | eşik: {thr:.3f}" + (f" (EER {err:.3%})" if err is not None else ""))
    print(f"küme: {len(sizes)} | en büyük {sizes.most_common(1)[0][1]} kayıt | "
          f"tek kayıtlık küme {sum(1 for v in sizes.values() if v == 1)}")
    print(f"birden çok kanala yayılan küme: {len(multi_channel)}")
    print(f"birden çok kümesi olan kanal: {sum(1 for v in per_channel_clusters.values() if len(v) > 1)}"
          f" / {len(per_channel_clusters)}")
    mv = sorted(m for m in marg if m is not None)
    if mv:
        print(f"kenar payı: p05 {mv[int(.05*len(mv))]:.3f} | medyan {mv[len(mv)//2]:.3f} | "
              f"negatif (yanlış kümede olabilir) {sum(1 for m in mv if m < 0)}")

    out = {"eşik": thr, "eer": err, "küme": len(sizes),
           "küme_boyutları": dict(Counter(sizes.values())),
           "birden_çok_kanala_yayılan_küme": multi_channel,
           "kanal_başına_küme": {k: len(v) for k, v in sorted(per_channel_clusters.items())},
           "kayıtlar": [{"source_id": sid, "channel": ch, "speaker_cluster": int(k),
                         "margin": m} for (sid, ch), k, m in zip(meta, labels, marg)]}
    dst = Path(args.out or Path(args.centers).with_name("speaker_clusters.json"))
    dst.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"çıktı: {dst}")


if __name__ == "__main__":
    main()
