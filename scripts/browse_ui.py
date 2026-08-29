"""Koşu tarayıcısı ve manuel denetim aracı: hat çalışırken kanal kanal klipleri
dinle, kusurları etiketle, bulguları tablo olarak al.

    python scripts/browse_ui.py --work work/sample-25 [--port 8765]
    python scripts/browse_ui.py --work work/sample-25 --dump-notes      # kanal × kusur tablosu
    python scripts/browse_ui.py --work work/sample-25 --csv bulgular.csv

Tarayıcıda http://127.0.0.1:8765 açılır. Üç sekme:

  Denetim   Soldaki kanal listesinden bir kanal seç; kanal için sabit bir
            "deste" çekilir (varsayılan 20 klip, kanalın kayıtlarına eşit
            dağıtılmış, tohumlu). Her klip dinlenir, karar (temiz / kusurlu /
            kullanılmaz) ve kusur etiketleri verilir. Deste
            `<work>/review-decks.json` dosyasında kalıcıdır; koşu ilerleyip
            yeni klip gelse de aynı klipler gösterilir ("yeni deste" ile
            yeniden çekilir).
  Bulgular  Kanal × karar/etiket tablosu, notlu kliplerin listesi, CSV.
  Keşif     Serbest süzgeçler (işaret, dışlanma sebebi, ölçüm koşulu, kimlik
            listesi) ve kaynağa göre gezinti; kural ayarlamak için.

Durum deposu salt-okunur açılır (WAL; hat yazarken okunabilir). Manifest
üretilmişse `recommended` / `exclusion_reasons` kliplerin üstüne bindirilir.
Notlar `<work>/manual-notes.jsonl` dosyasına eklenir; klip başına son not
geçerlidir. Her klibin yanındaki "bağlam" düğmesi kaynağın 24 kHz wav'ından
klibin 2 s öncesinden 2 s sonrasına kadar çalar (kesim sınırı denetimi).
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

STAGES = ["prepare", "asr", "align", "boilerplate", "segment", "clip_qc", "music", "export"]
SORT_KEYS = {"start", "duration", "n_words", "word_confidence", "word_confidence_mean", "align_score_min",
             "align_score_mean", "music_to_speech_db", "music_score_audioset", "speech_ratio",
             "internal_silence_sec", "lead_gap_sec", "trail_gap_sec", "rms_dbfs", "peak_dbfs", "clip_ratio"}
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
TEMPLATE = ROOT / "scripts" / "browse_template.html"


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


def cond_ok(cond, row, metrics) -> bool:
    name, op, val = cond
    v = row[name] if name in ("start", "end", "duration") else metrics.get(name)
    if v is None or isinstance(v, bool) and name not in metrics:
        return False
    if isinstance(v, bool):
        v = float(v)
    return {">": v > val, "<": v < val, ">=": v >= val, "<=": v <= val, "=": v == val}[op]


def clip_row(r, manifest, notes) -> dict:
    metrics = json.loads(r["metrics_json"] or "{}")
    flags = json.loads(r["flags_json"] or "[]")
    mrow = manifest.get(r["id"], {})
    return {"id": r["id"], "source_id": r["source_id"], "idx": r["idx"], "channel": r["channel"],
            "start": r["start"], "end": r["end"], "duration": r["duration"],
            "text": r["text"], "text_raw": r["text_raw"] if r["text_raw"] != r["text"] else None,
            "text_spoken": r["text_spoken"] if r["text_spoken"] != r["text"] else None,
            "flags": flags, "metrics": metrics, "has_audio": bool(r["audio"]),
            "recommended": mrow.get("recommended"), "exclusion_reasons": mrow.get("exclusion_reasons", []),
            "duplicate_of": mrow.get("duplicate_of"), "note": notes.get(r["id"])}


def clip_rows(ids: list[str], channel: str = "") -> list[dict]:
    if not ids:
        return []
    con = connect()
    try:
        q = ",".join("?" * len(ids))
        rows = con.execute(f"select * from clips where id in ({q})", tuple(ids)).fetchall()
    finally:
        con.close()
    manifest, notes = load_manifest(), load_notes()
    return [clip_row(r, manifest, notes) for r in rows]


def clips(params: dict) -> dict:
    source = params.get("source", "")
    q = lower(params.get("q", "").strip())
    flag = params.get("flag", "")
    rec = params.get("rec", "all")
    noted = params.get("noted", "all")
    sort = params.get("sort", "start")
    desc = params.get("dir", "asc") == "desc"
    offset = int(params.get("offset", 0) or 0)
    limit = max(1, min(int(params.get("limit", 200) or 200), 1000))
    dmin = float(params.get("dmin") or 0)
    dmax = float(params.get("dmax") or 1e9)
    channel = params.get("channel", "")
    reason = params.get("reason", "")
    conds = parse_conds(params.get("cond", ""))
    ids = {x.strip() for x in re.split(r"[\s,;]+", params.get("ids", "")) if x.strip()}
    con = connect()
    try:
        if source and source != "all":
            rows = con.execute("select * from clips where source_id=? order by idx", (int(source),)).fetchall()
        else:
            rows = con.execute("select * from clips order by source_id, idx").fetchall()
    finally:
        con.close()
    manifest = load_manifest()
    notes = load_notes()
    out = []
    for r in rows:
        c = clip_row(r, manifest, notes)
        note, flags, metrics, rec_v = c["note"], c["flags"], c["metrics"], c["recommended"]
        if q and q not in lower(r["text"] or "") and q not in lower(r["text_raw"] or ""):
            continue
        if flag == "none" and flags:
            continue
        if flag and flag not in ("none",) and flag not in flags:
            continue
        if rec == "yes" and rec_v is not True:
            continue
        if rec == "no" and rec_v is not False:
            continue
        if noted == "yes" and not note:
            continue
        if noted == "no" and note:
            continue
        if noted in VERDICTS and (not note or note["verdict"] != noted):
            continue
        if noted.startswith("tag:") and (not note or noted[4:] not in note.get("tags", [])):
            continue
        if not (dmin <= (r["duration"] or 0) <= dmax):
            continue
        if channel and r["channel"] != channel:
            continue
        if ids and r["id"] not in ids:
            continue
        if reason and not any(reason in x for x in c["exclusion_reasons"]):
            continue
        if conds and not all(cond_ok(cc, r, metrics) for cc in conds):
            continue
        out.append(c)

    def key(c):
        v = c.get(sort) if sort in ("start", "duration") else c["metrics"].get(sort)
        return (v is None, v if v is not None else 0)
    total = len(out)
    sample = int(params.get("sample") or 0)
    if sample:
        # Rastgele örnek: süzgeçten geçen havuzdan tohumlu, tekrarlanabilir çekim.
        rng = random.Random(int(params.get("seed") or time.time_ns() % 1_000_000))
        out = rng.sample(out, min(sample, len(out)))
        return {"total": total, "offset": 0, "sampled": len(out), "clips": out}
    if sort in SORT_KEYS:
        out.sort(key=key, reverse=desc)
        if desc:  # None'lar sonda kalsın
            out.sort(key=lambda c: key(c)[0])
    return {"total": total, "offset": offset, "clips": out[offset:offset + limit]}


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
