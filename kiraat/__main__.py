"""python -m kiraat run [--config configs/default.yaml] [--stages prepare asr ...] [--max-sources N]
python -m kiraat schema [--check work/sample-5c/manifests/clips.jsonl] [--all]"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from .config import Config
from .pipeline import Pipeline


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="kiraat")
    sub = parser.add_subparsers(dest="cmd", required=True)
    run = sub.add_parser("run", help="hattı koştur")
    run.add_argument("--config", default="configs/default.yaml")
    run.add_argument("--stages", nargs="+", default=None,
                     help="yalnızca bu aşamalar (prepare asr boilerplate segment clip_qc music export)")
    run.add_argument("--max-sources", type=int, default=None, help="runtime.max_sources'ı geçersiz kıl")
    run.add_argument("--max-channels", type=int, default=None, help="runtime.max_channels'ı geçersiz kıl")
    run.add_argument("--max-hours", type=float, default=None, help="runtime.max_hours'ı geçersiz kıl (saat bütçesi)")
    run.add_argument("--sample-seed", type=int, default=None, help="rastgele örneklem tohumu (runtime.sample_seed)")
    run.add_argument("--max-sources-per-channel", type=int, default=None,
                     help="runtime.max_sources_per_channel'ı geçersiz kıl (kanal başına kayıt)")
    run.add_argument("--max-minutes", type=float, default=None,
                     help="prepare.max_minutes'ı geçersiz kıl (kayıt başına dakika tavanı)")
    run.add_argument("--dry-run", action="store_true", help="yalnızca seçilen kaynakları kanal başına özetle, koşma")
    run.add_argument("--work-root", default=None, help="paths.work_root ve paths.db'yi bu dizine taşı (ayrı koşu)")
    sch = sub.add_parser("schema", help="yayımlanan sütun şemasını Markdown tablo olarak bas ya da bir manifestoyu şemayla karşılaştır")
    sch.add_argument("--check", default=None, help="bu clips.jsonl'in anahtarlarını şemayla karşılaştır; uyuşmazlıkta 1 döner")
    sch.add_argument("--all", action="store_true", help="yerel (yayımlanmayan) sütunları da tabloya al")
    args = parser.parse_args(argv)

    if args.cmd == "schema":
        from . import schema
        if args.check:
            missing, unknown = schema.check_manifest_file(Path(args.check))
            print(f"{args.check}: şemada olup manifestoda olmayan zorunlu sütun {sorted(missing) or 'yok'}; "
                  f"manifestoda olup şemada olmayan anahtar {sorted(unknown) or 'yok'}")
            return 1 if (missing or unknown) else 0
        print(schema.markdown_table(published_only=not args.all))
        return 0

    cfg = Config.load(args.config)
    runtime = dict(cfg.section("runtime"))
    for key in ("max_sources", "max_channels", "max_hours", "sample_seed", "max_sources_per_channel"):
        if getattr(args, key) is not None:
            runtime[key] = getattr(args, key)
    prep = dict(cfg.section("prepare"))
    if args.max_minutes is not None:
        prep["max_minutes"] = args.max_minutes
    paths = dict(cfg.section("paths"))
    if args.work_root:
        paths["work_root"] = args.work_root
        paths["db"] = str(Path(args.work_root) / "db" / "state.sqlite")
    cfg = Config({**cfg.data, "runtime": runtime, "prepare": prep, "paths": paths})
    if args.dry_run:
        return dry_run(cfg)
    logging.basicConfig(level=getattr(logging, str(cfg.get("runtime.log_level", "INFO"))),
                        format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S")
    Pipeline(cfg).run(args.stages)
    return 0


def dry_run(cfg: Config) -> int:
    """Seçilen kaynakları kanal başına özetle: kayıt sayısı, ham süre, tavanla
    sayılan süre. Tam koşu başlatmadan örneklemi görmek için."""
    import collections
    from .pipeline import discover_sources
    from .stages.prepare import ffprobe

    cap = float(cfg.get("prepare.max_minutes", 0) or 0) * 60.0
    durations: dict[str, float] = {}
    def duration_of(path: str) -> float:
        durations[path] = ffprobe(path)["duration"]
        return durations[path]
    picked = discover_sources(cfg, duration_of=duration_of)
    per = collections.defaultdict(lambda: [0, 0.0, 0.0])
    for s in picked:
        d = durations.get(s["path"]) or duration_of(s["path"])
        row = per[s["channel"]]
        row[0] += 1
        row[1] += d
        row[2] += min(d, cap) if cap else d
    print(f"{'kanal':26s} {'kayıt':>5s} {'ham':>8s} {'sayılan':>8s}")
    for ch, (n, raw, eff) in sorted(per.items(), key=lambda kv: kv[0].casefold()):
        print(f"{ch:26s} {n:5d} {raw/3600:7.2f}h {eff/3600:7.2f}h")
    tot_raw = sum(v[1] for v in per.values()); tot_eff = sum(v[2] for v in per.values())
    print(f"toplam: {len(picked)} kaynak, {len(per)} kanal, ham {tot_raw/3600:.2f} saat, "
          f"sayılan {tot_eff/3600:.2f} saat (tavan {cap/60:.0f} dk)" if cap else
          f"toplam: {len(picked)} kaynak, {len(per)} kanal, {tot_raw/3600:.2f} saat")
    return 0


if __name__ == "__main__":
    sys.exit(main())
