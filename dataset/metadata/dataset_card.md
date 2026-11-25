# Dataset Card

## Name
Small Country-Facts KG Hallucination Detection Pilot Dataset

## Purpose
A teaching/research prototype for testing the data pipeline of a multi-agent KG
verification project. It contains 10 short country source excerpts and 80 candidate
triples (8 per country).

## Labels
- `SOURCE_SUPPORTED`: the local source excerpt explicitly states the claim, and the audited external reference corroborates it.
- `TRUE_BUT_SOURCE_UNSUPPORTED`: the claim is true under the documented data convention but absent from the supplied source excerpt.
- `FACTUALLY_INCORRECT`: audited external evidence contradicts the claim; the source excerpt may or may not mention the relation.
- `INSUFFICIENT_EVIDENCE`: the claim has no sufficiently defined, verifiable answer from the available evidence.

## Critical limitations
1. This is a small pilot dataset, not a benchmark and not evidence of generalization.
2. The source files are manually curated summaries. Their sentences are not verified verbatim quotations from the linked Wikipedia pages, and the Source Verification Agent reads only these local files.
3. `Largest city` is operationalized as the first entry in the CIA World Factbook's `Major urban areas - population` field (2023 estimates), using the 2025-labelled edition snapshot preserved by a third-party archive. This is not a city-proper or standardized metropolitan-area definition. Under this measure T0203 (India—Mumbai) and T0903 (Australia—Sydney) are `FACTUALLY_INCORRECT`; the other eight city claims remain `TRUE_BUT_SOURCE_UNSUPPORTED`. See the row-level evidence in `ground_truth.csv`.
4. `Continent` uses the seven-continent model and means the country's principal territory; overseas territories are not used to assign a different continent. This convention is relevant for France and other geographically dispersed states.
5. Subjective rows (`Most popular food`, `Friendliest city`) remain `INSUFFICIENT_EVIDENCE`; they test abstention, not factual falsehood.
6. The CIA officially announced that the World Factbook had sunset on February 4, 2026. `ground_truth.csv` and `metadata/source_references.csv` now link to a third-party archive of its 2025-labelled edition (snapshot captured January 22, 2026); it is not a current CIA service.
7. Ground-truth labels were rechecked against local source text and archived country profiles, but remain pilot annotations—not expert validation or a publication-quality benchmark.
8. For publication-quality use, obtain independently archived authoritative sources, record access dates and page/section evidence, standardize geographic definitions, and have a second reviewer adjudicate all labels.

## Recommended use
Use this dataset to test CSV loading, source-document lookup, schema compatibility,
and agent plumbing. Do not claim research-quality ANN performance from this
80-triple pilot. See `MEMBER1_REAUDIT.md` for the label changes and evidence
limitations.
