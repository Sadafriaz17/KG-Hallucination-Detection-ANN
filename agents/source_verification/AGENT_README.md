# Source Verification Agent

**Module:** `agents/source_verification/source_agent.py`  
**Author:** Member 1  
**Status:** ✅ Implemented and tested

---

## Purpose

The Source Verification Agent determines whether a Knowledge Graph triple is:

| Verdict | Meaning |
|---------|---------|
| `SUPPORTED` | The source document contains a sentence that explicitly confirms the triple. |
| `CONTRADICTED` | A relevant source sentence explicitly denies the object or gives another value in a simple relation-value statement. |
| `NOT_MENTIONED` | The source does not establish the object or an explicit alternative. This includes ambiguous topical mentions. |

The agent operates **independently**: it never reads `ground_truth.csv` or the Factual Verification Agent's output.

---

## Algorithm

```
verify(triple):
  1. Validate triple structure (required keys, non-empty values).
  2. Load the full source document from disk using source_document_id.
  3. Strip preamble / metadata lines from the document.
  4. Split remaining text into individual sentences.
  5. Match subject and relation terms with word boundaries; single-word entity
     matches embedded in capitalized multi-word names are not accepted.
  6. Score each sentence for relevance to (subject, relation):
       score += 2.0  if subject appears in sentence
       score += 1.0  per relation keyword that appears in sentence
  7. Keep sentences scoring ≥ 3.0 (subject AND at least one relation term).
  8. Return SUPPORTED only when the object is not directly negated.
  9. Return CONTRADICTED only for a direct denial or explicit alternative
     value; otherwise return NOT_MENTIONED.
 10. Return SourceVerificationResult dataclass.
```

> [!NOTE]
> The `source_text` field from `triples.csv` is **not** used for the verdict
> decision. The agent reads the complete local file named by
> `source_document_id`. Those local files are curated summaries, not full
> downloads of the linked articles, so “full document” means the full local
> text file—not the full external web page.

---

## Usage

### Single triple

```python
from agents.source_verification import SourceVerificationAgent

agent = SourceVerificationAgent()

triple = {
    "triple_id":          "T0101",
    "subject":            "Pakistan",
    "relation":           "Capital",
    "object":             "Islamabad",
    "source_document_id": "source_01",
    "source_text":        "",   # optional retrieval aid
}

result = agent.verify(triple)
print(result.verdict)      # SUPPORTED
print(result.confidence)   # 0.95
print(result.evidence)     # "The capital city of Pakistan is Islamabad."
print(result.to_json())    # full JSON string
```

### Batch (all 80 triples, results saved automatically)

```python
from agents.source_verification import SourceVerificationAgent
from utils.data_loader import DataLoader

loader = DataLoader()
triples = loader.load_triples()

agent = SourceVerificationAgent()
results = agent.run_batch(triples)   # saves to outputs/source_verification/
```

### Custom paths

```python
from pathlib import Path
from agents.source_verification import SourceVerificationAgent

agent = SourceVerificationAgent(
    source_documents_dir=Path("dataset/source_documents"),
    output_dir=Path("outputs/source_verification"),
)
```

---

## Running from the command line

```bash
# From the project root:
python -c "
from agents.source_verification import SourceVerificationAgent
from utils.data_loader import DataLoader

agent   = SourceVerificationAgent()
triples = DataLoader().load_triples()
results = agent.run_batch(triples)

for r in results[:5]:
    print(r.triple_id, r.verdict, r.confidence)
"
```

---

## Running the tests

```bash
# From the project root:
pytest tests/test_source_agent.py -v
```

Run the current source-agent tests with `python -m pytest tests/test_source_agent.py -q`.

---

## Output format

Each result serialises to:

```json
{
  "triple_id": "T0101",
  "verdict": "SUPPORTED",
  "confidence": 0.95,
  "evidence": "The capital city of Pakistan is Islamabad.",
  "explanation": "The source document explicitly states ...",
  "source_document_id": "source_01"
}
```

Batch output is saved to `outputs/source_verification/` as a JSON file containing:

```json
{
  "generated_at": "2026-11-25T...",
  "total_results": 80,
  "verdict_counts": {
    "SUPPORTED": 20,
    "CONTRADICTED": 20,
    "NOT_MENTIONED": 40
  },
  "results": [ ... ]
}
```

---

## Confidence calibration

| Scenario | Confidence |
|----------|-----------|
| Object found in highest-scoring relevant sentence | 0.95 |
| Object found in a lower-ranked relevant sentence | 0.80 |
| Explicit denial or simple alternative value (CONTRADICTED) | 0.90 |
| Relevant but ambiguous mention (NOT_MENTIONED) | 0.60 |
| No relevant sentences found (NOT_MENTIONED) | 0.80 |
| Agent error during batch (graceful fallback) | 0.00 |

Confidence reflects **strength of source evidence**, not factual belief.

---

## Limitations

1. Uses keyword-based sentence matching — no semantic embeddings or BM25.
2. Can misclassify if the source document uses uncommon synonyms for the relation.
3. Contradiction detection only recognizes direct negation and simple
   subject/relation/copula/value wording; more complex syntax remains
   inconclusive or may be misclassified.
4. The single-word proper-name guard is heuristic and is not named-entity
   recognition.

These limitations are acceptable for the pilot dataset. See `IMPLEMENTATION_REPORT.md` for upgrade paths.

