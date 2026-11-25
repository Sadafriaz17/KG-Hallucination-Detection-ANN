# Dataset Card

## Name
Small Country-Facts KG Hallucination Detection Pilot Dataset

## Purpose
A teaching/research prototype for testing the data pipeline of a multi-agent KG
verification project. It contains 10 short country source excerpts and 80 candidate
triples (8 per country).

## Labels
- `SOURCE_SUPPORTED`: claim is explicitly stated in the supplied source excerpt and is factually true.
- `TRUE_BUT_SOURCE_UNSUPPORTED`: claim is intended to be true but is absent from the supplied excerpt.
- `FACTUALLY_INCORRECT`: claim is contradicted by the supplied excerpt and is factually false.
- `INSUFFICIENT_EVIDENCE`: claim is subjective or lacks a defined, verifiable criterion.

## Critical limitations
1. This is a small pilot dataset, not a benchmark and not evidence of generalization.
2. The source files are curated summaries/excerpts, not full article downloads or verbatim quotations.
3. The largest-city facts can depend on city-proper versus metropolitan/urban-area definitions. Verify the definition and current reference before treating these rows as gold labels.
4. `Continent` rows are intended to be true geographic facts omitted from the short source excerpts. Verify each row against an independent geographic reference before final experiments.
5. Subjective rows (`Most popular food`, `Friendliest city`) are deliberately assigned `INSUFFICIENT_EVIDENCE`; they test abstention, not factual falsehood.
6. The CIA World Factbook URL is supplied as a reference starting point. The Factbook's publication status and URL availability may change; check the page and replace with a currently accessible authoritative source if needed.
7. Ground-truth labels are provisional and require independent human review. Do not describe them as expert-validated.
8. For a publication-quality dataset, record access dates, preserve exact excerpts with page/section information, and have a second reviewer independently adjudicate labels.

## Recommended use
Use this archive to test CSV loading, source-document lookup, schema integration, and basic agent plumbing. Before model training, replace questionable rows and validate every fact/reference.
