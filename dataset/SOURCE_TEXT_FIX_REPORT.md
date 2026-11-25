# Source Text Fix Report

> **Clarification (2026-11-25):** “Verbatim” below means character-for-character
> matches between `triples.csv` and the local curated `.txt` files. Those local
> files are manually prepared summaries and have not been verified as verbatim
> quotations from their linked Wikipedia articles. The Source Verification
> Agent reads the complete local file, not the complete external article.
> Current status and ground-truth decisions are documented in
> [`MEMBER1_REAUDIT.md`](./MEMBER1_REAUDIT.md).

**Project:** Multi-Agent Knowledge Graph Hallucination Detection Using an ANN  
**Fix date:** 2026-11-25  
**Addresses audit finding:** Issue #1 from `DATASET_AUDIT_REPORT.md`  
**Author:** Member 1

---

## 1. Summary

The `source_text` column in `dataset/triples.csv` previously contained a repeated
boilerplate document header for all 8 triples belonging to the same source document.
This made the column useless for the Source Verification Agent, whose core task is to
locate the relevant passage from the source for each individual triple.

This fix replaces the boilerplate content with **verbatim sentence-level extracts**
taken directly from each source document.

---

## 2. Schema Proposal and Decision

Before modifying any file, the schema was reviewed to determine whether the existing
`source_text` column could represent the corrected content without a structural change.

### Options considered

| Option | Description | Decision |
|--------|-------------|----------|
| **A — Keep column, fix content** | Populate `source_text` with the specific relevant passage, or `""` when absent | ✅ **Chosen** |
| B — Rename column to `retrieved_passage` | Better name, but would break `DataLoader.TRIPLES_REQUIRED_COLUMNS` and all future code that reads this column | ❌ Rejected — unnecessary breakage at this stage |
| C — Add a second column `retrieved_passage` | Keep old `source_text` and add new column | ❌ Rejected — `source_text` was already the right concept; splitting adds complexity |

### Rationale for Option A

- The column name `source_text` correctly describes the intent: "text from the source document relevant to this triple."
- The column's **declared semantics** in the original `dataset_README.md` said "the exact sentence(s) from the source document supporting the triple." This was too narrow — it did not account for contradicting sentences or the empty-string case. The semantics have been updated in `metadata/schema.json`.
- No structural schema change is required. No code in `DataLoader`, `config.py`, or any agent file needs to change.
- The agent architecture is preserved: the `source_text` field is a **retrieval aid only**. The agent must still read the full source document and reach its own verdict.

### Updated `source_text` semantics (now documented in `metadata/schema.json`)

> The verbatim sentence(s) extracted from the source document that are most relevant
> to verifying this triple. **Empty string** when the claim is not mentioned in the
> source excerpt. This field is a retrieval aid for the Source Verification Agent;
> the agent must always read the full source document via `source_document_id` and
> determine its own SUPPORTED / CONTRADICTED / NOT_MENTIONED verdict independently.

---

## 3. Files Modified

| File | Action | Notes |
|------|--------|-------|
| `dataset/triples.csv` | **Updated** — `source_text` column rewritten | All other columns unchanged |
| `dataset/metadata/schema.json` | **Updated** — added `source_text_semantics` field and updated `note` | Documents the new semantics |
| `dataset/triples.csv.backup_20261125_175306` | **Created** — exact copy of original `triples.csv` before any change | MD5: `bbea1922f18acf21b21df3ef9c01ae86` |

**Files NOT modified (confirmed by MD5 hash):**

| File | MD5 (unchanged) |
|------|----------------|
| `dataset/ground_truth.csv` | `b07f215f0a0a728356a58c2cb5828b42` |
| All 10 `source_documents/*.txt` files | Unchanged (not touched) |
| All agent Python files | Unchanged |
| `config/config.py` | Unchanged |
| `utils/data_loader.py` | Unchanged |

---

## 4. Transformation Rules Applied

Each triple's row type was identified by its `relation` value:

| Relation | Row type | New `source_text` value |
|----------|----------|-------------------------|
| `Capital` (object is correct capital) | Supported | Verbatim capital sentence from source |
| `Currency` (object is correct currency) | Supported | Verbatim currency sentence from source |
| `Capital` (object is a wrong city) | Contradicted | Verbatim capital sentence from source — the source states a different capital, contradicting the triple |
| `Currency` (object is a wrong currency) | Contradicted | Verbatim currency sentence from source — the source states a different currency, contradicting the triple |
| `Largest city` | Not mentioned | `""` (empty string) |
| `Continent` | Not mentioned | `""` (empty string) |
| `Most popular food` | Not mentioned | `""` (empty string) |
| `Friendliest city` | Not mentioned | `""` (empty string) |

> [!IMPORTANT]
> For **contradicted** triples (x05, x06 — wrong capital / wrong currency), the
> `source_text` now contains the **correct** sentence from the source document.
> The agent sees, for example, `source_text = "The capital city of Pakistan is Islamabad."`
> alongside a triple claiming `Capital → Lahore`. This gives the agent the evidence
> it needs to issue a `CONTRADICTED` verdict. The agent must still verify this
> independently — `source_text` is a retrieval aid, not a verdict.

> [!NOTE]
> For **not-mentioned** triples (Largest city, Continent, Most popular food,
> Friendliest city), `source_text = ""`. The agent will read the full source
> document via `source_document_id` and determine for itself that the claim
> is not covered. No `NOT_MENTIONED` string is inserted into the field.

---

## 5. Result Statistics

| Category | Triple count | % of total |
|----------|-------------|-----------|
| `source_text` = supporting sentence (agent should return SUPPORTED) | **20** | 25.0% |
| `source_text` = contradicting sentence (agent should return CONTRADICTED) | **20** | 25.0% |
| `source_text` = `""` — not mentioned in source | **40** | 50.0% |
| Ambiguous / skipped | **0** | 0.0% |
| **Total** | **80** | **100%** |

---

## 6. Verbatim Sentences Used Per Source Document

All sentences were taken character-for-character from the source `.txt` files.
No text was invented or paraphrased.

| Source file | Country | Capital sentence used | Currency sentence used |
|-------------|---------|----------------------|----------------------|
| source_01.txt | Pakistan | "The capital city of Pakistan is Islamabad." | "The currency used in Pakistan is the Pakistani rupee." |
| source_02.txt | India | "The capital city of India is New Delhi." | "The currency used in India is the Indian rupee." |
| source_03.txt | China | "The capital city of China is Beijing." | "The currency used in China is the renminbi." |
| source_04.txt | Japan | "The capital city of Japan is Tokyo." | "The currency used in Japan is the Japanese yen." |
| source_05.txt | France | "The capital city of France is Paris." | "The currency used in France is the euro." |
| source_06.txt | Germany | "The capital city of Germany is Berlin." | "The currency used in Germany is the euro." |
| source_07.txt | Italy | "The capital city of Italy is Rome." | "The currency used in Italy is the euro." |
| source_08.txt | Canada | "The capital city of Canada is Ottawa." | "The currency used in Canada is the Canadian dollar." |
| source_09.txt | Australia | "The capital city of Australia is Canberra." | "The currency used in Australia is the Australian dollar." |
| source_10.txt | Brazil | "The capital city of Brazil is Brasília." | "The currency used in Brazil is the Brazilian real." |

---

## 7. Sample Rows — Before and After

### Pakistan (source_01) — All 8 triples

| triple_id | relation | object | source_text BEFORE | source_text AFTER |
|-----------|----------|--------|--------------------|-------------------|
| T0101 | Capital | Islamabad | *(boilerplate header)* | `The capital city of Pakistan is Islamabad.` |
| T0102 | Currency | Pakistani rupee | *(boilerplate header)* | `The currency used in Pakistan is the Pakistani rupee.` |
| T0103 | Largest city | Karachi | *(boilerplate header)* | *(empty string)* |
| T0104 | Continent | Asia | *(boilerplate header)* | *(empty string)* |
| T0105 | Capital | Lahore | *(boilerplate header)* | `The capital city of Pakistan is Islamabad.` |
| T0106 | Currency | Indian rupee | *(boilerplate header)* | `The currency used in Pakistan is the Pakistani rupee.` |
| T0107 | Most popular food | No objectively established answer | *(boilerplate header)* | *(empty string)* |
| T0108 | Friendliest city | No objectively established answer | *(boilerplate header)* | *(empty string)* |

---

## 8. Ambiguous Cases

**None identified.**

All 80 triples were processed without ambiguity. The relation-to-sentence mapping was
unambiguous for every row. The fix script's `--ambiguous` counter remained at zero.

---

## 9. Agent Architecture Reminder

> [!IMPORTANT]
> The `source_text` field is a **pre-retrieval aid**. When the Source Verification
> Agent is implemented, it must:
>
> 1. Receive the original triple (triple_id, subject, relation, object).
> 2. Load the **full source document** text using `source_document_id`.
> 3. Optionally use `source_text` as a candidate passage (e.g. to skip dense retrieval on this small dataset).
> 4. Issue its own `SUPPORTED / CONTRADICTED / NOT_MENTIONED` verdict with a confidence score.
>
> The agent must **never** receive `ground_truth.csv` labels as input.

---

## 10. Integrity Confirmation

| Check | Result |
|-------|--------|
| Total triples before fix | 80 |
| Total triples after fix | 80 — **unchanged** |
| Duplicate triple_ids | 0 — **unchanged** |
| All `triple_id` values identical | ✅ Verified programmatically |
| All `subject` values identical | ✅ Verified programmatically |
| All `relation` values identical | ✅ Verified programmatically |
| All `object` values identical | ✅ Verified programmatically |
| All `source_document_id` values identical | ✅ Verified programmatically |
| All `source_document_url` values identical | ✅ Verified programmatically |
| `ground_truth.csv` modified | ❌ **Not modified** (MD5 confirmed) |
| Four classification labels modified | ❌ **Not modified** |
| Sentences invented or paraphrased | ❌ **None — all verbatim from source files** |

---

## 11. Next Steps

1. The `source_text` fix resolves audit **Issue #1** (Medium severity). The dataset is now ready for Source Verification Agent implementation.
2. Audit **Issue #3** (relation→label data leakage) remains open and must be addressed before ANN model training.
3. The backup file `triples.csv.backup_20261125_175306` can be deleted once the team confirms the fix is satisfactory. It should not be committed to version control.

---

*Report generated: 2026-11-25. Script used: `brain/.../scratch/fix_source_text.py`.*

