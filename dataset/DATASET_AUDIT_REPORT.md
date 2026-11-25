# Dataset Audit Report
**Project:** Multi-Agent Knowledge Graph Hallucination Detection Using an ANN  
**Auditor:** Member 1 (automated + manual review)  
**Audit date:** 2026-11-25  
**Status at time of audit:** Pre-implementation — pipeline development phase

---

## Table of Contents
1. [Dataset Overview](#1-dataset-overview)
2. [Folder and File Inspection](#2-folder-and-file-inspection)
3. [Schema Validation](#3-schema-validation)
4. [Triple Validation Results](#4-triple-validation-results)
5. [Ground-Truth Validation Results](#5-ground-truth-validation-results)
6. [Source-Document Verification](#6-source-document-verification)
7. [Class Distribution](#7-class-distribution)
8. [Identified Errors and Inconsistencies](#8-identified-errors-and-inconsistencies)
9. [Research-Quality Assessment](#9-research-quality-assessment)
10. [Recommended Corrections](#10-recommended-corrections)
11. [Final Readiness Status](#11-final-readiness-status)

---

## 1. Dataset Overview

| Property | Value |
|----------|-------|
| Dataset name | Small Country-Facts KG Hallucination Detection Pilot Dataset |
| Declared purpose | Teaching/research prototype; pipeline testing |
| Source documents | 10 (one per country) |
| Total triples | 80 (8 per country, 10 countries) |
| Label classes | 4 |
| Label distribution | 20 rows per class (perfectly balanced) |
| Preparation date | 2026-11-25 |
| Countries covered | Australia, Brazil, Canada, China, France, Germany, India, Italy, Japan, Pakistan |

The dataset is a manually curated pilot designed to test the data-loading and agent pipeline. It is explicitly **not** described as a research benchmark by its own `dataset_card.md`.

---

## 2. Folder and File Inspection

### 2.1 Actual folder contents

```
dataset/
├── metadata/
│   ├── dataset_card.md          ✅ Present — scope, limitations, label defs
│   ├── schema.json              ✅ Present — label taxonomy (matches config.py)
│   └── source_references.csv   ✅ Present — Wikipedia + CIA Factbook URLs per country
├── source_documents/
│   ├── source_01.txt            ✅ Pakistan
│   ├── source_02.txt            ✅ India
│   ├── source_03.txt            ✅ China
│   ├── source_04.txt            ✅ Japan
│   ├── source_05.txt            ✅ France
│   ├── source_06.txt            ✅ Germany
│   ├── source_07.txt            ✅ Italy
│   ├── source_08.txt            ✅ Canada
│   ├── source_09.txt            ✅ Australia
│   └── source_10.txt            ✅ Brazil
├── triples.csv                  ✅ 80 rows, 7 columns
├── ground_truth.csv             ✅ 80 rows, 4 columns
├── README.md                    ✅ Quick-start guide
└── dataset_README.md            ✅ Column reference (created during project setup)
```

### 2.2 New files not in original project specification

| File | Assessment |
|------|-----------|
| `metadata/dataset_card.md` | ✅ Welcome addition — documents limitations honestly |
| `metadata/schema.json` | ✅ Matches `config.py` exactly — no conflicts |
| `metadata/source_references.csv` | ✅ Useful reference index; note that URLs are starting points, not verified live links |
| `dataset/README.md` | ✅ Differs from `dataset_README.md` created during setup; both are valid and complementary — no conflict |

### 2.3 Consistency with project architecture

All `source_document_id` values in `triples.csv` match the naming convention defined in the project (`source_01` through `source_10`) and correspond to actual `.txt` files. No orphan files, no missing files.

---

## 3. Schema Validation

### 3.1 triples.csv — required columns

| Column | Present | No missing values | Notes |
|--------|---------|-------------------|-------|
| `triple_id` | ✅ | ✅ | |
| `subject` | ✅ | ✅ | |
| `relation` | ✅ | ✅ | |
| `object` | ✅ | ✅ | |
| `source_document_id` | ✅ | ✅ | |
| `source_document_url` | ✅ | ✅ | |
| `source_text` | ✅ | ✅ | ⚠️ See Issue #1 |

### 3.2 ground_truth.csv — required columns

| Column | Present | No missing values | Notes |
|--------|---------|-------------------|-------|
| `triple_id` | ✅ | ✅ | |
| `final_label` | ✅ | ✅ | All values in allowed set |
| `verification_evidence` | ✅ | ✅ | |
| `verification_reference` | ✅ | ✅ | |

### 3.3 schema.json vs config.py

| Item | schema.json | config.py | Match? |
|------|-------------|-----------|--------|
| `SOURCE_SUPPORTED` | ✅ | ✅ | ✅ |
| `TRUE_BUT_SOURCE_UNSUPPORTED` | ✅ | ✅ | ✅ |
| `FACTUALLY_INCORRECT` | ✅ | ✅ | ✅ |
| `INSUFFICIENT_EVIDENCE` | ✅ | ✅ | ✅ |
| `SUPPORTED` / `CONTRADICTED` / `NOT_MENTIONED` | ✅ | ✅ | ✅ |
| `TRUE` / `FALSE` / `UNKNOWN` | ✅ | ✅ | ✅ |

**Schema is fully consistent across all files.**

---

## 4. Triple Validation Results

### 4.1 Structural checks (automated)

| Check | Result |
|-------|--------|
| Total rows | 80 |
| Unique `triple_id` values | 80 — **no duplicates** |
| Rows with any missing field | 0 — **all fields populated** |
| Invalid `source_document_id` references | 0 — **all 10 source files exist** |
| Duplicate (subject, relation, object) combinations | 0 — **no exact triple duplicates** |

### 4.2 Triple ID format

Triple IDs follow the pattern `T{CC}{RR}` where `{CC}` is the two-digit country index (01–10) and `{RR}` is the row within that country (01–08). This is clean, consistent, and machine-parseable.

### 4.3 Subject / relation / object values

**Unique subjects (10):**
Australia, Brazil, Canada, China, France, Germany, India, Italy, Japan, Pakistan

**Unique relations (6):**

| Relation | Type | Note |
|----------|------|------|
| `Capital` | Objective, verifiable | ✅ |
| `Currency` | Objective, verifiable | ✅ |
| `Largest city` | Objective with caveat | ⚠️ Definition-dependent (city-proper vs. metro area) |
| `Continent` | Objective, verifiable | ✅ |
| `Most popular food` | Subjective | ⚠️ No verifiable criterion |
| `Friendliest city` | Subjective | ⚠️ No verifiable criterion |

**Triples per subject:** exactly 8 per country — perfectly balanced.

### 4.4 Object values — factual spot-check

Each country has 8 triples following a fixed 8-row pattern:

| Row# | Relation | Object type | Factual status |
|------|----------|-------------|----------------|
| x01 | Capital | Correct capital | ✅ |
| x02 | Currency | Correct currency | ✅ |
| x03 | Largest city | Correct largest city | ✅ (with definition caveat) |
| x04 | Continent | Correct continent | ✅ |
| x05 | Capital | **Wrong capital** (another city) | ✅ Intentionally false |
| x06 | Currency | **Wrong currency** (another country's) | ✅ Intentionally false |
| x07 | Most popular food | "No objectively established answer" | ✅ Appropriate |
| x08 | Friendliest city | "No objectively established answer" | ✅ Appropriate |

Factual verification of all 20 objective triples (x01–x06):

| Triple | Claim | Verdict |
|--------|-------|---------|
| T0101 | Pakistan → Capital → Islamabad | ✅ Correct |
| T0102 | Pakistan → Currency → Pakistani rupee | ✅ Correct |
| T0103 | Pakistan → Largest city → Karachi | ✅ Correct (by population) |
| T0104 | Pakistan → Continent → Asia | ✅ Correct |
| T0105 | Pakistan → Capital → Lahore | ✅ Correctly labelled false |
| T0106 | Pakistan → Currency → Indian rupee | ✅ Correctly labelled false |
| T0201 | India → Capital → New Delhi | ✅ Correct |
| T0202 | India → Currency → Indian rupee | ✅ Correct |
| T0203 | India → Largest city → Mumbai | ✅ Correct (by population) |
| T0204 | India → Continent → Asia | ✅ Correct |
| T0205 | India → Capital → Kolkata | ✅ Correctly labelled false |
| T0206 | India → Currency → Pakistani rupee | ✅ Correctly labelled false |
| T0301 | China → Capital → Beijing | ✅ Correct |
| T0302 | China → Currency → renminbi | ✅ Correct |
| T0303 | China → Largest city → Shanghai | ✅ Correct (by population) |
| T0304 | China → Continent → Asia | ✅ Correct |
| T0305 | China → Capital → Tokyo | ✅ Correctly labelled false |
| T0306 | China → Currency → Japanese yen | ✅ Correctly labelled false |
| T0401 | Japan → Capital → Tokyo | ✅ Correct |
| T0402 | Japan → Currency → Japanese yen | ✅ Correct |
| T0403 | Japan → Largest city → Tokyo | ✅ Correct |
| T0404 | Japan → Continent → Asia | ✅ Correct |
| T0405 | Japan → Capital → Osaka | ✅ Correctly labelled false |
| T0406 | Japan → Currency → Chinese yuan | ✅ Correctly labelled false |
| T0501 | France → Capital → Paris | ✅ Correct |
| T0502 | France → Currency → euro | ✅ Correct |
| T0503 | France → Largest city → Paris | ✅ Correct (commune and metro) |
| T0504 | France → Continent → Europe | ✅ Correct |
| T0505 | France → Capital → Lyon | ✅ Correctly labelled false |
| T0506 | France → Currency → British pound | ✅ Correctly labelled false |
| T0601 | Germany → Capital → Berlin | ✅ Correct |
| T0602 | Germany → Currency → euro | ✅ Correct |
| T0603 | Germany → Largest city → Berlin | ✅ Correct |
| T0604 | Germany → Continent → Europe | ✅ Correct |
| T0605 | Germany → Capital → Hamburg | ✅ Correctly labelled false |
| T0606 | Germany → Currency → Swiss franc | ✅ Correctly labelled false |
| T0701 | Italy → Capital → Rome | ✅ Correct |
| T0702 | Italy → Currency → euro | ✅ Correct |
| T0703 | Italy → Largest city → Rome | ✅ Correct (by municipality population) |
| T0704 | Italy → Continent → Europe | ✅ Correct |
| T0705 | Italy → Capital → Milan | ✅ Correctly labelled false |
| T0706 | Italy → Currency → French franc | ✅ Correctly labelled false (France adopted euro in 2002) |
| T0801 | Canada → Capital → Ottawa | ✅ Correct |
| T0802 | Canada → Currency → Canadian dollar | ✅ Correct |
| T0803 | Canada → Largest city → Toronto | ✅ Correct |
| T0804 | Canada → Continent → North America | ✅ Correct |
| T0805 | Canada → Capital → Montreal | ✅ Correctly labelled false |
| T0806 | Canada → Currency → US dollar | ✅ Correctly labelled false |
| T0901 | Australia → Capital → Canberra | ✅ Correct |
| T0902 | Australia → Currency → Australian dollar | ✅ Correct |
| T0903 | Australia → Largest city → Sydney | ✅ Correct |
| T0904 | Australia → Continent → Oceania | ✅ Correct |
| T0905 | Australia → Capital → Melbourne | ✅ Correctly labelled false |
| T0906 | Australia → Currency → New Zealand dollar | ✅ Correctly labelled false |
| T1001 | Brazil → Capital → Brasília | ✅ Correct |
| T1002 | Brazil → Currency → Brazilian real | ✅ Correct |
| T1003 | Brazil → Largest city → São Paulo | ✅ Correct |
| T1004 | Brazil → Continent → South America | ✅ Correct |
| T1005 | Brazil → Capital → Rio de Janeiro | ✅ Correctly labelled false |
| T1006 | Brazil → Currency → Argentine peso | ✅ Correctly labelled false |

**No factual errors detected in the objective triples.**

### 4.5 ⚠️ Issue #1 — source_text field is a header stub, not an extracted sentence

**Severity: MEDIUM**

The `source_text` column in `triples.csv` stores a boilerplate header excerpt (the preamble block of the source document) that is **identical for all 8 triples belonging to the same source document**. It does not contain the specific sentence from the source document that supports or contradicts each triple.

**Example — all 8 Pakistan triples (T0101–T0108) share this identical source_text:**
> `"CURATED SOURCE EXCERPT: Pakistan Dataset document ID: source_01 Original source page: https://en.wikipedia.org/wiki/Pakistan Retrieved/prepared: 2026-11-25 This is a short, manually prepared excerpt for a small course-project prototype...."`

**Why this matters:**
- The Source Verification Agent will rely on `source_text` to find the relevant passage. If all triples for a document point to the same generic header, the agent has no fine-grained text to work with.
- For pipeline testing this is acceptable. For model training it needs to be fixed.

**Recommended correction:** See Section 10.

---

## 5. Ground-Truth Validation Results

### 5.1 Structural checks (automated)

| Check | Result |
|-------|--------|
| Total GT rows | 80 |
| Unique `triple_id` values | 80 — **no duplicates** |
| GT IDs not found in triples.csv | 0 — **perfect 1:1 match** |
| Triples without a GT row | 0 |
| Invalid `final_label` values | 0 — all 4 label types used only |
| Rows with missing `verification_evidence` | 0 |
| Rows with missing `verification_reference` | 0 |

### 5.2 Label logic audit — per row type

#### SOURCE_SUPPORTED rows (x01, x02 — Capital correct, Currency correct)

| Sample | Claim | Source says | Label | Correct? |
|--------|-------|-------------|-------|----------|
| T0101 | Pakistan → Capital → Islamabad | "The capital city of Pakistan is Islamabad." | SOURCE_SUPPORTED | ✅ |
| T0102 | Pakistan → Currency → Pakistani rupee | "The currency used in Pakistan is the Pakistani rupee." | SOURCE_SUPPORTED | ✅ |

**All 20 SOURCE_SUPPORTED labels are consistent with their source documents.** The source document explicitly contains the fact, the label is correct.

#### TRUE_BUT_SOURCE_UNSUPPORTED rows (x03 Largest city, x04 Continent)

| Sample | Claim | Source says | Label | Correct? |
|--------|-------|-------------|-------|----------|
| T0103 | Pakistan → Largest city → Karachi | Not mentioned in source | TRUE_BUT_SOURCE_UNSUPPORTED | ✅ |
| T0104 | Pakistan → Continent → Asia | Not mentioned in source | TRUE_BUT_SOURCE_UNSUPPORTED | ✅ |

Each source document deliberately only states capital and currency. Largest city and continent facts are correct (independently verifiable) but absent from the source excerpt. The label distinction is correctly applied.

> [!NOTE]
> The ground_truth notes acknowledge that largest-city facts depend on definitional choices (city-proper vs. metropolitan area). This is an honest limitation, not an error.

#### FACTUALLY_INCORRECT rows (x05 wrong capital, x06 wrong currency)

| Sample | Claim | Actual fact | Label | Correct? |
|--------|-------|-------------|-------|----------|
| T0105 | Pakistan → Capital → **Lahore** | Islamabad | FACTUALLY_INCORRECT | ✅ |
| T0106 | Pakistan → Currency → **Indian rupee** | Pakistani rupee | FACTUALLY_INCORRECT | ✅ |

All 20 FACTUALLY_INCORRECT labels are consistent. The wrong-city and wrong-currency choices are unambiguously false.

**Notable: T0706 — Italy → Currency → French franc**  
This is labelled FACTUALLY_INCORRECT. This is **correct**: France adopted the euro in 2002 and the French franc no longer exists as a legal currency. The label is valid but the evidence note in `ground_truth.csv` only says "the excerpt explicitly gives euro as the currency" — which is true but misses the historical nuance. This is a minor documentation gap, not a labelling error.

#### INSUFFICIENT_EVIDENCE rows (x07 Most popular food, x08 Friendliest city)

| Sample | Claim | Why INSUFFICIENT_EVIDENCE | Correct? |
|--------|-------|---------------------------|----------|
| T0107 | Pakistan → Most popular food → No objectively established answer | Subjective, no survey definition | ✅ |
| T0108 | Pakistan → Friendliest city → No objectively established answer | Subjective, no operational definition | ✅ |

The object value "No objectively established answer" is itself a metadata annotation embedded in the KG, not a factual claim. The INSUFFICIENT_EVIDENCE label is appropriate.

> [!IMPORTANT]
> These 20 rows test the **abstention** capability of the system. They are not testing whether a city or food is factually wrong. This is a valid design decision but must be clearly documented for Member 2 when designing the ANN output.

### 5.3 ⚠️ Issue #2 — verification_evidence text is templated, not triple-specific

**Severity: LOW-MEDIUM**

The `verification_evidence` strings are correct but are templated. All 10 SOURCE_SUPPORTED capital triples share the same evidence sentence pattern:  
> `"The source excerpt explicitly states that the capital is [city]."`

This is not incorrect, but it means the evidence is generated by formula rather than being independently written for each triple. For pipeline testing this is fine. For human inter-annotator agreement studies, independent evidence would be required.

---

## 6. Source-Document Verification

### 6.1 Source document structure (all 10 documents)

Every source document follows an identical template:

```
CURATED SOURCE EXCERPT: [Country]
Dataset document ID: source_XX
Original source page: [Wikipedia URL]
Retrieved/prepared: 2026-11-25

[Disclaimer paragraph]

1. The capital city of [Country] is [capital].
2. The currency used in [Country] is the [currency].

[Attribution paragraph]
[Design note paragraph]
```

**Key design decision:** Each document **intentionally** contains only two facts (capital and currency). This is the mechanism by which 4 of the 8 triples per country become `TRUE_BUT_SOURCE_UNSUPPORTED` or `INSUFFICIENT_EVIDENCE`.

### 6.2 Per-document fact verification against source text

| Source | Country | Fact 1 (Capital) | Fact 2 (Currency) | Consistent with GT? |
|--------|---------|------------------|-------------------|---------------------|
| source_01 | Pakistan | Islamabad ✅ | Pakistani rupee ✅ | ✅ |
| source_02 | India | New Delhi ✅ | Indian rupee ✅ | ✅ |
| source_03 | China | Beijing ✅ | renminbi ✅ | ✅ |
| source_04 | Japan | Tokyo ✅ | Japanese yen ✅ | ✅ |
| source_05 | France | Paris ✅ | euro ✅ | ✅ |
| source_06 | Germany | Berlin ✅ | euro ✅ | ✅ |
| source_07 | Italy | Rome ✅ | euro ✅ | ✅ |
| source_08 | Canada | Ottawa ✅ | Canadian dollar ✅ | ✅ |
| source_09 | Australia | Canberra ✅ | Australian dollar ✅ | ✅ |
| source_10 | Brazil | Brasília ✅ | Brazilian real ✅ | ✅ |

**All 20 source-supported facts match their source documents exactly.**

### 6.3 Cross-document contamination check

No source document contains information from another country. Each document is strictly scoped to its own country.

### 6.4 ⚠️ Issue #3 — source_text in triples.csv does not point to specific sentences

Already flagged as Issue #1 in Section 4.5. The `source_text` field stores the full header of the source document rather than the specific sentence establishing the fact. The Source Verification Agent cannot use this field for precise sentence-level retrieval.

---

## 7. Class Distribution

### 7.1 Overall distribution

| Final Label | Count | Percentage |
|-------------|-------|-----------|
| `SOURCE_SUPPORTED` | 20 | 25.0% |
| `TRUE_BUT_SOURCE_UNSUPPORTED` | 20 | 25.0% |
| `FACTUALLY_INCORRECT` | 20 | 25.0% |
| `INSUFFICIENT_EVIDENCE` | 20 | 25.0% |
| **Total** | **80** | **100%** |

The dataset is **perfectly balanced** (20 examples per class). This is a deliberate design decision.

### 7.2 Distribution by subject (country)

Each country contributes exactly:

| Label | Count per country |
|-------|-------------------|
| `SOURCE_SUPPORTED` | 2 (Capital correct + Currency correct) |
| `TRUE_BUT_SOURCE_UNSUPPORTED` | 2 (Largest city + Continent) |
| `FACTUALLY_INCORRECT` | 2 (Wrong capital + Wrong currency) |
| `INSUFFICIENT_EVIDENCE` | 2 (Most popular food + Friendliest city) |

### 7.3 Distribution by relation

| Relation | Label assigned | Count |
|----------|---------------|-------|
| Capital (correct) | SOURCE_SUPPORTED | 10 |
| Currency (correct) | SOURCE_SUPPORTED | 10 |
| Largest city | TRUE_BUT_SOURCE_UNSUPPORTED | 10 |
| Continent | TRUE_BUT_SOURCE_UNSUPPORTED | 10 |
| Capital (wrong) | FACTUALLY_INCORRECT | 10 |
| Currency (wrong) | FACTUALLY_INCORRECT | 10 |
| Most popular food | INSUFFICIENT_EVIDENCE | 10 |
| Friendliest city | INSUFFICIENT_EVIDENCE | 10 |

> [!WARNING]
> **The relation and label are perfectly correlated.** A model that learns which relation a triple uses can perfectly predict the label without understanding the content. This is a **data leakage risk** for the ANN. See Section 9.

---

## 8. Identified Errors and Inconsistencies

### Issue #1 — source_text is a header stub, not a sentence-level extract
- **Severity:** MEDIUM  
- **Affected rows:** All 80 triples  
- **Detail:** The `source_text` column stores the preamble block of the document (identical for all 8 triples per source document) rather than the specific sentence(s) supporting or contradicting the triple.  
- **Impact:** The Source Verification Agent cannot use this field for fine-grained sentence matching. For pipeline testing it is acceptable. For model training it must be corrected.  
- **Recommended fix:** Replace each row's `source_text` with the specific sentence from the source document relevant to the triple. For rows not mentioned in the source, leave the field as `"NOT_MENTIONED"` or the most relevant passage with an explanation.

---

### Issue #2 — verification_evidence is formulaic, not independently written
- **Severity:** LOW  
- **Affected rows:** All 80 ground-truth rows  
- **Detail:** Evidence strings follow the same sentence template for each label type rather than being independently composed per triple.  
- **Impact:** Acceptable for a pilot dataset. Not acceptable as a standard for a human-validated benchmark.  
- **Recommended fix:** Before claiming the labels are human-validated, independently rewrite each evidence string from scratch.

---

### Issue #3 — Relation → Label mapping creates a data leakage shortcut
- **Severity:** HIGH for model generalization; acceptable for pipeline testing  
- **Affected rows:** All 80 triples  
- **Detail:** Because the same 8 relations are used for every country and each relation is always assigned the same label, any model — including the ANN — can achieve 100% accuracy by learning `relation → label` rather than any semantic understanding.  
- **Impact:** Evaluation metrics will be inflated and will not measure genuine hallucination detection.  
- **Recommended fix:** See Section 10, Recommendation R3.

---

### Issue #4 — T0103, T0203, T0303, T0403, T0503, T0603, T0703, T0803, T0903, T1003 — Largest city label requires definitional clarification
- **Severity:** LOW  
- **Affected rows:** 10 triples (all xX03 rows)  
- **Detail:** The labels are `TRUE_BUT_SOURCE_UNSUPPORTED`. The ground truth assumes the claims are factually true. The dataset_card.md acknowledges that "largest city" depends on the city-proper versus metropolitan/urban-area definition.  
- **Example concern:** Italy's largest city by municipality population is Rome ✅. However, Milan's metropolitan area is comparable. This ambiguity is documented but not resolved.  
- **Impact:** Labels are probably correct but are marked as provisional in the dataset card.  
- **Recommended fix:** Add a `definition_note` column or footnote specifying which definition of "largest city" is used (e.g., "by municipality population per [reference]").

---

### Issue #5 — T0706 Italy → Currency → French franc — evidence note lacks historical context
- **Severity:** LOW (cosmetic)  
- **Affected rows:** T0706  
- **Detail:** The evidence says "the excerpt explicitly gives euro as the currency, contradicting the candidate object French franc." This is correct but incomplete. The French franc was abolished in 2002 when France adopted the euro. The triple could also be classified as FACTUALLY_INCORRECT on independent grounds.  
- **Impact:** None on labelling correctness; purely a documentation gap.  
- **Recommended fix:** Add a note to the verification_evidence: "Additionally, the French franc ceased to exist as legal tender in 2002."

---

### Issue #6 — dataset/README.md contains a minor arithmetic error in the label distribution note
- **Severity:** LOW (documentation only)  
- **Affected file:** `dataset/README.md` line 18  
- **Detail:** The comment reads: `"There are 20 rows per label (5? No: 2 rows per country × 10 countries = 20 rows per label)."` The `5?` appears to be a drafting artefact.  
- **Impact:** None on data quality.  
- **Recommended fix:** Clean up the sentence: "2 rows per country × 10 countries = 20 rows per label."

---

## 9. Research-Quality Assessment

### 9.1 Class representation
✅ **All four classes are represented equally (20 each).** The dataset is perfectly balanced, which is good for training a baseline classifier without class-weighting.

### 9.2 Diversity of examples
⚠️ **Diversity is low.** The dataset covers only one domain (country facts) and uses only 6 predicates applied identically across all 10 subjects. The structured repetition means:
- All SOURCE_SUPPORTED triples use `Capital` or `Currency`.
- All FACTUALLY_INCORRECT triples use `Capital` or `Currency`.
- All TRUE_BUT_SOURCE_UNSUPPORTED triples use `Largest city` or `Continent`.
- All INSUFFICIENT_EVIDENCE triples use `Most popular food` or `Friendliest city`.

A model trained on this dataset learns label patterns from relations, not from semantic reasoning.

### 9.3 Artificially constructed examples
⚠️ **All 80 examples are artificially constructed** following a rigid template. There is no naturally occurring text, no ambiguous boundary cases, and no overlapping evidence. This is appropriate for pipeline prototyping but not for evaluating agent performance on realistic data.

### 9.4 Source document sufficiency
✅ For the designed purpose: each source document perfectly supports or fails to support the triples assigned to it.  
⚠️ For realistic agent evaluation: the documents are too short (2 facts each) and too clean. A real source document would contain noisy, complex, and potentially contradictory text. The agent will not be challenged by these documents.

### 9.5 Data leakage risk
🚨 **HIGH RISK.** Because each relation maps deterministically to exactly one label class, the ANN will learn to solve the task via a simple lookup table rather than any semantic understanding. Evaluation on this dataset alone is **not** evidence of generalization.

### 9.6 Suitability for a small ANN experiment
✅ **Yes — suitable for pipeline testing.**  
❌ **Not suitable for demonstrating that the ANN learns hallucination detection.** The dataset is too small (80 rows) and too regular for meaningful generalization evaluation.

### 9.7 Train/test splitting feasibility
⚠️ **Problematic.** With only 80 rows, any train/test split results in very small test sets. A document-level split (hold out 2 countries as test) gives 64 train / 16 test rows — too small for reliable metric estimation.  
Stratified random split (e.g., 60/20 train/val/test) is feasible but will still produce inflated metrics due to the leakage issue (Section 9.5).

### 9.8 Honest summary

| Dimension | Assessment |
|-----------|-----------|
| Pipeline testing | ✅ Fully suitable |
| Agent plumbing and CSV loading | ✅ Fully suitable |
| ANN input/output format validation | ✅ Suitable |
| Genuine hallucination detection evaluation | ❌ Not suitable |
| Publication-quality benchmark | ❌ Not suitable |
| Generalisation beyond country facts | ❌ Not demonstrated |

---

## 10. Recommended Corrections

### R1 — Fix source_text to contain sentence-level extracts (Priority: HIGH before agent implementation)

Replace the boilerplate header in the `source_text` column with the specific sentence from the source document relevant to each triple.

**Example correction for T0101:**
- **Current:** `"CURATED SOURCE EXCERPT: Pakistan Dataset document ID: source_01 ..."`
- **Corrected:** `"The capital city of Pakistan is Islamabad."`

**For triples not supported by the source (TRUE_BUT_SOURCE_UNSUPPORTED, INSUFFICIENT_EVIDENCE):**
- **Corrected:** `"NOT_MENTIONED"` or leave as the most relevant passage with a note.

This change must be made **before implementing the Source Verification Agent**, as the agent will use this field.

---

### R2 — Document the "largest city" definition (Priority: LOW)

Add a note in `dataset_card.md` or a new column `definition_note` specifying:
> "Largest city by municipality/city-proper population as of [year], per [reference]."

Apply this to all 10 xX03 triples.

---

### R3 — Add diversity to prevent relation→label leakage (Priority: HIGH before model training)

Before training the ANN, expand the dataset with examples where:
- The same relation (`Capital`) appears as both SOURCE_SUPPORTED and FACTUALLY_INCORRECT for different countries.  
  *(This already exists — but for the same set of countries.)*
- Some `Largest city` or `Continent` triples are FACTUALLY_INCORRECT (e.g., wrong continent).
- Some `Capital` triples are TRUE_BUT_SOURCE_UNSUPPORTED (source document doesn't mention it).

This breaks the perfect relation→label correlation and forces the ANN to learn content-based reasoning.

---

### R4 — Expand the dataset before model training (Priority: HIGH before model training)

Add at least 3–5 additional countries with varied relation types. Target a minimum of 200–300 triples for meaningful ANN training. Consider including:
- Triples about historical facts (not just current facts).
- Cross-entity relations (e.g., X is the capital of Y where X and Y are both entities in the KG).
- Borderline TRUE_BUT_SOURCE_UNSUPPORTED cases where the source is ambiguous.

---

### R5 — Clean up the README.md arithmetic note (Priority: LOW)

In `dataset/README.md` line 18, change:  
`"There are 20 rows per label (5? No: 2 rows per country × 10 countries = 20 rows per label)."`  
to:  
`"There are 20 rows per label (2 rows per country × 10 countries = 20 rows per label)."`

---

### R6 — Add T0706 historical note to verification_evidence (Priority: LOW)

In `ground_truth.csv`, update T0706's `verification_evidence` to:  
`"The excerpt explicitly gives euro as the currency, contradicting the candidate object French franc. Additionally, the French franc was abolished as legal tender in 2002 when France adopted the euro, making this claim factually incorrect on independent grounds as well."`

---

## 11. Final Readiness Status

> **READY AFTER MINOR CORRECTIONS**

### Rationale

The dataset is **structurally sound and correctly labelled** for its declared purpose (pipeline testing and agent plumbing). No structural errors, schema mismatches, label type violations, or orphan references were found.

**However, two corrections are strongly recommended before beginning agent implementation:**

1. **Fix the `source_text` field (R1)** — the Source Verification Agent's core logic depends on this field containing the relevant sentence, not a document header.
2. **Document and acknowledge the relation→label leakage (R3, R4)** — make sure the final ANN evaluation section explicitly addresses this limitation.

The dataset is **not** ready for model training without expansion (R3, R4). It is **ready for pipeline development** as stated in its own `dataset_card.md`.

---

### Quick reference — what to fix before the next step

| # | Action | Priority | Required before |
|---|--------|----------|----------------|
| R1 | Replace `source_text` values with sentence-level extracts | 🔴 HIGH | Agent implementation |
| R3 | Add diversity to break relation→label correlation | 🔴 HIGH | Model training |
| R4 | Expand dataset to ≥200 triples | 🔴 HIGH | Model training |
| R2 | Document largest-city definition | 🟡 LOW | Final evaluation |
| R5 | Fix README.md arithmetic note | 🟢 LOW | Anytime |
| R6 | Update T0706 evidence note | 🟢 LOW | Anytime |

---

*Audit completed: 2026-11-25. This report covers the dataset state as of that date. Re-audit after any dataset modification.*

