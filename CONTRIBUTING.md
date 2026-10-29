# Contributing

Issues and pull requests are welcome in English or Turkish.

## Before you write code

- Read the table at the top of [`docs/DESIGN.md`](docs/DESIGN.md): every
  design decision answers a measured defect of the previous pipeline.
- Keep the two invariants in the [README](README.md#two-invariants): cuts at
  sentence boundaries, and stages that measure but never drop a clip. A new
  signal becomes a policy rule only after a blind listening audit.
- Thresholds belong in [`configs/default.yaml`](configs/default.yaml), never in
  code. `Config.load` rejects unknown keys, so add new keys there.
- Use `kiraat.text.turkish.lower`/`upper` instead of `str.lower()`/`str.upper()`
  on Turkish text (I/ı and i/İ map differently).
- Pin new dependencies to an exact version in `requirements.txt`.

## Workflow

1. Run a changed stage on a few recordings first (`--max-sources`,
   `--max-minutes`) and inspect its output with the matching `scripts/probe_*.py`
   or `scripts/listen_ui.py` before scaling up.
2. Bump the stage's version string when its output changes, so a re-run
   recomputes it instead of reusing stale rows.
3. Add or update tests and run `python -m pytest`. CI runs the same suite on CPU.
4. Describe in the PR what you measured and on how many recordings.

## Reporting problems with the data

Use the issue templates: a bad clip or transcript, a pipeline bug, or a
removal request from a rights holder or narrator. Include clip IDs and the
dataset revision where you can.
