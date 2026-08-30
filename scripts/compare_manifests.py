"""İki manifestoyu (clips.jsonl) sütun sütun karşılaştır.

    python scripts/compare_manifests.py A/manifests/clips.jsonl B/manifests/clips.jsonl

Dağıtıcı (paralel) koşunun sıralı koşuyla özdeş çıktı verdiğini doğrulamak
için: klip kimlikleri aynı mı, her sütun aynı mı; sayısal sütunlarda azami
mutlak fark. Çalışma dizini yolları (`audio`) kök ayrı olduğu için
karşılaştırılmaz, yalnızca dosya adı bakılır; işaret listeleri küme olarak
karşılaştırılır (sıraları aşamaların bitiş sırasına bağlıdır). Fark varsa 1
döner.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def load(path: Path) -> dict[str, dict]:
    rows = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        rows[r["id"]] = r
    return rows


def main(a: str, b: str) -> int:
    ra, rb = load(Path(a)), load(Path(b))
    ok = True
    only_a, only_b = set(ra) - set(rb), set(rb) - set(ra)
    print(f"klip: A {len(ra)}, B {len(rb)}, yalnız A {len(only_a)}, yalnız B {len(only_b)}")
    ok &= not only_a and not only_b
    common = sorted(set(ra) & set(rb))
    cols = sorted({k for i in common for k in (*ra[i], *rb[i])})
    for col in cols:
        n_diff = 0
        max_abs = 0.0
        example = None
        for i in common:
            va, vb = ra[i].get(col), rb[i].get(col)
            if col == "audio":
                va, vb = Path(str(va)).name, Path(str(vb)).name
            elif col in ("flags", "exclusion_reasons", "source_flags") and isinstance(va, list) and isinstance(vb, list):
                va, vb = sorted(va), sorted(vb)     # küme anlamlı; sıra aşamaların bitiş sırasına bağlı
            if va == vb:
                continue
            if isinstance(va, (int, float)) and isinstance(vb, (int, float)) and not isinstance(va, bool):
                d = abs(float(va) - float(vb))
                max_abs = max(max_abs, d)
            n_diff += 1
            example = example or (i, va, vb)
        if n_diff:
            ok = False
            print(f"  {col:28s} fark {n_diff}/{len(common)}"
                  + (f", azami |Δ| {max_abs:.6g}" if max_abs else "")
                  + f"  örn. {example[0]}: {example[1]!r} ≠ {example[2]!r}")
    print("SONUÇ: özdeş" if ok else "SONUÇ: FARK VAR")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
