"""python -m kiraat run [--config configs/default.yaml] [--stages prepare asr ...] [--max-sources N]"""

from __future__ import annotations

import argparse
import logging
import sys

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
    args = parser.parse_args(argv)

    cfg = Config.load(args.config)
    if args.max_sources is not None:
        cfg = Config({**cfg.data, "runtime": {**cfg.section("runtime"), "max_sources": args.max_sources}})
    logging.basicConfig(level=getattr(logging, str(cfg.get("runtime.log_level", "INFO"))),
                        format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S")
    Pipeline(cfg).run(args.stages)
    return 0


if __name__ == "__main__":
    sys.exit(main())
