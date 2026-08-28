"""Durum deposu: sqlite, tek dosya.

Kayıtlar (`sources`), klipler (`clips`) ve her aşamanın hangi nesnede
hangi sürümle bittiği (`done`). Aşama çıktıları JSON sütunlarda tutulur;
karar sütunu yoktur — `recommended` yalnızca dışa aktarımda, politikadan
hesaplanır ve manifestoya yazılır.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

SCHEMA = """
create table if not exists sources (
  id integer primary key,
  path text unique not null,
  channel text not null,
  ext text,
  bytes integer,
  duration real,
  source_sample_rate integer,
  audio text,
  error text,
  meta_json text not null default '{}'
);
create table if not exists clips (
  id text primary key,
  source_id integer not null references sources(id),
  channel text not null,
  idx integer not null,
  start real not null,
  "end" real not null,
  duration real not null,
  audio text,
  text_raw text,
  text text,
  text_spoken text,
  flags_json text not null default '[]',
  metrics_json text not null default '{}',
  meta_json text not null default '{}'
);
create index if not exists clips_source on clips(source_id, idx);
create table if not exists done (
  kind text not null,      -- 'source' | 'clip' | 'channel'
  key text not null,
  stage text not null,
  version text not null,
  primary key (kind, key, stage)
);
"""


class Store:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.con = sqlite3.connect(str(self.path))
        self.con.row_factory = sqlite3.Row
        self.con.execute("pragma journal_mode=wal")
        self.con.executescript(SCHEMA)

    def close(self) -> None:
        self.con.close()

    # --------------------------------------------------------------- sources
    def add_sources(self, rows: Iterable[Mapping[str, Any]]) -> int:
        n = 0
        for r in rows:
            cur = self.con.execute(
                "insert or ignore into sources(path, channel, ext, bytes) values (?,?,?,?)",
                (r["path"], r["channel"], r.get("ext"), r.get("bytes")),
            )
            n += cur.rowcount
        self.con.commit()
        return n

    def sources(self, ids: Sequence[int] | None = None) -> list[dict[str, Any]]:
        if ids is None:
            rows = self.con.execute("select * from sources order by id").fetchall()
        else:
            q = ",".join("?" * len(ids))
            rows = self.con.execute(f"select * from sources where id in ({q}) order by id", tuple(ids)).fetchall()
        return [self._source(r) for r in rows]

    def update_source(self, source_id: int, **fields: Any) -> None:
        meta = fields.pop("meta", None)
        sets = [f"{k}=?" for k in fields]
        vals: list[Any] = list(fields.values())
        if meta is not None:
            sets.append("meta_json=?")
            vals.append(json.dumps(meta, ensure_ascii=False))
        if sets:
            self.con.execute(f"update sources set {', '.join(sets)} where id=?", (*vals, source_id))
            self.con.commit()

    @staticmethod
    def _source(r: sqlite3.Row) -> dict[str, Any]:
        d = dict(r)
        d["meta"] = json.loads(d.pop("meta_json") or "{}")
        return d

    # ----------------------------------------------------------------- clips
    def replace_clips(self, source_id: int, clips: Sequence[Mapping[str, Any]]) -> None:
        # Önce done, sonra clips: aksi hâlde alt sorgu boş döner ve eski klip
        # kimliklerinin 'bitti' kayıtları kalır — yeni klipler aynı kimliği
        # aldığında klip aşamaları onları atlar.
        self.con.execute("delete from done where kind='clip' and key in "
                         "(select id from clips where source_id=?)", (source_id,))
        self.con.execute("delete from clips where source_id=?", (source_id,))
        self.con.executemany(
            'insert into clips(id, source_id, channel, idx, start, "end", duration, audio, '
            "text_raw, text, text_spoken, flags_json, metrics_json, meta_json) "
            "values (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            [(c["id"], source_id, c["channel"], c["idx"], c["start"], c["end"], c["duration"],
              c.get("audio"), c.get("text_raw"), c.get("text"), c.get("text_spoken"),
              json.dumps(list(c.get("flags", ())), ensure_ascii=False),
              json.dumps(dict(c.get("metrics", {})), ensure_ascii=False),
              json.dumps(dict(c.get("meta", {})), ensure_ascii=False)) for c in clips],
        )
        self.con.commit()

    def clips(self, source_id: int | None = None) -> list[dict[str, Any]]:
        if source_id is None:
            rows = self.con.execute("select * from clips order by source_id, idx").fetchall()
        else:
            rows = self.con.execute("select * from clips where source_id=? order by idx", (source_id,)).fetchall()
        return [self._clip(r) for r in rows]

    @staticmethod
    def _clip(r: sqlite3.Row) -> dict[str, Any]:
        d = dict(r)
        d["flags"] = json.loads(d.pop("flags_json") or "[]")
        d["metrics"] = json.loads(d.pop("metrics_json") or "{}")
        d["meta"] = json.loads(d.pop("meta_json") or "{}")
        return d

    def merge_clip_results(self, rows: Iterable[Mapping[str, Any]]) -> None:
        """Bir klip aşamasının ölçüm ve işaretlerini mevcut sütunlara katar."""
        for row in rows:
            cur = self.con.execute("select flags_json, metrics_json from clips where id=?", (row["id"],)).fetchone()
            if cur is None:
                raise KeyError(f"klip yok: {row['id']}")
            flags = json.loads(cur["flags_json"])
            for f in row.get("flags", ()):
                if f not in flags:
                    flags.append(f)
            metrics = json.loads(cur["metrics_json"])
            metrics.update(row.get("metrics", {}))
            self.con.execute("update clips set flags_json=?, metrics_json=? where id=?",
                             (json.dumps(flags, ensure_ascii=False), json.dumps(metrics, ensure_ascii=False), row["id"]))
        self.con.commit()

    # ------------------------------------------------------------------ done
    def is_done(self, kind: str, key: str, stage: str, version: str) -> bool:
        r = self.con.execute("select version from done where kind=? and key=? and stage=?",
                             (kind, key, stage)).fetchone()
        return r is not None and r["version"] == version

    def mark_done(self, kind: str, key: str, stage: str, version: str) -> None:
        self.con.execute("insert or replace into done(kind, key, stage, version) values (?,?,?,?)",
                         (kind, key, stage, version))
        self.con.commit()

    def pending_clips(self, stage: str, version: str) -> list[dict[str, Any]]:
        rows = self.con.execute(
            "select c.* from clips c left join done d on d.kind='clip' and d.key=c.id and d.stage=? "
            "where d.key is null or d.version<>? order by c.source_id, c.idx", (stage, version)).fetchall()
        return [self._clip(r) for r in rows]
