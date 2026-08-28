"""python -m kiraat run [--config configs/default.yaml] [--stages prepare asr ...] [--max-sources N]"""

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
    run.add_argument("--sample-seed", type=int, default=None, help="rastgele örneklem tohumu (runtime.sample_seed)")
    run.add_argument("--work-root", default=None, help="paths.work_root ve paths.db'yi bu dizine taşı (ayrı koşu)")
    args = parser.parse_args(argv)

    cfg = Config.load(args.config)
    runtime = dict(cfg.section("runtime"))
    for key in ("max_sources", "max_channels", "sample_seed"):
        if getattr(args, key) is not None:
            runtime[key] = getattr(args, key)
    paths = dict(cfg.section("paths"))
    if args.work_root:
        paths["work_root"] = args.work_root
        paths["db"] = str(Path(args.work_root) / "db" / "state.sqlite")
    cfg = Config({**cfg.data, "runtime": runtime, "paths": paths})
    logging.basicConfig(level=getattr(logging, str(cfg.get("runtime.log_level", "INFO"))),
                        format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S")
    Pipeline(cfg).run(args.stages)
    return 0


if __name__ == "__main__":
    sys.exit(main())
