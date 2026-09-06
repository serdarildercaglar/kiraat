"""Yineleme kararının gözle denetlenebilir dökümü.

Kullanıcının kuralı (6 Eyl 2026): aynı metin farklı seslendirmeyle
tekrar ediyorsa YİNELEME DEĞİLDİR — prozodi çeşitliliği için değerlidir.
Yineleme, metnin aynı VE ölçülen bütün değerlerin aynı olmasıdır.

Bu betik manifesti okur ve şu anki (metin, kanal) anahtarının ne
işaretlediğini, kullanıcının kuralının ne işaretleyeceğini yan yana
koyar; ayrıca ikisinin ayrıştığı yerlerden örnek basar.

    python scripts/probe_dedupe.py work/full-1/manifests/clips.jsonl
"""

from __future__ import annotations

import collections
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from kiraat.dedupe import dedupe_key  # noqa: E402

#: Ölçüm olmayan alanlar; geri kalan her anahtar "ölçtüğümüz değer"dir.
NOT_METRIC = {
    "id", "audio", "channel", "source_id", "source_path", "source_sample_rate",
    "source_flags", "start", "end", "text_raw", "text", "text_spoken", "flags",
    "duplicate_of", "recommended", "exclusion_reasons", "policy_version",
}


def fingerprint(row: dict) -> str:
    """Ölçüm alanlarının sıralı JSON dökümü; değer sözlük de olabilir
    (`music_stem_db`), o yüzden demet değil dize."""
    return json.dumps({k: v for k, v in row.items() if k not in NOT_METRIC},
                      sort_keys=True, ensure_ascii=False)


def main(path: str) -> None:
    by_text_channel: dict[tuple, list[dict]] = collections.defaultdict(list)
    n = 0
    for line in open(path, encoding="utf-8"):
        row = json.loads(line)
        key = dedupe_key(row.get("text") or "")
        if not key:
            continue
        n += 1
        by_text_channel[(key, row["channel"])].append(
            {"id": row["id"], "dup": bool(row["duplicate_of"]), "fp": fingerprint(row),
             "dur": row["duration"], "text": row["text"]})

    simdi = ayni_olcum = farkli_olcum = 0
    ornek_farkli: list[tuple] = []
    for (key, ch), rows in by_text_channel.items():
        if len(rows) == 1:
            continue
        simdi += sum(1 for r in rows if r["dup"])
        groups = collections.defaultdict(list)
        for r in rows:
            groups[r["fp"]].append(r)
        for fp, g in groups.items():
            if len(g) > 1:
                ayni_olcum += len(g) - 1
        farkli = len(rows) - len(groups)
        farkli_olcum += len(rows) - 1 - (len(rows) - len(groups))
        if len(groups) > 1 and len(ornek_farkli) < 8:
            ornek_farkli.append((ch, g[0]["text"], [round(r["dur"], 2) for r in rows]))

    print(f"klip (metni olan): {n}")
    print(f"şimdiki kural (metin+kanal) yineleme sayar: {simdi}")
    print(f"metin VE bütün ölçümler aynı (gerçek kopya): {ayni_olcum}")
    print(f"metin aynı, ölçüm farklı (yeniden okuma, TUTULMALI): {simdi - ayni_olcum}")
    print("\nölçümü ayrışan gruplardan örnekler (kanal | süreler | metin):")
    for ch, text, durs in ornek_farkli:
        print(f"  {ch} | {durs} | {text[:70]}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "work/full-1/manifests/clips.jsonl")
