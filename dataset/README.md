# KG Hallucination Detection ANN — Pilot Dataset

This archive contains a small, ready-to-load prototype dataset for the project.

## Contents
- `source_documents/source_01.txt` ... `source_10.txt`: curated source excerpts.
- `triples.csv`: 80 candidate triples, 7 columns.
- `ground_truth.csv`: provisional labels and verification-reference URLs.
- `metadata/dataset_card.md`: scope, label definitions, limitations, and review guidance.

## Quick start
1. Extract this ZIP into your repository's `dataset/` directory, or copy its contents into the existing `dataset/` folder.
2. Check that the `source_document_id` in each CSV row matches a source filename (without `.txt`).
3. Review every row in `ground_truth.csv`; labels are provisional.
4. Do not train the ANN until the team has agreed on the shared agent-output schema and reviewed the data.

## Current label distribution
After the 2026-11-25 re-audit:

| Label | Rows |
|---|---:|
| `SOURCE_SUPPORTED` | 20 |
| `TRUE_BUT_SOURCE_UNSUPPORTED` | 18 |
| `FACTUALLY_INCORRECT` | 22 |
| `INSUFFICIENT_EVIDENCE` | 20 |

The changes from the previous balanced distribution are documented in
[`MEMBER1_REAUDIT.md`](./MEMBER1_REAUDIT.md): T0203 and T0903 are now
`FACTUALLY_INCORRECT` under an explicitly defined urban-area measure.

## Important
This is a pilot for pipeline development, not a validated research benchmark.
The source files are curated summaries, not full copies of the linked articles.
City-size labels use the archived Factbook's 2023 `Major urban areas - population`
field and must not be interpreted as universal city-proper or metropolitan-area
rankings. See [`metadata/dataset_card.md`](./metadata/dataset_card.md) and
[`MEMBER1_REAUDIT.md`](./MEMBER1_REAUDIT.md).
