# Octavia Translation Evaluation Pipeline

A lightweight, reproducible pipeline that evaluates translation quality before release. Given a source text and its translation, the pipeline computes length-ratio metrics and a BLEU score per segment, then produces a structured JSON report with a deterministic `PASS` / `FAIL` decision.

Designed to act as a release gate in any CI/CD workflow — exit code `0` means safe to release, exit code `1` blocks it.

---

## Architecture

```
┌─────────────┐     ┌──────────────────┐
│  source.txt │     │  translation.txt │
└──────┬──────┘     └────────┬─────────┘
       │                     │
       └──────────┬───────────┘
                  │
           ┌──────▼──────┐
           │   loader    │  validates segment count, encoding, empty lines
           └──────┬──────┘
                  │
         ┌────────┴────────┐
         │                 │
  ┌──────▼──────┐   ┌──────▼──────┐
  │   length    │   │    BLEU     │
  │   ratio     │   │   score     │
  │   metrics   │   │ (sacrebleu) │
  └──────┬──────┘   └──────┬──────┘
         │                 │
         └────────┬────────┘
                  │
           ┌──────▼──────┐
           │  thresholds │  evaluates checks against config.json
           └──────┬──────┘
                  │
           ┌──────▼──────┐
           │   reporter  │  writes report.json + prints terminal summary
           └──────┬──────┘
                  │
         ┌────────┴────────┐
         │                 │
    report.json      PASS / FAIL
                    (exit code 0/1)
```

---

## Module Responsibilities

```
evaluator/
├── loader.py       reads and validates segment files
├── metrics.py      computes length ratios and BLEU score
├── models.py       typed frozen dataclasses (Thresholds, LengthMetrics,
│                   CheckResults, SegmentResult, EvaluationResult)
├── thresholds.py   applies threshold logic, returns CheckResults
└── reporter.py     serializes EvaluationResult to JSON and terminal output
```

Each module has a single responsibility and communicates through typed dataclasses defined in `models.py`. No raw dictionaries cross module boundaries.

---

## Setup

### Docker

```bash
docker build -t evaluator .
docker run evaluator
```

To use custom input files and retrieve the report on the host:

```bash
docker run --rm \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/reports:/app/reports \
  evaluator \
  python evaluate.py --source data/source.txt --translation data/translation.txt
```

### Local Python 3.10+

```bash
pip install -r requirements.txt
python evaluate.py
```

### Make

```bash
make install
make run
```

---

## CLI

```
python evaluate.py [--source PATH] [--translation PATH]
                   [--output PATH] [--config PATH] [--lang-pair PAIR]
```

| Flag | Default | Description |
|---|---|---|
| `--source` | `data/source.txt` | Source text file, one segment per line |
| `--translation` | `data/translation.txt` | Translated text file, one segment per line |
| `--output` | `reports/report.json` | Output path for the JSON report |
| `--config` | built-in defaults | JSON file to override threshold values |
| `--lang-pair` | `en-es` | Language pair label recorded in the report |

---

## Metrics

### Length Ratio

```
length_ratio = len(translated_segment) / len(source_segment)
```

Computed per segment at the character level. Aggregated into average ratio, violation count, and violation percentage.

Character-level length ratio is the standard proxy for synchronization risk in video dubbing systems. A translated segment significantly longer than its source will cause audio/video desynchronization in the Text-to-Speech → Sync → Merge stages of the Octavia pipeline.

### BLEU Score

BLEU (Bilingual Evaluation Understudy) measures n-gram precision between a hypothesis and a reference translation. Computed via [sacrebleu](https://github.com/mjpost/sacrebleu) with `effective_order=True`.

Selected because it is language-agnostic, deterministic, requires no pre-trained model or GPU, and is the standard metric for automated MT regression testing.

**Note on references:** BLEU requires human reference translations. This dataset provides none, so the source English text serves as a pseudo-reference. Cross-lingual n-gram overlap is minimal by nature, producing low scores regardless of translation quality. The threshold of 25.0 accounts for this. In production, provide actual reference translations per language pair and recalibrate the threshold accordingly.

---

## Thresholds

Defined in `config.json` and loaded into a typed `Thresholds` dataclass at runtime.

| Key | Default | Rationale |
|---|---|---|
| `max_average_length_ratio` | `1.2` | Spanish averages 20–30% more characters than English. A mean ratio above 1.2 signals systemic over-translation that will cause sync failures at scale. |
| `max_violation_percentage` | `10.0` | Tolerates up to 1 in 10 segments as natural outliers. Beyond that, the pattern is systemic. |
| `min_bleu_score` | `25.0` | Conservative floor for pseudo-reference evaluation. Raise when true reference translations are available. |

Override any threshold without modifying source code:

```bash
python evaluate.py --config config.json
```

---

## Output

### Terminal

```
============================================================
  Octavia Translation Evaluation Pipeline
============================================================
  Language pair           : en-es
  Generated at            : 2026-03-17T10:16:26.432018+00:00
============================================================
  Segments evaluated      : 10
  Average length ratio    : 1.2485
  Length violations       : 8 (80.0%)
  BLEU score              : 0.8101
============================================================
  CHECK RESULTS
  avg_length_ratio_ok     : FAIL
  violation_rate_ok       : FAIL
  bleu_ok                 : FAIL
============================================================
  FINAL DECISION: FAIL
============================================================
```

### JSON Report

```json
{
  "pipeline": "Octavia Translation Evaluation Pipeline",
  "generated_at": "2026-03-17T10:16:26.432018+00:00",
  "language_pair": "en-es",
  "summary": {
    "total_segments": 10,
    "average_length_ratio": 1.2485,
    "violation_count": 8,
    "violation_percentage": 80.0,
    "bleu_score": 0.8101,
    "decision": "FAIL"
  },
  "thresholds": { ... },
  "checks": { ... },
  "segments": [ ... ]
}
```

Full example at `reports/report.json`.

---

## Exit Codes

| Code | Meaning |
|---|---|
| `0` | All checks passed — safe to release |
| `1` | One or more checks failed, or a runtime error occurred |

### CI/CD Integration

A GitHub Actions workflow is included at `.github/workflows/evaluate.yml`. It triggers on every push and pull request to `main`, runs the evaluation, and uploads `reports/report.json` as a build artifact.

To integrate into an existing pipeline:

```yaml
- name: Evaluate translation quality
  run: python evaluate.py --source data/source.txt --translation data/translation.txt
```

The non-zero exit code on failure will automatically block the pipeline step.

---

## Requirements

- Python 3.10+
- sacrebleu 2.4.3
- No internet access required at runtime
- No GPU required
- Docker (optional)