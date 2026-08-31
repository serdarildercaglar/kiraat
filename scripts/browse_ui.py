"""Denetim tezgâhı: hat çalışırken klipleri ölçüte göre süz, dinle, karar ver.

    python scripts/browse_ui.py --work work/sample-25 [--port 8765]
    python scripts/browse_ui.py --work work/sample-25 --dump-notes      # kanal × kusur tablosu
    python scripts/browse_ui.py --work work/sample-25 --csv bulgular.csv

Tarayıcıda http://127.0.0.1:8765 açılır. İki görünüm:

  Tezgâh    Solda ölçüt kurucu: her satır bir sütuna koşul koyar ve satırlar VE
            ile birleşir. Süzülebilen sütun kümesi depodan okunur — klip
            alanları, metin alanları, bütün ölçümler (iç içe olanlar
            `music_stem_db.vocals` gibi açılır), manifestten gelen öneri ve
            dışlanma sebepleri, manuel karar ve kusur etiketleri. Ortada
            klipler üç kipte gelir: tohumlu rastgele örnek, herhangi bir
            sütuna göre sıralı liste, ya da kanal başına kalıcı deste. Sağda
            karne (havuzun kaçına karar verilmiş, kaçı temiz çıkmış) ve eşik
            yardımcısı (seçili ölçümün havuzdaki dağılımı; kovaya tıklamak
            koşul kurar). Altta klavyeyle karar çubuğu; kör mod metni ve
            ölçümleri gizler, karar yalnızca sesle verilir.
  Bulgular  Kanal × karar/etiket tablosu, kusurlu kliplerin listesi, CSV.

Durum deposu salt-okunur açılır (WAL; hat yazarken okunabilir). Manifest
üretilmişse `recommended` / `exclusion_reasons` kliplerin üstüne bindirilir.
Notlar `<work>/manual-notes.jsonl` dosyasına eklenir; klip başına son not
geçerlidir. Desteler `<work>/review-decks.json`, kayıtlı ölçütler
`<work>/review-filters.json` dosyasında kalıcıdır. "bağlam" düğmesi kaynağın
24 kHz wav'ından klibin 2 s öncesinden 2 s sonrasına kadar çalar (kesim
sınırı denetimi).
"""

from __future__ import annotations

import argparse
import collections
import csv
import io
import json
import mimetypes
import os
import random
import re
import sqlite3
import sys
import time
import urllib.parse
import zlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from kiraat.text.turkish import lower  # noqa: E402

STAGES = ["prepare", "asr", "align", "boilerplate", "segment", "clip_qc", "music", "dnsmos", "export"]
VERDICTS = ["temiz", "kusurlu", "kullanilmaz"]
#: Kusur etiketleri: anahtar, sayfadaki ad, klavye harfi. Sıra sayfadaki sıradır.
TAGS = [
    ("bas_kesik", "baş kesik", "b"),
    ("son_kesik", "son kesik", "e"),
    ("metin_hatali", "metin hatalı", "t"),
    ("okunus_hatali", "okunuş hatalı", "o"),
    ("muzik", "müzik", "m"),
    ("gurultu", "gürültü/yankı", "g"),
    ("yapay_ses", "yapay ses", "y"),
    ("kunye", "künye/anons", "a"),
    ("baska_konusmaci", "başka konuşmacı", "s"),
    ("diger", "diğer", "d"),
]
TAG_KEYS = [t[0] for t in TAGS]

parser = argparse.ArgumentParser()
parser.add_argument("--work", default="work", help="koşu dizini (db/state.sqlite bunun altında)")
parser.add_argument("--host", default="127.0.0.1")
parser.add_argument("--port", type=int, default=8765)
parser.add_argument("--dump-notes", action="store_true", help="sunucu yerine bulgu tablosunu bas ve çık")
parser.add_argument("--csv", default=None, help="bulgu tablosunu bu CSV dosyasına yaz ve çık")
args = parser.parse_args()

WORK = Path(args.work)
if not WORK.is_absolute():
    WORK = ROOT / WORK
DB = WORK / "db" / "state.sqlite"
MANIFEST = WORK / "manifests" / "clips.jsonl"
NOTES = WORK / "manual-notes.jsonl"
DECKS = WORK / "review-decks.json"
PRESETS = WORK / "review-filters.json"
TEMPLATE = ROOT / "scripts" / "review_template.html"


def connect() -> sqlite3.Connection:
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True, timeout=5)
    con.row_factory = sqlite3.Row
    return con


def resolve(p: str) -> Path:
    q = Path(p)
    return q if q.is_absolute() else ROOT / q


# ------------------------------------------------------------------ notlar
def load_notes() -> dict[str, dict]:
    """Klip başına son not. Eski kayıtlarda `tags` yok, `verdict` iyi/kusur/kotu
    olabilir; yeni adlara çevrilir."""
    out: dict[str, dict] = {}
    if NOTES.exists():
        for line in NOTES.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                r.setdefault("tags", [])
                r["verdict"] = {"iyi": "temiz", "kusur": "kusurlu", "kotu": "kullanilmaz"}.get(r.get("verdict"), r.get("verdict", ""))
                out[r["clip_id"]] = r
    return out


def append_note(body: dict) -> dict:
    tags = [t for t in (body.get("tags") or []) if t in TAG_KEYS]
    verdict = str(body.get("verdict", "") or "")
    if verdict not in ("", *VERDICTS):
        raise ValueError(f"bilinmeyen karar: {verdict}")
    rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "clip_id": str(body["clip_id"]),
           "channel": str(body.get("channel", "")), "verdict": verdict, "tags": tags,
           "note": str(body.get("note", "")).strip()}
    with NOTES.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec


# ---------------------------------------------------------------- manifest
_manifest_cache: tuple[float, dict] | None = None


def load_manifest() -> dict[str, dict]:
    global _manifest_cache
    if not MANIFEST.exists():
        return {}
    mtime = MANIFEST.stat().st_mtime
    if _manifest_cache and _manifest_cache[0] == mtime:
        return _manifest_cache[1]
    rows: dict[str, dict] = {}
    with MANIFEST.open(encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                r = json.loads(line)
                rows[r["id"]] = {"recommended": r.get("recommended"),
                                 "exclusion_reasons": r.get("exclusion_reasons", []),
                                 "policy_version": r.get("policy_version"),
                                 "duplicate_of": r.get("duplicate_of")}
    _manifest_cache = (mtime, rows)
    return rows


def log_tail(n: int = 15) -> list[str]:
    logs = sorted(WORK.glob("*.log"), key=lambda p: p.stat().st_mtime)
    if not logs:
        return []
    lines = logs[-1].read_text(encoding="utf-8", errors="replace").splitlines()
    keep = [ln for ln in lines if re.match(r"^\d\d:\d\d:\d\d (INFO|WARNING|ERROR)", ln)]
    return keep[-n:]


# ------------------------------------------------------------------- özet
def summary() -> dict:
    con = connect()
    try:
        sources = []
        done_src = collections.defaultdict(set)
        for r in con.execute("select key, stage from done where kind='source'"):
            done_src[str(r["key"])].add(r["stage"])
        done_channel = collections.defaultdict(set)   # boilerplate kanal bazlı 'bitti' yazar
        for r in con.execute("select key, stage from done where kind='channel'"):
            done_channel[r["stage"]].add(str(r["key"]))
        clip_stage = {r["stage"]: r["n"] for r in
                      con.execute("select stage, count(*) n from done where kind='clip' group by stage")}
        n_clips_total = con.execute("select count(*) from clips").fetchone()[0]
        flag_counts: collections.Counter = collections.Counter()
        for r in con.execute("select flags_json from clips where flags_json != '[]'"):
            for f in json.loads(r["flags_json"]):
                flag_counts[f] += 1
        for s in con.execute("select * from sources order by id"):
            m = json.loads(s["meta_json"] or "{}")
            n, h = con.execute("select count(*), coalesce(sum(duration),0) from clips where source_id=?",
                               (s["id"],)).fetchone()
            sid = f"src{s['id']:05d}"
            stages_done = done_src.get(str(s["id"]), set()) | done_src.get(sid, set())
            stages_done |= {st for st, chans in done_channel.items() if s["channel"] in chans}
            sources.append({"id": s["id"], "sid": sid, "channel": s["channel"], "name": Path(s["path"]).name,
                            "duration": s["duration"], "container_duration": m.get("container_duration"),
                            "cap_sec": m.get("cap_sec"), "error": s["error"], "flags": m.get("source_flags", []),
                            "n_words": m.get("n_words"), "n_clips": n, "clip_sec": h,
                            "stages": sorted(stages_done, key=STAGES.index)})
    finally:
        con.close()
    manifest = load_manifest()
    notes = load_notes()
    reason_counts: collections.Counter = collections.Counter()
    for v in manifest.values():
        for x in v["exclusion_reasons"]:
            reason_counts[x] += 1
    return {"flags": dict(flag_counts.most_common()), "reasons": dict(reason_counts.most_common()),
            "work": str(WORK.relative_to(ROOT)) if WORK.is_relative_to(ROOT) else str(WORK),
            "now": time.strftime("%H:%M:%S"), "sources": sources, "stages": STAGES,
            "clip_stage_done": clip_stage, "n_clips": n_clips_total,
            "manifest": {"exists": bool(manifest), "n": len(manifest),
                         "recommended": sum(1 for v in manifest.values() if v["recommended"])},
            "notes": {"n": len(notes), "by_verdict": collections.Counter(v["verdict"] for v in notes.values())},
            "tags": [{"key": k, "label": lb, "hotkey": hk} for k, lb, hk in TAGS],
            "verdicts": VERDICTS,
            "channels": channels(sources, manifest, notes),
            "log": log_tail()}


def channels(sources: list[dict], manifest: dict, notes: dict) -> list[dict]:
    """Kanal başına: kayıt/saat/klip, önerilen sayısı, deste ilerlemesi, karar ve etiket sayıları."""
    con = connect()
    try:
        by_ch_clips = {r["channel"]: (r["n"], r["sec"]) for r in
                       con.execute("select channel, count(*) n, coalesce(sum(duration),0) sec from clips group by channel")}
        clip_channel = {r["id"]: r["channel"] for r in con.execute("select id, channel from clips")}
    finally:
        con.close()
    rec_by_ch: collections.Counter = collections.Counter()
    for cid, v in manifest.items():
        if v["recommended"]:
            rec_by_ch[clip_channel.get(cid, "")] += 1
    decks = load_decks()
    out = []
    for ch in sorted({s["channel"] for s in sources}, key=str.casefold):
        srcs = [s for s in sources if s["channel"] == ch]
        n_clips, sec = by_ch_clips.get(ch, (0, 0.0))
        deck = decks.get(ch, {})
        ids = deck.get("ids", [])
        ch_notes = [notes[i] for i in ids if i in notes] if ids else [v for v in notes.values() if clip_channel.get(v["clip_id"]) == ch]
        verdicts = collections.Counter(v["verdict"] for v in ch_notes if v["verdict"])
        tags: collections.Counter = collections.Counter()
        for v in ch_notes:
            tags.update(v.get("tags", []))
        out.append({"channel": ch, "n_sources": len(srcs), "hours": sum(s["duration"] or 0 for s in srcs) / 3600,
                    "stages_done": sum(1 for s in srcs if "segment" in s["stages"]),
                    "n_clips": n_clips, "clip_hours": sec / 3600, "recommended": rec_by_ch.get(ch, 0),
                    "deck_n": len(ids), "reviewed": sum(1 for v in ch_notes if v["verdict"]),
                    "verdicts": dict(verdicts), "tags": dict(tags),
                    "errors": sum(1 for s in srcs if s["error"])})
    return out


# ------------------------------------------------------------------ deste
def load_decks() -> dict[str, dict]:
    if DECKS.exists():
        return json.loads(DECKS.read_text(encoding="utf-8"))
    return {}


def save_decks(decks: dict) -> None:
    DECKS.write_text(json.dumps(decks, ensure_ascii=False, indent=1), encoding="utf-8")


def draw_deck(channel: str, n: int, pool: str, seed: int) -> dict:
    """Kanalın kliplerinden n tanesini kaynaklara eşit dağıtarak, tohumla çek.

    pool: 'rec' = manifest varsa yalnızca önerilen alt küme (yoksa hepsi),
    'all' = bütün klipler, 'excluded' = yalnızca dışlananlar.
    """
    con = connect()
    try:
        rows = con.execute("select id, source_id, audio from clips where channel=? order by source_id, idx",
                           (channel,)).fetchall()
    finally:
        con.close()
    manifest = load_manifest()
    cand = [r for r in rows if r["audio"]]
    if manifest and pool == "rec":
        cand = [r for r in cand if manifest.get(r["id"], {}).get("recommended") is True]
    elif manifest and pool == "excluded":
        cand = [r for r in cand if manifest.get(r["id"], {}).get("recommended") is False]
    by_src: dict[int, list[str]] = collections.defaultdict(list)
    for r in cand:
        by_src[r["source_id"]].append(r["id"])
    rng = random.Random(seed * 1_000_003 + zlib.crc32(channel.encode("utf-8")))
    queues = [rng.sample(v, len(v)) for _, v in sorted(by_src.items())]
    rng.shuffle(queues)
    ids: list[str] = []
    while queues and len(ids) < n:            # kaynaklar dönüşümlü: 3 kayıt × ~7 klip
        for q in list(queues):
            if len(ids) >= n:
                break
            ids.append(q.pop(0))
            if not q:
                queues.remove(q)
    return {"ids": ids, "pool": pool if manifest else "all", "n": n, "seed": seed,
            "pool_size": len(cand), "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}


def channel_ready(channel: str, pool: str) -> tuple[bool, str]:
    """Deste kalıcı olabilir mi? Kanalın bütün kayıtları bölütlenmiş olmalı;
    önerilen havuz için ayrıca manifest olmalı. Aksi hâlde deste tek kayıttan
    çekilip kalıcılaşır ve kanalın geri kalanı hiç görülmez."""
    con = connect()
    try:
        ids = [r["id"] for r in con.execute("select id from sources where channel=?", (channel,))]
        done = {r["key"] for r in con.execute("select key from done where kind='source' and stage='segment'")}
    finally:
        con.close()
    missing = [i for i in ids if str(i) not in done and f"src{i:05d}" not in done]
    if missing:
        return False, f"kanalın {len(missing)}/{len(ids)} kaydı henüz bölütlenmedi"
    if pool in ("rec", "excluded") and not load_manifest():
        return False, "önerilen alt küme henüz hesaplanmadı (export bekleniyor)"
    return True, ""


def deck(params: dict, redraw: bool = False) -> dict:
    channel = params.get("channel", "")
    n = max(1, min(int(params.get("n") or 20), 200))
    pool = params.get("pool") or "rec"
    seed = int(params.get("seed") or 2026)
    decks = load_decks()
    d = decks.get(channel)
    if redraw or not d:
        d = draw_deck(channel, n, pool, seed if not redraw else int(time.time_ns() % 1_000_000))
        ready, why = channel_ready(channel, pool)
        d["temporary"] = "" if ready else why
        if d["ids"] and ready:
            decks[channel] = d
            save_decks(decks)
    rows = clip_rows(ids=d["ids"], channel=channel)
    order = {cid: i for i, cid in enumerate(d["ids"])}
    rows.sort(key=lambda c: order.get(c["id"], 1e9))
    return {**d, "clips": rows}


# ---------------------------------------------------------------- klipler
COND_RE = re.compile(r"^\s*([a-z_]+)\s*(>=|<=|>|<|=)\s*(-?\d+(?:\.\d+)?)\s*$")


def parse_conds(text: str) -> list[tuple[str, str, float]]:
    """'music_to_speech_db>-40;word_confidence<0.6' → [(metrik, op, değer)]. Bozuk parça yok sayılır."""
    out = []
    for part in text.split(";"):
        m = COND_RE.match(part)
        if m:
            out.append((m[1], m[2], float(m[3])))
    return out


def metric_value(c: dict, name: str):
    """Koşullarda ve sıralamada kullanılan değer: klip alanı ya da ölçüm."""
    if name in ("start", "end", "duration", "idx"):
        return c.get(name)
    v = c["metrics"].get(name)
    return float(v) if isinstance(v, bool) else v


def cond_ok(cond, c: dict) -> bool:
    name, op, val = cond
    v = metric_value(c, name)
    if v is None or isinstance(v, str):
        return False
    return {">": v > val, "<": v < val, ">=": v >= val, "<=": v <= val, "=": v == val}[op]


_clips_cache: tuple[tuple, list[dict]] | None = None


def base_rows() -> list[dict]:
    """Bütün klipler, ölçümleri çözülmüş; manifest ve notlar bindirilmemiş.

    Süzgeç istekleri saniyede birkaç kez gelir ve her biri bütün klipleri
    tarar; depo değişmediği sürece çözümlenmiş satırlar bellekte tutulur.
    Anahtar: dosya damgaları + klip sayısı, yani hat yazdıkça tazelenir."""
    global _clips_cache
    con = connect()
    try:
        wal = DB.parent / (DB.name + "-wal")
        st = DB.stat()
        wst = wal.stat() if wal.exists() else None
        n = con.execute("select count(*) from clips").fetchone()[0]
        key = (st.st_mtime_ns, st.st_size, wst.st_mtime_ns if wst else 0, wst.st_size if wst else 0, n)
        if _clips_cache and _clips_cache[0] == key:
            return _clips_cache[1]
        src_name = {r["id"]: Path(r["path"]).name for r in con.execute("select id, path from sources")}
        rows = []
        for r in con.execute("select * from clips order by source_id, idx"):
            text, raw, spoken = r["text"] or "", r["text_raw"] or "", r["text_spoken"] or ""
            rows.append({"id": r["id"], "source_id": r["source_id"], "source_name": src_name.get(r["source_id"], ""),
                         "idx": r["idx"], "channel": r["channel"],
                         "start": r["start"], "end": r["end"], "duration": r["duration"],
                         "text": text, "text_raw": raw, "text_spoken": spoken,
                         "raw_differs": raw != text, "spoken_differs": spoken != text,
                         "n_chars": len(text),
                         "flags": json.loads(r["flags_json"] or "[]"),
                         "metrics": json.loads(r["metrics_json"] or "{}"),
                         "has_audio": bool(r["audio"]),
                         "_lc": lower(text) + " " + lower(raw)})
    finally:
        con.close()
    _clips_cache = (key, rows)
    return rows


def overlay(c: dict, manifest: dict, notes: dict) -> dict:
    """Temel satıra manifest kararını ve son manuel notu bindir."""
    m = manifest.get(c["id"], {})
    out = {k: v for k, v in c.items() if k != "_lc"}
    out.update({"recommended": m.get("recommended"), "exclusion_reasons": m.get("exclusion_reasons", []),
                "duplicate_of": m.get("duplicate_of"), "policy_version": m.get("policy_version"),
                "note": notes.get(c["id"])})
    return out


def clip_rows(ids: list[str], channel: str = "") -> list[dict]:
    """Verilen kimlikler (deste). Sıra çağıranın işidir."""
    want = set(ids)
    if not want:
        return []
    manifest, notes = load_manifest(), load_notes()
    return [overlay(c, manifest, notes) for c in base_rows() if c["id"] in want]


# ------------------------------------------------ sütunlar ve genel süzgeç
#: Sabit sütunlar: anahtar, sayfadaki ad, tür, öbek. Ölçümler bunlara depodan
#: eklenir (yeni bir aşama yeni ölçüm yazınca sütun kendiliğinden görünür).
BASE_COLUMNS = [
    ("id", "klip kimliği", "str", "klip"),
    ("channel", "kanal", "enum", "klip"),
    ("source_id", "kaynak no", "num", "klip"),
    ("source_name", "kaynak dosyası", "str", "klip"),
    ("idx", "kayıttaki sıra", "num", "klip"),
    ("start", "başlangıç (s)", "num", "klip"),
    ("end", "bitiş (s)", "num", "klip"),
    ("duration", "süre (s)", "num", "klip"),
    ("has_audio", "ses dosyası var", "bool", "klip"),
    ("flags", "işaretler", "list", "klip"),
    ("text", "metin", "str", "metin"),
    ("text_raw", "ham metin", "str", "metin"),
    ("text_spoken", "okunuş metni", "str", "metin"),
    ("raw_differs", "ham metin farklı", "bool", "metin"),
    ("spoken_differs", "okunuş metni farklı", "bool", "metin"),
    ("n_chars", "karakter sayısı", "num", "metin"),
    ("recommended", "önerilen alt kümede", "bool", "politika"),
    ("exclusion_reasons", "dışlanma sebepleri", "list", "politika"),
    ("duplicate_of", "kopyası olduğu klip", "str", "politika"),
    ("policy_version", "politika sürümü", "str", "politika"),
    ("verdict", "manuel karar", "enum", "manuel"),
    ("tags", "kusur etiketleri", "list", "manuel"),
    ("note_text", "not metni", "str", "manuel"),
    ("note_ts", "not zamanı", "str", "manuel"),
]
METRIC_LABELS = {
    "n_words": "kelime sayısı", "word_confidence": "kelime güveni min",
    "word_confidence_mean": "kelime güveni ort", "confidence_source": "güven kaynağı",
    "align_score_min": "hizalama skoru min", "align_score_mean": "hizalama skoru ort",
    "music_to_speech_db": "müzik/konuşma dB", "music_score_audioset": "audioset müzik skoru",
    "music_db_separated": "ayrıştırılmış müzik dB", "speech_ratio": "konuşma oranı",
    "internal_silence_sec": "iç sessizlik (s)", "leading_silence_sec": "baş sessizlik (s)",
    "trailing_silence_sec": "son sessizlik (s)", "lead_gap_sec": "baş komşu boşluğu (s)",
    "trail_gap_sec": "son komşu boşluğu (s)", "rms_dbfs": "RMS dBFS", "peak_dbfs": "tepe dBFS",
    "clip_ratio": "kırpılma oranı", "music_db_separated": "müzik ayrıştırmayla ölçüldü",
    "music_stem_db.vocals": "kaynak: vokal dB", "music_stem_db.drums": "kaynak: davul dB",
    "music_stem_db.bass": "kaynak: bas dB", "music_stem_db.other": "kaynak: diğer çalgı dB",
}
#: Tür başına kullanılabilir işleçler; sayfadaki açılır liste bunu okur.
OPS = {
    "num": [("gt", ">"), ("ge", "≥"), ("lt", "<"), ("le", "≤"), ("eq", "="), ("ne", "≠"),
            ("empty", "ölçüm yok"), ("notempty", "ölçüm var")],
    "str": [("contains", "içerir"), ("ncontains", "içermez"), ("eq", "eşittir"), ("ne", "eşit değil"),
            ("starts", "ile başlar"), ("ends", "ile biter"), ("re", "düzenli ifade"),
            ("empty", "boş"), ("notempty", "dolu")],
    "enum": [("eq", "eşittir"), ("ne", "eşit değil"), ("contains", "içerir"),
             ("empty", "boş"), ("notempty", "dolu")],
    "list": [("has", "içinde var"), ("nothas", "içinde yok"), ("empty", "boş"), ("notempty", "dolu"),
             ("count_gt", "öğe sayısı >"), ("count_lt", "öğe sayısı <")],
    "bool": [("true", "doğru"), ("false", "yanlış"), ("empty", "hesaplanmadı")],
}


def field(c: dict, key: str):
    """Bir klibin herhangi bir sütunundaki değer: klip alanı, ölçüm ya da not.
    İç içe ölçümler noktayla açılır: `music_stem_db.vocals`."""
    if key in c:
        return c[key]
    if key in c["metrics"]:
        return c["metrics"][key]
    if "." in key:
        head, _, tail = key.partition(".")
        v = c["metrics"].get(head)
        return v.get(tail) if isinstance(v, dict) else None
    note = c.get("note") or {}
    if key == "verdict":
        return note.get("verdict") or None
    if key == "tags":
        return note.get("tags", [])
    if key == "note_text":
        return note.get("note") or None
    if key == "note_ts":
        return note.get("ts") or None
    return None


def _num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def is_empty(v) -> bool:
    return v is None or v == "" or v == []


def op_match(v, op: str, raw: str) -> bool:
    """Tek bir süzgeç satırı: değer, işleç, kullanıcı girdisi."""
    if op == "empty":
        return is_empty(v)
    if op == "notempty":
        return not is_empty(v)
    if op == "true":
        return v is True or v == 1
    if op == "false":
        return v is False or v == 0
    if isinstance(v, list):
        t = lower(str(raw))
        if op == "has":
            return any(t in lower(str(x)) for x in v)
        if op == "nothas":
            return not any(t in lower(str(x)) for x in v)
        n = _num(raw)
        if op == "count_gt":
            return n is not None and len(v) > n
        if op == "count_lt":
            return n is not None and len(v) < n
        return False
    if op in ("gt", "ge", "lt", "le") or (op in ("eq", "ne") and isinstance(v, (int, float)) and not isinstance(v, bool)):
        a, b = _num(v), _num(raw)
        if a is None or b is None:
            return False
        return {"gt": a > b, "ge": a >= b, "lt": a < b, "le": a <= b, "eq": a == b, "ne": a != b}[op]
    t, s_ = lower(str(raw)), lower("" if v is None else str(v))
    return {"eq": s_ == t, "ne": s_ != t, "contains": t in s_, "ncontains": t not in s_,
            "starts": s_.startswith(t), "ends": s_.endswith(t),
            "re": bool(re.search(raw, str(v or ""), re.IGNORECASE))}.get(op, False)


def parse_filters(text: str) -> list[dict]:
    """Sayfadan gelen JSON süzgeç satırları: [{"c":sütun,"o":işleç,"v":değer}, …]."""
    if not text:
        return []
    try:
        rows = json.loads(text)
    except json.JSONDecodeError:
        return []
    return [r for r in rows if isinstance(r, dict) and r.get("c") and r.get("o")]


def columns() -> list[dict]:
    """Süzülebilir bütün sütunlar; sayısal olmayanlarda depodaki değer listesiyle."""
    rows = base_rows()
    manifest, notes = load_manifest(), load_notes()
    #: Ölçüm türü tek klipten kestirilemez (ilk klipte null olabilir): boş
    #: olmayan bütün değerlere bakılır, en sık tür kazanır.
    kinds: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    for r in rows:
        for k, v in r["metrics"].items():
            if v is None or v == "":
                kinds[k]["?"] += 0                  # anahtar görünsün, tür oy almasın
                continue
            if isinstance(v, dict):                 # iç içe ölçüm: alt anahtarlar ayrı sütun
                for sub, sv in v.items():
                    kinds[f"{k}.{sub}"]["num" if isinstance(sv, (int, float)) and not isinstance(sv, bool)
                                        else "enum"] += 1
                continue
            kinds[k]["bool" if isinstance(v, bool) else "num" if isinstance(v, (int, float))
                     else "list" if isinstance(v, list) else "enum"] += 1
    seen = {k: (c.most_common(1)[0][0] if c and c.most_common(1)[0][1] else "num") for k, c in kinds.items()}
    out = [{"key": k, "label": lb, "type": t, "group": g} for k, lb, t, g in BASE_COLUMNS]
    out += [{"key": k, "label": METRIC_LABELS.get(k, k), "type": t, "group": "ölçüm"}
            for k, t in sorted(seen.items(), key=lambda kv: (kv[0] not in METRIC_LABELS, kv[0]))]
    vals: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    for r in rows:
        vals["channel"][r["channel"]] += 1
        vals["source_name"][r["source_name"]] += 1
        for f in r["flags"]:
            vals["flags"][f] += 1
        for k, v in r["metrics"].items():
            if isinstance(v, str):
                vals[k][v] += 1
    for m in manifest.values():
        for x in m.get("exclusion_reasons", []):
            vals["exclusion_reasons"][x] += 1
        if m.get("policy_version"):
            vals["policy_version"][str(m["policy_version"])] += 1
    for n in notes.values():
        if n.get("verdict"):
            vals["verdict"][n["verdict"]] += 1
        for t in n.get("tags", []):
            vals["tags"][t] += 1
    for col in out:
        v = vals.get(col["key"])
        if v:
            col["values"] = [[k, n] for k, n in v.most_common(60)]
    return out


def select_clips(params: dict) -> list[dict]:
    """Süzgeçlerden geçen klipler (sıralama/örnekleme yok). Tek yer: hem liste,
    hem karne, hem dağılım aynı kümeyi görür."""
    q = lower(params.get("q", "").strip())
    flag = params.get("flag", "")
    rec = params.get("rec", "all")
    noted = params.get("noted", "all")
    source = params.get("source", "")
    channel = params.get("channel", "")
    reason = params.get("reason", "")
    dmin = float(params.get("dmin") or 0)
    dmax = float(params.get("dmax") or 1e9)
    conds = parse_conds(params.get("cond", ""))
    rows_f = parse_filters(params.get("f", ""))
    ids = {x.strip() for x in re.split(r"[\s,;]+", params.get("ids", "")) if x.strip()}
    only_audio = params.get("audio", "") == "yes"
    manifest, notes = load_manifest(), load_notes()
    out = []
    for r in base_rows():
        if source and source != "all" and r["source_id"] != int(source):
            continue
        if channel and r["channel"] != channel:
            continue
        if ids and r["id"] not in ids:
            continue
        if q and q not in r["_lc"]:
            continue
        if flag == "none" and r["flags"]:
            continue
        if flag and flag != "none" and flag not in r["flags"]:
            continue
        if not (dmin <= (r["duration"] or 0) <= dmax):
            continue
        if only_audio and not r["has_audio"]:
            continue
        if conds and not all(cond_ok(cc, r) for cc in conds):
            continue
        c = overlay(r, manifest, notes)
        if rec == "yes" and c["recommended"] is not True:
            continue
        if rec == "no" and c["recommended"] is not False:
            continue
        if reason and not any(reason in x for x in c["exclusion_reasons"]):
            continue
        note = c["note"]
        if noted == "yes" and not note:
            continue
        if noted == "no" and note:
            continue
        if noted in VERDICTS and (not note or note["verdict"] != noted):
            continue
        if noted.startswith("tag:") and (not note or noted[4:] not in note.get("tags", [])):
            continue
        if rows_f and not all(op_match(field(c, f["c"]), f["o"], f.get("v", "")) for f in rows_f):
            continue
        out.append(c)
    return out


def sort_key(c: dict, col: str):
    """Her sütunda sıralama: sayı sayıyla, metin metinle; boşlar en sonda."""
    v = field(c, col)
    if isinstance(v, list):
        v = ", ".join(map(str, v)) or None
    if isinstance(v, bool):
        v = int(v)
    if v is None or v == "":
        return (1, 0.0, "")
    if isinstance(v, (int, float)):
        return (0, float(v), "")
    return (0, 0.0, lower(str(v)))


def sort_clips(rows: list[dict], sort: str, desc: bool) -> None:
    if not sort:
        return
    rows.sort(key=lambda c: sort_key(c, sort), reverse=desc)
    if desc:                      # değeri olmayanlar her hâlde sonda kalsın
        rows.sort(key=lambda c: sort_key(c, sort)[0])


def clips(params: dict) -> dict:
    out = select_clips(params)
    total = len(out)
    sort = params.get("sort", "start")
    desc = params.get("dir", "asc") == "desc"
    offset = int(params.get("offset", 0) or 0)
    limit = max(1, min(int(params.get("limit", 200) or 200), 1000))
    sample = int(params.get("sample") or 0)
    if sample:
        # Rastgele örnek: süzgeçten geçen havuzdan tohumlu, tekrarlanabilir çekim.
        rng = random.Random(int(params.get("seed") or time.time_ns() % 1_000_000))
        out = rng.sample(out, min(sample, len(out)))
        return {"total": total, "offset": 0, "sampled": len(out), "clips": out}
    sort_clips(out, sort, desc)
    return {"total": total, "offset": offset, "clips": out[offset:offset + limit]}


# ------------------------------------------------------- ölçüt karnesi
PCTS = [1, 5, 10, 25, 50, 75, 90, 95, 99]


def percentile(vals: list[float], p: float) -> float:
    """Doğrusal aradeğerli yüzdelik (numpy'siz; vals sıralı olmalı)."""
    if not vals:
        return float("nan")
    k = (len(vals) - 1) * p / 100
    lo, hi = int(k), min(int(k) + 1, len(vals) - 1)
    return vals[lo] + (vals[hi] - vals[lo]) * (k - lo)


def distribution(rows: list[dict], metric: str, bins: int = 24) -> dict:
    """Süzülen havuzda bir ölçümün dağılımı: yüzdelikler + histogram.

    Eşik seçmek için: p5/p95 nerede, hangi kovada kaç klip var, o kovadan
    itibaren kaç klip kalır (kümülatif). Kovaya tıklamak koşul üretir."""
    vals = sorted(float(v) for v in (field(c, metric) for c in rows)
                  if isinstance(v, (int, float)) and not isinstance(v, bool))
    if not vals:
        return {"metric": metric, "n": 0, "pcts": {}, "bins": []}
    lo, hi = vals[0], vals[-1]
    if hi <= lo:
        hi = lo + 1e-9
    width = (hi - lo) / bins
    counts = [0] * bins
    for v in vals:
        counts[min(bins - 1, int((v - lo) / width))] += 1
    below, out_bins = 0, []
    for i, n in enumerate(counts):
        out_bins.append({"lo": lo + i * width, "hi": lo + (i + 1) * width, "n": n,
                         "below": below, "above": len(vals) - below - n})
        below += n
    return {"metric": metric, "n": len(vals), "min": lo, "max": vals[-1], "mean": sum(vals) / len(vals),
            "pcts": {str(p): percentile(vals, p) for p in PCTS}, "bins": out_bins}


def stats(params: dict) -> dict:
    """Süzgeçten geçen havuzun karnesi: kaç klip, kaçına karar verilmiş, karar
    dağılımı, en sık kusur etiketleri, kanal/sebep kırılımı ve istenirse bir
    ölçümün dağılımı. Manuel test döngüsünün ölçtüğü sayı budur."""
    rows = select_clips(params)
    verdicts: collections.Counter = collections.Counter()
    tags: collections.Counter = collections.Counter()
    chans: collections.Counter = collections.Counter()
    reasons: collections.Counter = collections.Counter()
    flags: collections.Counter = collections.Counter()
    rec = {"yes": 0, "no": 0, "none": 0}
    sec = 0.0
    for c in rows:
        sec += c["duration"] or 0
        chans[c["channel"]] += 1
        rec["yes" if c["recommended"] is True else "no" if c["recommended"] is False else "none"] += 1
        for x in c["exclusion_reasons"]:
            reasons[x] += 1
        for f in c["flags"]:
            flags[f] += 1
        n = c["note"]
        if n and n["verdict"]:
            verdicts[n["verdict"]] += 1
            for t in n.get("tags", []):
                tags[t] += 1
    judged = sum(verdicts.values())
    out = {"n": len(rows), "hours": sec / 3600, "judged": judged, "verdicts": dict(verdicts),
           "clean_rate": (verdicts.get("temiz", 0) / judged) if judged else None,
           "tags": dict(tags.most_common(6)), "channels": dict(chans.most_common(8)), "n_channels": len(chans),
           "reasons": dict(reasons.most_common(6)), "flags": dict(flags.most_common(6)), "rec": rec}
    metric = params.get("metric", "")
    if metric:
        out["dist"] = distribution(rows, metric)
    return out


# ------------------------------------------------------ kayıtlı süzgeçler
def load_presets() -> list[dict]:
    if PRESETS.exists():
        return json.loads(PRESETS.read_text(encoding="utf-8"))
    return []


def edit_presets(body: dict) -> list[dict]:
    """{'name':…, 'params':{…}} kaydeder (aynı ad üzerine yazar);
    {'name':…, 'delete':true} siler. Ölçüt kümesi böylece tekrar açılabilir."""
    name = str(body.get("name", "")).strip()
    if not name:
        raise ValueError("ad boş")
    items = [p for p in load_presets() if p["name"] != name]
    if not body.get("delete"):
        items.append({"name": name, "params": dict(body.get("params") or {}),
                      "ts": time.strftime("%Y-%m-%dT%H:%M:%S")})
    items.sort(key=lambda p: p["name"].casefold())
    PRESETS.write_text(json.dumps(items, ensure_ascii=False, indent=1), encoding="utf-8")
    return items


# --------------------------------------------------------------- bulgular
def findings() -> dict:
    """Kanal × karar/etiket tablosu ve karar verilmiş kliplerin listesi."""
    notes = load_notes()
    con = connect()
    try:
        info = {r["id"]: (r["channel"], r["text"], r["start"], r["end"]) for r in
                con.execute("select id, channel, text, start, \"end\" from clips")}
    finally:
        con.close()
    rows_by_ch: dict[str, dict] = {}
    listed = []
    for cid, v in notes.items():
        if not v["verdict"]:
            continue
        ch = v.get("channel") or (info.get(cid) or ("?",))[0]
        row = rows_by_ch.setdefault(ch, {"channel": ch, "reviewed": 0, **{k: 0 for k in VERDICTS}, **{k: 0 for k in TAG_KEYS}})
        row["reviewed"] += 1
        row[v["verdict"]] += 1
        for t in v.get("tags", []):
            if t in row:
                row[t] += 1
        text = (info.get(cid) or ("", "", 0, 0))[1]
        listed.append({"clip_id": cid, "channel": ch, "verdict": v["verdict"], "tags": v.get("tags", []),
                       "note": v.get("note", ""), "text": text, "ts": v["ts"]})
    rows = sorted(rows_by_ch.values(), key=lambda r: r["channel"].casefold())
    total = {"channel": "TOPLAM", "reviewed": 0, **{k: 0 for k in VERDICTS}, **{k: 0 for k in TAG_KEYS}}
    for r in rows:
        for k, v in r.items():
            if k != "channel":
                total[k] += v
    listed.sort(key=lambda x: (x["channel"].casefold(), x["clip_id"]))
    return {"columns": ["channel", "reviewed", *VERDICTS, *TAG_KEYS], "rows": rows, "total": total, "clips": listed,
            "tag_labels": {k: lb for k, lb, _ in TAGS}}


def findings_csv() -> str:
    f = findings()
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(f["columns"])
    for r in [*f["rows"], f["total"]]:
        w.writerow([r[c] for c in f["columns"]])
    w.writerow([])
    w.writerow(["clip_id", "channel", "verdict", "tags", "note", "text"])
    for c in f["clips"]:
        w.writerow([c["clip_id"], c["channel"], c["verdict"], " ".join(c["tags"]), c["note"], c["text"]])
    return buf.getvalue()


def print_findings() -> None:
    f = findings()
    cols = f["columns"]
    print(f"{NOTES}: {f['total']['reviewed']} karar verilmiş klip")
    head = ["kanal", "dinlenen", *VERDICTS, *[f['tag_labels'][k] for k in TAG_KEYS]]
    widths = [max(24, len(head[0]))] + [max(len(h), 5) for h in head[1:]]
    print("  ".join(h.ljust(w) if i == 0 else h.rjust(w) for i, (h, w) in enumerate(zip(head, widths))))
    for r in [*f["rows"], f["total"]]:
        cells = [str(r[c]) for c in cols]
        print("  ".join(c.ljust(w) if i == 0 else c.rjust(w) for i, (c, w) in enumerate(zip(cells, widths))))
    bad = [c for c in f["clips"] if c["verdict"] != "temiz"]
    if bad:
        print(f"\nkusurlu/kullanılmaz {len(bad)} klip:")
        for c in bad:
            print(f"  {c['clip_id']:18s} {c['channel']:24s} {c['verdict']:11s} {','.join(c['tags']):30s} {c['note'][:40]:40s} | {c['text'][:70]}")


def listen_lists() -> list[dict]:
    """`<work>/listen-*.txt` dosyaları: boşlukla ayrılmış klip kimlikleri. Keşif
    sekmesinde "hazır liste" olarak seçilir (ör. sınır denetimi için 181 klip)."""
    out = []
    for p in sorted(WORK.glob("listen-*.txt")):
        ids = p.read_text(encoding="utf-8").split()
        out.append({"name": p.stem[len("listen-"):], "n": len(ids), "ids": " ".join(ids)})
    return out


# ---------------------------------------------------------------- sunucu
def audio_path(clip_id: str) -> Path | None:
    con = connect()
    try:
        r = con.execute("select audio from clips where id=?", (clip_id,)).fetchone()
    finally:
        con.close()
    return resolve(r["audio"]) if r and r["audio"] else None


def source_audio_path(source_id: int) -> Path | None:
    con = connect()
    try:
        r = con.execute("select audio from sources where id=?", (source_id,)).fetchone()
    finally:
        con.close()
    return resolve(r["audio"]) if r and r["audio"] else None


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    def log_message(self, fmt, *a):  # sessiz
        pass

    def _bytes(self, data: bytes, ctype: str, status=200, extra: dict | None = None):
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(data)

    def _json(self, obj, status=200):
        self._bytes(json.dumps(obj, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8", status)

    def _file(self, path: Path | None):
        if not path or not path.exists():
            self.send_error(404, "ses dosyası yok")
            return
        size = path.stat().st_size
        ctype = mimetypes.guess_type(str(path))[0] or ("audio/flac" if path.suffix == ".flac" else "application/octet-stream")
        if path.suffix == ".flac":
            ctype = "audio/flac"
        start, end = 0, size - 1
        rng = self.headers.get("Range")
        status = 200
        if rng and rng.startswith("bytes="):
            a, _, b = rng[6:].partition("-")
            start = int(a) if a else max(0, size - int(b))
            end = int(b) if (b and a) else size - 1
            end = min(end, size - 1)
            if start >= size or start > end:
                self.send_error(416, "aralık dosya dışında")
                return
            status = 206
        length = end - start + 1
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(length))
        if status == 206:
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.end_headers()
        if self.command == "HEAD":
            return
        with path.open("rb") as fh:
            fh.seek(start)
            remaining = length
            while remaining > 0:
                chunk = fh.read(min(1 << 20, remaining))
                if not chunk:
                    break
                try:
                    self.wfile.write(chunk)
                except (BrokenPipeError, ConnectionResetError):
                    return
                remaining -= len(chunk)

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        params = {k: v[0] for k, v in urllib.parse.parse_qs(u.query).items()}
        try:
            if u.path == "/":
                self._bytes(TEMPLATE.read_text(encoding="utf-8").encode("utf-8"), "text/html; charset=utf-8")
            elif u.path == "/api/summary":
                self._json(summary())
            elif u.path == "/api/clips":
                self._json(clips(params))
            elif u.path == "/api/deck":
                self._json(deck(params))
            elif u.path == "/api/notes":
                self._json(load_notes())
            elif u.path == "/api/columns":
                self._json(columns())
            elif u.path == "/api/ops":
                self._json({t: [[k, lb] for k, lb in v] for t, v in OPS.items()})
            elif u.path == "/api/stats":
                self._json(stats(params))
            elif u.path == "/api/presets":
                self._json(load_presets())
            elif u.path == "/api/lists":
                self._json(listen_lists())
            elif u.path == "/api/findings":
                self._json(findings())
            elif u.path == "/api/findings.csv":
                name = f"bulgular-{WORK.name}-{time.strftime('%Y%m%d')}.csv"
                self._bytes(findings_csv().encode("utf-8-sig"), "text/csv; charset=utf-8",
                            extra={"Content-Disposition": f'attachment; filename="{name}"'})
            elif u.path.startswith("/audio/"):
                self._file(audio_path(urllib.parse.unquote(u.path[len("/audio/"):])))
            elif u.path.startswith("/source-audio/"):
                self._file(source_audio_path(int(u.path[len("/source-audio/"):])))
            else:
                self.send_error(404)
        except sqlite3.OperationalError as e:
            self._json({"error": f"veritabanı: {e}"}, 503)
        except Exception as e:  # noqa: BLE001
            self._json({"error": repr(e)}, 500)

    def do_POST(self):
        u = urllib.parse.urlparse(self.path)
        n = int(self.headers.get("Content-Length") or 0)
        try:
            body = json.loads(self.rfile.read(n) or b"{}")
            if u.path == "/api/note":
                self._json(append_note(body))
            elif u.path == "/api/deck":
                self._json(deck({k: str(v) for k, v in body.items()}, redraw=bool(body.get("redraw"))))
            elif u.path == "/api/presets":
                self._json(edit_presets(body))
            else:
                self.send_error(404)
        except Exception as e:  # noqa: BLE001
            self._json({"error": repr(e)}, 500)


if __name__ == "__main__":
    if args.dump_notes:
        print_findings()
        sys.exit(0)
    if args.csv:
        Path(args.csv).write_text(findings_csv(), encoding="utf-8-sig")
        print(f"yazıldı: {args.csv}")
        sys.exit(0)
    if not DB.exists():
        sys.exit(f"durum deposu yok: {DB}")
    os.chdir(ROOT)
    srv = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"koşu tarayıcısı: http://{args.host}:{args.port}  (work={WORK}, notlar={NOTES}, desteler={DECKS})")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
