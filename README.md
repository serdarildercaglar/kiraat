# kiraat

[![tests](https://github.com/serdarildercaglar/kiraat/actions/workflows/tests.yml/badge.svg)](https://github.com/serdarildercaglar/kiraat/actions/workflows/tests.yml)
[![license: Apache-2.0](https://img.shields.io/badge/code%20license-Apache--2.0-blue.svg)](LICENSE)
[![dataset](https://img.shields.io/badge/%F0%9F%A4%97%20dataset-serdarcaglar%2Fkiraat-yellow.svg)](https://huggingface.co/datasets/serdarcaglar/kiraat)

A production pipeline that turns long-form Turkish audiobook recordings into a
sentence-aligned read-speech corpus for TTS and ASR. The name comes from
*kıraat*, Turkish for "reading aloud".

Its first release, the [KIRAAT dataset](https://huggingface.co/datasets/serdarcaglar/kiraat),
holds **1,840,404 clips / 3,105.7 hours** from 2,680 recordings across 27
channels, with a recommended subset of 2,575.2 hours. The paper is in
[`paper/`](paper/). [Türkçe README](README.tr.md)

## Two invariants

**Cuts happen at sentence boundaries, not at silences.** The pipeline runs
long-form ASR and forced alignment first, finds sentence boundaries on the
transcript and cuts there. Narrators breathe at commas and run sentences
together, so silence-based (VAD) cutting starts clips mid-sentence. In a
206-recording comparison, lowercase-start rates were 14.31% for a VAD baseline
and 1.39% for the sentence-based strategy. `tests/test_segment.py` enforces the
contract.

**No threshold drops a clip.** Stages only measure. Every clip is published
with every metric, and a versioned policy in the config adds a `recommended`
flag plus `exclusion_reasons`. Changing the policy never requires regenerating
the data. `ClipStage.validate_output` rejects any stage that tries to write a
decision.

## Quick start

```bash
pip install torch==2.5.1 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cu124
pip install -r requirements-dev.txt
python -m pytest                      # runs on CPU, no GPU or corpus needed
python -m kiraat run --dry-run        # list the sources that would be processed
python -m kiraat run                  # runtime.max_sources (5 by default)
python scripts/report.py              # summary of the manifest
python -m kiraat schema               # published column schema as a table
```

Dependencies are pinned to exact versions on purpose: an upstream upgrade can
silently change the output. Model weights are pinned by HF revision or by the
package that ships them.

Load the published corpus:

```python
from datasets import load_dataset

train = load_dataset("serdarcaglar/kiraat", split="train", streaming=True)
clip = next(iter(train))
clip["audio"]["array"], clip["text_spoken"], clip["speaker_id"]
```

## Pipeline

`prepare → asr → align → boilerplate → segment → speaker → clip_qc → music → dnsmos → export`

- `kiraat/scheduler.py` overlaps CPU stages and GPU stages in separate process
  pools, and only the main process writes to the store. `--serial` runs the
  same work in one process; both produce the same manifest
  (`scripts/compare_manifests.py`).
- State lives in a versioned SQLite store, so a re-run skips finished work.
- Recordings up to 15 hours are processed without loading them into memory.
- Every run writes `run.json` next to the manifest: git commit, stage
  versions, policy version, full config, model weight IDs and package
  versions.
- Every stage has a small probe script under `scripts/` that makes its output
  inspectable by eye on a few recordings before scaling up.

| path | what it does |
|---|---|
| `kiraat/segment.py`, `boundaries.py` | sentence-aligned segmenter, boundary refinement into silence |
| `kiraat/boilerplate.py` | channel-level mining of intros/outros and announcements |
| `kiraat/scoring.py` | score-based output contract and versioned policy |
| `kiraat/stages/` | prepare, ASR, alignment, segmentation, clip QC, DNSMOS, music, speaker |
| `kiraat/text/` | Turkish casing (I/ı, i/İ), sentence splitting, normalization |
| `configs/default.yaml` | every threshold; unknown keys are an error |
| `docs/` | dataset card, design notes, feature reference, research notebook |

## Rights

The **code** in this repository is licensed under [Apache-2.0](LICENSE). The
license does not cover the audio, the transcripts or the published dataset,
which declare no license (see the
[dataset card](docs/DATASET_CARD.md#rights-use-and-removal)), nor third-party
model weights such as `models/dnsmos/`, which keep their own terms. Rights
holders can request removal by
[opening an issue](https://github.com/serdarildercaglar/kiraat/issues/new?template=removal-request.yml).

## Contributing and citation

See [CONTRIBUTING.md](CONTRIBUTING.md). Cite with [CITATION.cff](CITATION.cff)
or the BibTeX in the [dataset card](docs/DATASET_CARD.md#citation).
