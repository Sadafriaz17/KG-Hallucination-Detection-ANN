# Source Verification Agent — Implementation Report

> **Historical implementation report.** This report documents the initial
> source-agent implementation and its original 31-test baseline. The agent has
> since received focused batch/matching fixes, and the factual agent and
> dataset audit are now implemented. See
> [`dataset/MEMBER1_REAUDIT.md`](dataset/MEMBER1_REAUDIT.md) and the current
> [source-agent guide](agents/source_verification/AGENT_README.md).

**Project:** Multi-Agent Knowledge Graph Hallucination Detection Using an ANN  
**Component:** Source Verification Agent (Member 1)  
**Implementation date:** 2026-11-25  
**Status:** ✅ Complete — 31/31 tests passing

---

## 1. Files Created or Modified

| File | Action | Description |
|------|--------|-------------|
| `agents/source_verification/source_agent.py` | **Replaced** (was placeholder) | Full agent implementation |
| `agents/source_verification/__init__.py` | **Updated** | Exports `SourceVerificationAgent`, `SourceVerificationResult` |
| `agents/source_verification/AGENT_README.md` | **Created** | Usage guide |
| `utils/data_loader.py` | **Updated** (stubs → implementations) | `load_triples`, `load_ground_truth`, `load_source_document`, `list_source_document_ids` |
| `tests/test_source_agent.py` | **Created** | 31 tests across 7 test classes |
| `tests/conftest.py` | **Created** | Pytest path setup |
| `outputs/source_verification/.gitkeep` | **Created** | Tracks empty output directory in git |
| `outputs/source_verification/full_dataset_results.json` | **Created** | Sample output: all 80 triples processed |
| `requirements.txt` | **Updated** | Added clarification note (no new packages needed) |

**Files NOT modified:**
- `dataset/triples.csv` ✅ Unchanged
- `dataset/ground_truth.csv` ✅ Unchanged
- `config/config.py` ✅ Unchanged (all constants already correct)
- `agents/factual_verification/` ✅ Unchanged (not in scope)

---

## 2. Architecture

### 2.1 SourceVerificationResult (dataclass)

```
triple_id          str    — identifies the triple
verdict            str    — SUPPORTED | CONTRADICTED | NOT_MENTIONED
confidence         float  — [0.0, 1.0] reflects source evidence strength
evidence           str    — verbatim sentence from document, or ""
explanation        str    — natural-language justification
source_document_id str    — document that was read
```

Serialises to JSON via `.to_dict()` / `.to_json()`.

### 2.2 Algorithm

The agent uses **keyword-based sentence retrieval** (stdlib only, no external packages):

```
1.  Validate triple structure.
2.  Load full source document from disk.
3.  Filter out preamble/metadata lines.
4.  Split remaining text into sentences.
5.  Score each sentence:
      +2.0  subject appears in sentence
      +1.0  per relation-term that appears
6.  Keep sentences scoring ≥ 3.0 (requires BOTH subject AND relation match).
7.  Verdict:
      object found in relevant sentence  → SUPPORTED  (0.95 / 0.80)
      relevant sentences, object absent  → CONTRADICTED (0.90)
      no relevant sentences              → NOT_MENTIONED (0.80)
```

The minimum-score threshold of **3.0** is the key design decision: requiring both subject (score +2) and at least one relation term (score +1) prevents false positives where a sentence about Pakistan's *capital* is mistakenly used as evidence for a *largest-city* query.

### 2.3 Preamble filtering

Source documents contain header lines like:
```
CURATED SOURCE EXCERPT: Pakistan
Dataset document ID: source_01
```

These are stripped before scoring. Twelve known prefix patterns are listed in `_PREAMBLE_PREFIXES`. This ensures metadata lines cannot be returned as evidence sentences.

### 2.4 Batch processing

`run_batch()` processes triples sequentially. Any triple that raises an exception is caught and recorded with:
- `verdict = "NOT_MENTIONED"` (conservative fallback)
- `confidence = 0.0`
- `explanation` prefixed with `[AGENT ERROR]`

The batch never aborts early.

---

## 3. Test Results

```
======================== 31 passed, 1 warning in 0.27s ========================
```

| Test class | Cases | Result |
|------------|-------|--------|
| `TestSupported` | TC-01, TC-02, + 2 extra | ✅ 4/4 |
| `TestContradicted` | TC-03, TC-04, + 2 extra | ✅ 4/4 |
| `TestNotMentioned` | TC-05, + 3 extra | ✅ 4/4 |
| `TestEmptySourceText` | TC-06, + 1 extra | ✅ 2/2 |
| `TestMissingDocument` | TC-07, + batch variant | ✅ 2/2 |
| `TestMalformedTriple` | TC-08, + 4 edge cases | ✅ 5/5 |
| `TestBatchRun` | TC-09, + all-countries | ✅ 2/2 |
| `TestDataLoaderIntegration` | 5 integration tests | ✅ 5/5 |
| `TestOutputFormat` | 3 format checks | ✅ 3/3 |
| **Total** | | **31/31** |

---

## 4. Sample Output on Full Dataset

```
Processed : 80 triples
  CONTRADICTED   : 20
  NOT_MENTIONED  : 40
  SUPPORTED      : 20
```

This matches the dataset design exactly:
- 20 correct (Capital/Currency) → SUPPORTED
- 20 incorrect (Capital/Currency) → CONTRADICTED
- 40 not in source (Largest city, Continent, Most popular food, Friendliest city) → NOT_MENTIONED

Full results saved to: `outputs/source_verification/full_dataset_results.json`

---

## 5. Bugs Found and Fixed During Implementation

| # | Bug | Root cause | Fix |
|---|-----|-----------|-----|
| 1 | NOT_MENTIONED triples returned CONTRADICTED | Header line `"CURATED SOURCE EXCERPT: Pakistan"` matched subject "Pakistan" at score 2.0 | Added `_PREAMBLE_PREFIXES` filter to strip metadata lines before scoring |
| 2 | Sentences about one relation matching another | Score threshold of 2.0 allowed subject-only matches | Raised `min_score` to 3.0 — requires subject AND at least one relation term |
| 3 | Batch tests failing with `TypeError` | Test helper `_make_triple()` defined with keyword-only args (`*`) but called positionally | Changed tests to use keyword arguments in batch call sites |

---

## 6. Design Decisions

| Decision | Rationale |
|----------|-----------|
| Stdlib only (no `transformers`, `rank_bm25`) | Keeps dependencies minimal at this stage; sufficient for pilot dataset |
| `source_text` field not used for verdict | Preserves agent independence; `source_text` is a retrieval aid, not an answer |
| `ground_truth.csv` never read | Required by architecture; agent must be independent |
| Minimum score = 3.0 | Prevents cross-relation false positives proven by test failures |
| Score +2 for subject, +1 per relation term | Subject specificity is more important than relation keyword coverage |
| Confidence values fixed (not computed) | Appropriate for pilot; can be replaced with similarity scores later |
| `_PREAMBLE_PREFIXES` tuple | Allows easy extension as new document formats are added |

---

## 7. Known Limitations

| Limitation | Impact | Mitigation path |
|------------|--------|----------------|
| Keyword matching, no semantics | May miss paraphrased claims | Replace `_find_relevant_sentences` with BM25 or dense retrieval |
| No negation handling | "X is NOT the capital" would be treated as SUPPORTED | Add negation detection (e.g., `not`, `never`, `isn't`) |
| Fixed confidence values | Cannot distinguish weak vs. strong evidence at the same level | Compute sentence similarity scores (e.g., TF-IDF cosine) |
| Preamble patterns hard-coded | Will not catch all metadata formats | Make `_PREAMBLE_PREFIXES` configurable via `config.py` |
| Sequential batch processing | Slow on large datasets | Add multiprocessing via `concurrent.futures` |

---

## 8. Next Steps

1. **Factual Verification Agent** (Member 1) — verify triples against external knowledge bases independently of the source document.
2. **Ground-truth label preparation** (Member 1) — combine Source Verification + Factual Verification verdicts into final labels per the classification schema.
3. **Graph Consistency Agent** (Member 2) — check for logical consistency within the full KG.
4. **Feature extraction** (Member 2) — combine all three agent verdicts + confidence scores into ANN feature vectors.

---

*Report generated: 2026-11-25*

