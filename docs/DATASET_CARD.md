---
language:
- tr
task_categories:
- text-to-speech
- automatic-speech-recognition
pretty_name: KIRAAT — A Turkish Read-Speech Corpus
size_categories:
- 1M<n<10M
configs:
- config_name: default
  data_files:
  - split: train
    path: data/train-*
  - split: dev
    path: data/dev-*
  - split: test
    path: data/test-*
  - split: rest
    path: data/rest-*
tags:
- speech
- turkish
- read-speech
- tts
- audiobook
extra_gated_prompt: >-
  No dataset licence is declared. The audio originates from public YouTube
  uploads, whose public availability does not establish redistribution or
  commercial-use permission. Credit the source channels and the dataset.
  Recording, literary-text and narrator rights must be assessed separately;
  this card does not grant rights held by third parties. Rights holders can
  request removal through repository issues or dataset discussions.
extra_gated_fields:
  I accept the attribution and channel-credit condition: checkbox
---

# KIRAAT — A Turkish Read-Speech Corpus

A sentence-aligned read-speech corpus built from **publicly available
recordings on Turkish audiobook YouTube channels**. The channel credits are
in the table at the end of this card; every clip carries the channel it came
from in the `channel` column.

| | |
|---|---|
| clips | **1,840,404** |
| duration | **3,105.7 hours** |
| recommended subset | **1,547,494 clips / 2,575.2 hours** |
| channels | 27 |
| speaker clusters (inferred) | **90** |
| source recordings | 2,680 |
| words (ASR) | 21,695,774 |
| audio | 24 kHz, mono, FLAC, embedded in the parquet shards |
| download size | ~250 GB (clip files measured at 246 GB) |
| splits | `train` / `dev` / `test` / `rest` — the whole corpus is published |
| language | Turkish |

## Loading

```python
from datasets import load_dataset

# the default training subset
train = load_dataset("serdarcaglar/kiraat", split="train")

# 250 GB is a lot to download for a look; stream instead
train = load_dataset("serdarcaglar/kiraat", split="train", streaming=True)
clip = next(iter(train))
clip["audio"]["array"], clip["text_spoken"], clip["speaker_id"]

# everything the policy left out — published, not deleted
rest = load_dataset("serdarcaglar/kiraat", split="rest", streaming=True)
```

Audio is embedded in the parquet shards, so there is no separate audio
download; `datasets` decodes the `audio` column for you. This needs
**`datasets>=4`** — the shards were written with the `List` feature type,
and on 3.x loading fails with `Feature type 'List' not found` before any
row is read. Decoding the `audio` column also needs `torchcodec`
installed; without it you can still read the raw FLAC bytes with
`.cast_column("audio", Audio(decode=False))`.

## Two things that set this corpus apart

**Segmentation follows transcript sentence boundaries.** The reported
206-recording comparison uses lowercase starts and missing final punctuation
as transcript proxies. Lowercase-start rates are 14.31% in the implemented
VAD baseline and 1.39% in the sentence arm; unflagged rates are 12.81% and
0.00%. These checks depend on ASR casing/punctuation and do not establish
acoustic truncation rates. Baseline clips can be inspected from their text,
so absence of a dedicated flag does not make the proxy undetectable.

**No threshold ever drops a clip.** Quality measurements are published as
columns. Which clips belong to the default training subset is decided by a
*versioned policy*, and the reason for every exclusion is written into the
`exclusion_reasons` column. Small score-stratified listening audits informed removal of two candidate
thresholds (`clip_ratio`, `word_confidence`). They do not establish
corpus-wide error rates or downstream training utility. You can cut your own thresholds from the columns — clips with
`recommended=false` have not been deleted.

## Splits

| split | clips | hours | recordings | channels | speaker clusters |
|---|---|---|---|---|---|
| train | 1,512,448 | 2,517.08 | 2,579 | 27 | 89 |
| dev | 5,750 | 9.54 | 40 | 27 | 26 |
| test | 5,473 | 9.30 | 45 | 27 | 26 |
| rest | 316,733 | 569.78 | — | 27 | — |
| **total** | **1,840,404** | **3,105.70** | **2,680** | **27** | **90** |

`train`, `dev` and `test` are drawn from the recommended subset. Every
remaining clip is published in a fourth split, **`rest`** — nothing is
deleted, and a clip's measurement columns are the same there as anywhere
else:

| what is in `rest` | clips | hours |
|---|---|---|
| `recommended=false` | 292,910 | 530.5 |
| recommended but unused: beyond a channel's dev/test duration target, or dropped by the text-leakage cleanup (these are never moved into `train`) | 23,823 | 39.3 |

The `recordings` column above counts recordings whose clips form a split;
`rest` draws clips from recordings across all three, and 16 of the 2,680
recordings have all of their clips in `rest`.

The **train/dev/test splits have disjoint source IDs**. `rest` also contains
clips from their recordings. If adding `rest` to training, first exclude
every dev/test source ID and recheck transcript overlap. `dev`
and `test` are channel-balanced (equal duration target per channel). Text
leakage was checked and cleaned: dev/test clips carrying a sentence
identical to one in `train` were dropped, and the remaining overlap is
**zero** for train--dev and train--test. A separate database audit found
12 shared normalized text keys between dev and test. These checks do not
exclude near-duplicate text, shared books or re-uploads under different IDs.

The reported cluster assignments have overlap: 25 of the 26 test clusters
also occur in training. These are **inferred speaker labels**, not manually
verified identities, and the evaluation is predominantly seen-cluster. If you want
an unseen-speaker experiment, build your own split from the `speaker_id`
column.

## How it was built

Decode to 24 kHz mono with ffmpeg → long-form ASR with faster-whisper
`large-v3` (word timestamps) → forced alignment with torchaudio `MMS_FA` →
channel-level boilerplate/announcement mining → sentence-boundary
segmentation with audio-based boundary refinement → clip measurements (VAD
speech ratio, silences, level, BS.1770 loudness; music via HDemucs +
AudioSet; DNSMOS P.835; speaker embeddings via ECAPA-TDNN) → recommended
subset via the versioned policy.

The export code writes model identifiers, configuration and stage versions
to `run.json`. Speaker-weight provenance is incomplete: the configured
revision is not passed to the loader, and the provenance record omits the
speaker model and its dependencies. The pipeline source is available:
<https://github.com/serdarildercaglar/kiraat>. Every count, hour and share
printed in this card is regenerated from the run database by
`scripts/verify_card.py` — including the duplicate marking, the policy
decision and the four splits, which are recomputed rather than read back.

## Quality distributions (recommended subset)

| column | p05 | p50 | p95 |
|---|---|---|---|
| duration (s) | 2.76 | 5.82 | 10.56 |
| `loudness_lufs` | −27.99 | −20.92 | −12.54 |
| `dnsmos_ovrl` | 2.862 | 3.296 | 3.491 |
| `dnsmos_sig` | 3.271 | 3.563 | 3.710 |
| `dnsmos_bak` | 3.631 | 4.109 | 4.210 |
| `speech_ratio` | 0.851 | 0.977 | 1.000 |
| `align_score_mean` | 0.858 | 0.961 | 0.994 |
| `word_confidence` | 0.550 | 0.917 | 0.999 |
| `n_words` | 5 | 11 | 21 |

Across the whole corpus, **83.6%** of clips have `dnsmos_ovrl ≥ 3.0` — a
threshold commonly used in the field (at `≥ 3.5` the share is 3.9%). No loudness normalization is applied. Mono conversion, resampling and a
40 Hz high-pass filter do modify the signal. Level remains a column.

Music separation was skipped for 1,455,201 clips and run on 385,203 clips.
`music_to_speech_db = -80` with `music_db_separated=false` is an unmeasured
sentinel, not evidence of absent music. Policies below the screening
threshold need further inference.

## Recommended-subset policy (v6)

For `recommended=true`: `speech_ratio ≥ 0.60`, `internal_silence_sec ≤ 1.0`,
and none of the flags `oversize`, `forced_split`, `gap_split`, `short`,
`duplicate`, `boilerplate`, `background_music`.

This leaves out 292,910 clips (530.5 hours). What each rule contributes to
that total — a clip can fail more than one rule:

| rule | clips excluded |
|---|---|
| flag present | 281,995 |
| `internal_silence_sec > 1.0` | 12,757 |
| `speech_ratio < 0.60` | 2,412 |

Flag frequencies over the whole corpus: `background_music` 207,196 (11.26%),
`forced_split` 52,501 (2.85%), `short` 20,904 (1.14%), `oversize` 6,731
(0.37%), `gap_split` 5,141 (0.28%), `boilerplate` 1,053 (0.06%), `duplicate`
576 (0.03%).

The duplicate heuristic matches normalized text, duration, LUFS, RMS and
peak exactly. Matching summary values do not prove waveform identity, and
re-encoding or shifted boundaries can evade the heuristic. Its precision and
recall have not been validated; separate readings are intended to be retained.

## Columns

| column | type | unit | stage | description |
|---|---|---|---|---|
| `audio` | audio | 24 kHz | export | The clip audio itself, mono FLAC embedded in the parquet shards. `datasets` decodes it to `{array, sampling_rate}`; there is no separate audio download. No gain is applied — see `loudness_lufs`. |
| `id` | string |  | segment | Clip id, `srcNNNNN-KKKKK`: the source recording's number and the clip's index within that recording. |
| `source_id` | string |  | prepare | The source recording the clip was cut from (`srcNNNNN`). Every clip of one recording carries the same value; this is the key to group by if you build your own recording-level splits. |
| `channel` | string |  | prepare | The YouTube channel the source recording came from (folder name). This is not a speaker identity; a channel may have several readers. |
| `source_sample_rate` | int | Hz | prepare | The source recording's actual container sample rate. Preparation resamples to at most 24 kHz without upsampling lower-rate sources. All 2,698 prepared recordings in the stored run report 24 kHz; dataset loading declares 24 kHz audio. |
| `source_flags` | list[string] |  | prepare | Recording-level flags. `truncated_source`: the decoded audio is shorter than 95% of the duration the container reports (a corrupt or partial download). |
| `start` | float | s | segment | Clip start time within the source recording, taken from the word timestamp at the sentence boundary, with boundary refinement and lead padding applied. |
| `end` | float | s | segment | Clip end time within the source recording, same as `start`. |
| `duration` | float | s | segment | Clip duration, `end - start`. |
| `text_raw` | string |  | asr | Untouched ASR output (Whisper large-v3), joined over the clip's word span. |
| `text` | string |  | segment | Lightly cleaned text: whitespace, quotes and repeated punctuation fixed; numbers and abbreviations left as they are. The readable/archival version. |
| `text_spoken` | string |  | segment | Text converted to how it is spoken: numbers, ordinals, times/dates/currencies and common abbreviations written out in Turkish. This is the field intended for TTS training. |
| `n_words` | int |  | segment | Word count in the clip (ASR words, with clitics — de/da, mi, ki — attached to the preceding word). |
| `word_confidence` | float |  | segment | The lowest word probability in the clip, either a Whisper word probability or an aligner score depending on `confidence_source`. A single rare word (proper noun, interjection) drags it down; it is a ranking signal, not a gate. |
| `word_confidence_mean` | float |  | segment | The clip mean of word probabilities from the same source. |
| `confidence_source` | string |  | segment | Where the `word_confidence` columns come from: `asr` (Whisper word probability) or `align` (forced-alignment score). |
| `align_score_min` (optional) | float |  | align | The minimum MMS_FA CTC word alignment score in the clip; a model score, not a calibrated probability of transcript correctness or a human-reference error measure. |
| `align_score_mean` (optional) | float |  | align | The clip mean of the aligner's word scores. |
| `lead_gap_sec` (optional) | float | s | segment | Gap between the clip's first word and the previous word in the recording. Empty if it is the recording's first word. A small value means the previous sentence risks bleeding into the clip. |
| `trail_gap_sec` (optional) | float | s | segment | Gap between the clip's last word and the next word in the recording; empty if it is the recording's last word. |
| `leading_silence_sec` | float | s | clip_qc | Time from the clip start to the first speech found by VAD (Silero), from a separate no-padding, short-silence-threshold VAD pass. |
| `trailing_silence_sec` | float | s | clip_qc | Time from VAD's last speech to the clip end, from the same no-padding pass. |
| `internal_silence_sec` | float | s | clip_qc | The longest speechless stretch inside the clip (largest gap between VAD regions). |
| `speech_ratio` | float |  | clip_qc | The fraction of clip duration VAD counts as speech (0–1). |
| `peak_dbfs` | float | dBFS | clip_qc | Absolute peak sample level. |
| `rms_dbfs` | float | dBFS | clip_qc | RMS level of the clip (no gain applied — the source's own level). |
| `clip_ratio` | float |  | clip_qc | Fraction of samples at full scale (\|x\| ≥ 0.99); a measure of digital clipping. |
| `loudness_lufs` (optional) | float | LUFS | clip_qc | BS.1770 integrated loudness (pyloudnorm). No gain is applied to the audio; level normalization is left to you, and this column is its input. Empty for clips shorter than the 0.4 s measurement block or entirely silent. |
| `music_score_audioset` (optional) | float |  | music | Maximum score of an AudioSet AST classifier over its music labels (Music, Background music, Soundtrack…), taken as the max over clip windows. A cheap screening signal; it can coexist with speech. Empty for unreadable clips (`unreadable_audio`). |
| `music_to_speech_db` (optional) | float | dB | music | A physical measurement from source separation (HDemucs): the ratio of accompaniment energy (drums+bass+other) to vocal energy. If the separator did not run, the floor value −80. The `background_music` flag requires both the dB threshold and the configured minimum AudioSet score. The floor value does not measure absent music. Empty for unreadable clips. |
| `music_db_separated` (optional) | bool |  | music | Whether the separator actually ran on this clip. If not, `music_to_speech_db` is the floor value rather than a measurement (the AudioSet score was below the screening threshold). Empty for unreadable clips. |
| `music_stem_db` (optional) | string (JSON) | dB | music | Per-stem energy levels for the separator's four stems (drums, bass, other, vocals); written only for clips the separator ran on. `music_to_speech_db` is derived from these. Published as a JSON object encoded in a string (the key set is not fixed), so parse it with `json.loads`. |
| `dnsmos_sig` (optional) | float |  | dnsmos | DNSMOS P.835 speech quality estimate (SIG, 1–5): distortion of the speech itself. Matches the reference implementation exactly: 9.01 s windows, polynomial mapping, window averaging. Empty for unreadable clips (`unreadable_audio`). |
| `dnsmos_bak` (optional) | float |  | dnsmos | DNSMOS P.835 background estimate (BAK, 1–5): how intrusive the background noise is; higher means cleaner. Empty for unreadable clips. |
| `dnsmos_ovrl` (optional) | float |  | dnsmos | DNSMOS P.835 overall quality estimate (OVRL, 1–5). Not a gate: a policy rule may only be added after blind listening review (see the policy v4 record). Empty for unreadable clips. |
| `flags` | list[string] |  | export | Clip flags; none of them removes a clip. `forced_split`: a sentence that exceeded the duration ceiling on its own was split at internal punctuation; `gap_split`: the same sentence was split at a long silence; `oversize`: no internal punctuation to split on, so the sentence was kept whole and exceeds the ceiling; `short`: duration below `segment.min_sec`; `background_music`: both music thresholds pass; `duplicate`: normalized text and audio summary values match (see `duplicate_of`); `boilerplate`: an intro/announcement pattern that recurs across the channel's recordings; `unreadable_audio`: the clip file could not be read and has no measurements. |
| `duplicate_of` (optional) | string |  | export | If the clip is a duplicate, the id of the copy that was kept; otherwise empty. The heuristic matches normalized text and `dedupe.identity_fields` (duration, LUFS, RMS, peak) exactly; this does not prove waveform identity. A separate reading of the same text is NOT a duplicate — it is kept as prosodic variety; channel is not part of the key. |
| `speaker_id` (optional) | string |  | export | The recording's speaker cluster (`spkNNNN`). Clustering runs over the whole corpus: the merge threshold is taken from the equal-error point of two measured distributions (within-recording clip similarity, and cross-channel recording similarity), and no cluster count is imposed. The identity is recording-level; all clips of a recording carry the same value. Not a gate — the policy has no rule on it. |
| `speaker_consistency` (optional) | float |  | speaker | Mean pairwise cosine similarity among the recording's embedded clips. A low value may indicate acoustic or speaker variation; it does not by itself prove multiple speakers or substitute for diarization. |
| `speaker_margin` (optional) | float |  | export | The recording's similarity to its own cluster centroid minus its similarity to the nearest other cluster. A small value points to a recording near a cluster boundary; a negative value says it may be in the wrong cluster. |
| `recommended` | bool |  | export | Whether the versioned policy (`recommended_subset`) recommends this clip for the default training subset. It removes no data; you can set your own rule from the measurement columns. |
| `exclusion_reasons` | list[string] |  | export | If `recommended=false`, the list of rules that were not met: `metric<threshold`, `metric>threshold`, `flag:name[,name]`, `missing_measurement:metric`. Empty for recommended clips. |
| `policy_version` | string |  | export | The policy version that produced `recommended` and `exclusion_reasons`; the rules are versioned in the config, and when they change only these three columns are recomputed. |
| `split` | string |  | export | The published split the row belongs to: `train`, `dev`, `test` or `rest`. |

## Known limitations

- **The text is ASR output**, not corrected by hand; `text_raw`, `text` and
  `text_spoken` are all derived from the same ASR transcript.
- **Digits are not force-aligned.** The aligner (`MMS_FA`) is character-based
  and its dictionary has no digit characters, so words containing digits
  ("1923", "15'inci", "%20") get their timestamps from ASR rather than the
  aligner, and those words do not contribute to `align_score`. Share of
  affected clips: **3.08%** (2.91% within the recommended subset). Converting
  the text to its spoken form before alignment would have solved this, but it
  would change the published text itself, so it was not done; the
  `text_spoken` column provides the spoken form separately.
- **Garbage alignment on short sentence-initial words** occurs (measured
  share 2.12%); `align_score_min` makes it visible.
- **Channel and speaker concentration**: in the recommended subset the top
  two channels account for 38.2% of the hours, and the top five of the 90
  speakers carry 54.4% of the hours.
- **A channel is not a speaker**: 13 of the 27 channels have more than one
  reader. Speaker identity comes from clustering and is recording-level.
- **A single encoding profile**: sources are ~129 kb/s AAC; the median source
  bandwidth cut is 15.7 kHz, and around 13 kHz on two channels.
- **The test set has not been verified by hand**; the leakage check is
  automatic.
- **2,699 recordings were downloaded and 2,680 produced clips**: one could
  not be decoded, and 18 more yielded no sentence-bounded clip.

## Channel credits

Built from the publicly available recordings of the channels below. Work
using this corpus is expected to carry these credits.

| channel | recordings | clips | hours | recommended hours | speaker clusters |
|---|---|---|---|---|---|
| seslikitaplarmavi | 279 | 332,847 | 580.7 | 539.5 | 2 |
| BirDinle | 235 | 285,797 | 487.9 | 444.8 | 6 |
| dinleyiniz | 83 | 138,254 | 239.4 | 223.2 | 32 |
| sess-Seslikitap | 176 | 149,786 | 226.2 | 199.2 | 4 |
| Peri_Mia | 216 | 132,779 | 206.9 | 80.1 | 1 |
| Pandoramedyaseslikitap | 67 | 112,170 | 193.6 | 91.0 | 1 |
| ZubeyirSener | 99 | 110,294 | 185.6 | 148.5 | 1 |
| ses-arşiv | 234 | 92,190 | 154.6 | 142.6 | 7 |
| cantadakitap | 291 | 74,328 | 126.4 | 111.9 | 1 |
| anahtarca | 175 | 61,242 | 111.7 | 92.5 | 3 |
| kitaplar | 146 | 63,096 | 103.0 | 73.4 | 2 |
| seslikutuphanemkanali | 50 | 45,723 | 77.9 | 74.4 | 1 |
| kitapdinle | 33 | 41,540 | 72.0 | 68.6 | 1 |
| idea_stüdyo | 43 | 33,102 | 54.9 | 52.6 | 1 |
| MuratKaraOfficial2021 | 71 | 24,059 | 39.3 | 34.9 | 1 |
| seslimakalem | 182 | 19,144 | 37.5 | 30.9 | 1 |
| SesliKitaPodcast | 41 | 18,232 | 31.1 | 22.7 | 1 |
| seslikitapturkish | 27 | 17,238 | 28.9 | 25.8 | 7 |
| sesli-kitaplar | 44 | 13,255 | 24.5 | 15.3 | 3 |
| eba | 39 | 15,104 | 24.4 | 23.4 | 9 |
| Seslendiriyor | 28 | 14,262 | 24.1 | 20.2 | 7 |
| OkumaSaati | 58 | 14,889 | 22.0 | 21.5 | 1 |
| SESLİKİTAPEVİ | 29 | 13,041 | 21.2 | 8.5 | 1 |
| denizinötesindekisesler | 16 | 7,786 | 14.8 | 13.4 | 1 |
| seskitap | 12 | 5,558 | 9.1 | 8.7 | 2 |
| bizimkütüphane | 3 | 4,024 | 6.9 | 6.7 | 1 |
| KitaplarinKedisi | 3 | 664 | 1.0 | 1.0 | 2 |
| **total** | **2,680** | **1,840,404** | **3,105.7** | **2,575.2** | **90** |

The speaker column counts the distinct clusters heard on each channel, so
it adds up to more than 90: a cluster can appear on several channels — the
same reader published by more than one of them. The hours columns are
rounded per channel and add up to 3,105.6 / 2,575.3.

## Rights, use and removal

**No dataset license is declared.** Public availability of the source uploads
alone does not establish permission to redistribute their audio or literary
texts. This card does not grant rights held by recording, text or voice rights
holders, and does not establish permission for commercial use or voice cloning.
Licenses for code, derived annotations and underlying recordings must be
specified separately once the applicable rights have been documented.

Credit the dataset and the source channels in the table above. Attribution and
an access acknowledgment do not substitute for a redistribution license or
narrator consent. The Hugging Face access conditions apply separately.

Rights holders and narrators can request removal through an issue in the code
repository or a discussion on the dataset page. The stated procedure is to
remove the affected channel's recordings; the release should additionally
record affected clip IDs and dataset revisions. Source-by-source permission
records and versioned removal records are not supplied in this repository.

## Personal and sensitive information

The audio is human speech, so it carries identifiable voices: 90 speaker
clusters read these recordings. `speaker_id` is a cluster derived from
speaker embeddings, **not a name** — no identity, contact or demographic
information is published, and no attempt was made to link a cluster to a
person. The material is read literature from public uploads rather than
private conversation, but that does not rule out personal or sensitive information in the text;
the transcripts were not screened for it by hand. Requests to remove a voice are handled the same way as rights
holder requests below.

## Citation

Serdar İlder Çağlar — ORCID
[0000-0002-5776-2431](https://orcid.org/0000-0002-5776-2431)

```bibtex
@misc{kiraat2026,
  title  = {KIRAAT: A Sentence-Aligned Turkish Read-Speech Corpus},
  author = {Serdar {\.I}lder {\c{C}}a{\u{g}}lar},
  orcid  = {0000-0002-5776-2431},
  year   = {2026},
  url    = {https://github.com/serdarildercaglar/kiraat},
  note   = {ORCID: https://orcid.org/0000-0002-5776-2431}
}
```
