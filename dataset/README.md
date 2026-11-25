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

## Label distribution
There are 20 rows per label (5? No: 2 rows per country × 10 countries = 20 rows per label).

## Important
This is a pilot for pipeline development, not a validated research benchmark. The source excerpts are intentionally short and some labels require review. See `metadata/dataset_card.md`.
