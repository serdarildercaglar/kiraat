#!/usr/bin/env python
"""Cümle ortasından kesilmiş klip oranı — iki hattı yan yana ölçer.

Değişmez şu: kesim cümle sınırındadır. Bu betik onu doğrudan sınar ve
sessizlikte kesen bir hattın aynı ham kayıtlarda ne ürettiğiyle karşılaştırır.

İki ölçüm, ikisi de `kiraat.text.turkish` içindeki ortak yordamlarla:

* **baş kırığı** — metin küçük harfle başlıyor (`is_lower_start`), yani klip
  cümlenin ortasından giriyor. Rakam ya da tırnakla başlayanlar kırık
  sayılmaz.
* **son kırığı** — metin cümle sonu noktalamasıyla bitmiyor
  (`has_sentence_end`), yani klip cümle bitmeden kesiliyor.

Karşılaştırılan hat, sessizlikte kesen v1'in `state-v2.sqlite` deposudur;
veri bu depoya kopyalanmaz, yalnız okunur (`--v1` ile yol verilir).

Kullanım:

    python scripts/probe_sentence_cuts.py \
        --kiraat work/full-1/db/state.sqlite \
        --v1 ../voxcpm/work/db/state-v2.sqlite \
        --examples 5
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from kiraat.config import Config  # noqa: E402
from kiraat.scoring import Policy  # noqa: E402
from kiraat.text.turkish import has_sentence_end, is_lower_start  # noqa: E402


@dataclass
class Tally:
    """Bir küme için sayaçlar; saat cinsinden de tutulur."""

    ad: str
    n: int = 0
    saat: float = 0.0
    bas_kirik: int = 0
    bas_kirik_saat: float = 0.0
    son_kirik: int = 0
    bos: int = 0
    ornekler: list[str] = field(default_factory=list)

    def ekle(self, text: str | None, duration: float, ornek_sayisi: int, kimlik: str) -> None:
        self.n += 1
        self.saat += duration / 3600.0
        if not text or not text.strip():
            self.bos += 1
            return
        if is_lower_start(text):
            self.bas_kirik += 1
            self.bas_kirik_saat += duration / 3600.0
            if len(self.ornekler) < ornek_sayisi:
                self.ornekler.append(f"{kimlik}: {text[:90]}")
        if not has_sentence_end(text):
            self.son_kirik += 1

    def satir(self) -> str:
        if not self.n:
            return f"{self.ad:<28} {'—':>12}"
        return (
            f"{self.ad:<28} {self.n:>11,} {self.saat:>9,.1f} "
            f"{self.bas_kirik:>11,} {100 * self.bas_kirik / self.n:>7.2f} "
            f"{self.son_kirik:>11,} {100 * self.son_kirik / self.n:>7.2f}"
        )


BASLIK = (
    f"{'küme':<28} {'klip':>11} {'saat':>9} "
    f"{'baş kırığı':>11} {'%':>7} {'son kırığı':>11} {'%':>7}"
)


class Dokum:
    """Kırık kliplerin tam dökümü; JSONL, satır başına bir klip.

    Sayı tabloyu, döküm gözü besler: hangi cümlenin nerede kesildiği ancak
    metne bakılarak anlaşılır.
    """

    def __init__(self, yol: Path | None) -> None:
        self.yol = yol
        self.fh = yol.open("w", encoding="utf-8") if yol else None
        self.n = 0

    def yaz(self, text: str | None, **alanlar: object) -> None:
        if self.fh is None or not text or not text.strip():
            return
        bas, son = is_lower_start(text), not has_sentence_end(text)
        if not (bas or son):
            return
        kirik = "iki_uc" if bas and son else ("bas" if bas else "son")
        json.dump({"kirik": kirik, "text": text, **alanlar}, self.fh, ensure_ascii=False)
        self.fh.write("\n")
        self.n += 1

    def kapat(self) -> None:
        if self.fh:
            self.fh.close()


def olc_v1(db: Path, ornek: int, dokum: Dokum) -> list[Tally]:
    """v1 deposu: metin `stage_results`'ta, karar `clips.decision`'da."""
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    kumeler = {
        "ACCEPT": Tally("v1 temiz havuz (ACCEPT)"),
        "REVIEW": Tally("v1 inceleme havuzu (REVIEW)"),
        "REJECT": Tally("v1 elenen (REJECT, yayımlanmadı)"),
    }
    yayim = Tally("v1 yayımlanan havuz")
    tumu = Tally("v1 tüm klipler")
    sorgu = """
        SELECT c.id, c.channel, c.decision, c.start_sec, c.duration, r.metrics_json
        FROM stage_results r JOIN clips c ON c.id = r.row_id
        WHERE r.level = 'clip' AND r.stage = 'text'
    """
    for kimlik, kanal, karar, start, duration, mj in con.execute(sorgu):
        text = json.loads(mj).get("text")
        etiket = f"v1-{kimlik}"
        dokum.yaz(
            text,
            korpus="v1",
            id=kimlik,
            kanal=kanal,
            karar=karar,
            start=round(start, 2),
            duration=round(duration, 2),
            yayimlandi=karar in ("ACCEPT", "REVIEW"),
        )
        tumu.ekle(text, duration, ornek, etiket)
        if karar in kumeler:
            kumeler[karar].ekle(text, duration, ornek, etiket)
        if karar in ("ACCEPT", "REVIEW"):
            yayim.ekle(text, duration, ornek, etiket)
    con.close()
    return [tumu, yayim, kumeler["ACCEPT"], kumeler["REVIEW"], kumeler["REJECT"]]


def olc_kiraat(db: Path, policy: Policy, ornek: int, dokum: Dokum) -> list[Tally]:
    """kiraat deposu: metin ve işaretler `clips` satırında; öneri politikadan."""
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    tumu = Tally("kiraat tüm korpus")
    onerilen = Tally("kiraat önerilen alt küme")
    disarida = Tally("kiraat politika dışı")
    sorgu = "SELECT id, channel, start, duration, text, flags_json, metrics_json FROM clips"
    for kimlik, kanal, start, duration, text, fj, mj in con.execute(sorgu):
        tumu.ekle(text, duration, ornek, kimlik)
        flags = json.loads(fj)
        onerilir, gerekceler = policy.evaluate(json.loads(mj), flags)
        hedef = disarida if gerekceler else onerilen
        hedef.ekle(text, duration, ornek, kimlik)
        dokum.yaz(
            text,
            korpus="kiraat",
            id=kimlik,
            kanal=kanal,
            isaretler=flags,
            start=round(start, 2),
            duration=round(duration, 2),
            onerilir=onerilir,
            gerekceler=list(gerekceler),
        )
    con.close()
    return [tumu, onerilen, disarida]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--kiraat", type=Path, default=Path("work/full-1/db/state.sqlite"))
    ap.add_argument("--v1", type=Path, default=None, help="v1 state-v2.sqlite yolu")
    ap.add_argument("--config", type=Path, default=Path("configs/default.yaml"))
    ap.add_argument("--examples", type=int, default=5)
    ap.add_argument(
        "--dump",
        type=Path,
        default=None,
        help="kırık kliplerin tam dökümünü bu dizine JSONL olarak yaz",
    )
    args = ap.parse_args()

    cfg = Config.load(args.config)
    policy = Policy.from_dict(cfg.data["recommended_subset"])
    if args.dump:
        args.dump.mkdir(parents=True, exist_ok=True)

    satirlar: list[Tally] = []
    dokumler: list[Dokum] = []
    if args.v1:
        if not args.v1.exists():
            print(f"v1 deposu bulunamadi: {args.v1}", file=sys.stderr)
            return 2
        d = Dokum(args.dump / "v1-kirik.jsonl" if args.dump else None)
        satirlar += olc_v1(args.v1, args.examples, d)
        d.kapat()
        dokumler.append(d)
    d = Dokum(args.dump / "kiraat-kirik.jsonl" if args.dump else None)
    satirlar += olc_kiraat(args.kiraat, policy, args.examples, d)
    d.kapat()
    dokumler.append(d)

    print(f"politika surumu: {policy.version}")
    print()
    print(BASLIK)
    print("-" * len(BASLIK))
    for t in satirlar:
        print(t.satir())

    bos = [t for t in satirlar if t.bos]
    if bos:
        print()
        for t in bos:
            print(f"bos metin: {t.ad} -> {t.bos:,}")

    for d in dokumler:
        if d.yol:
            print(f"\ndokum: {d.yol} -> {d.n:,} kirik klip")

    print()
    for t in satirlar:
        if t.ornekler:
            print(f"--- {t.ad}: bas kirigi ornekleri")
            for o in t.ornekler:
                print(f"    {o}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
