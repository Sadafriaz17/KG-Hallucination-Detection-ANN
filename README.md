# Multi-Agent Knowledge Graph Hallucination Detection Using an ANN

> **University ANN Project** | Initial Project Structure

---

## Project Description

This project addresses the problem of **hallucination in Knowledge Graphs (KGs)** — the presence of triples (subject, relation, object) that are factually incorrect or unsupported by their cited sources.

A **multi-agent system** is used to gather verification signals from three independent perspectives:
1. **Source Verification** — does the linked source document support the triple?
2. **Factual Verification** — is the triple factually correct according to external knowledge bases?
3. **Graph Consistency** — is the triple logically consistent with the rest of the KG?

These signals are combined as feature vectors and fed into an **Artificial Neural Network (ANN)** that classifies each triple into one of four final labels.

---

## Project Objectives

1. Build a reproducible dataset of KG triples with associated source documents.
2. Implement three independent verification agents, each producing structured verdicts.
3. Combine agent outputs into feature vectors for ANN classification.
4. Train and evaluate an ANN to detect hallucinated triples.
5. Establish a majority-voting baseline for comparison.

---

## Planned System Workflow

```
triples.csv
    │
    ├──► Source Verification Agent  ──► verdict + confidence
    ├──► Factual Verification Agent ──► verdict + confidence
    └──► Graph Consistency Agent    ──► verdict + confidence (Member 2)
                │
                ▼
        Feature Extraction (Member 2)
                │
                ▼
        ANN Classifier (Member 2)
                │
                ▼
        Final Label per Triple
```

---

## Final Classification Labels

| Label | Meaning |
|-------|---------|
| `SOURCE_SUPPORTED` | The triple is explicitly supported by its source document |
| `TRUE_BUT_SOURCE_UNSUPPORTED` | Factually correct, but NOT found in the source document |
| `FACTUALLY_INCORRECT` | The triple is factually wrong regardless of source |
| `INSUFFICIENT_EVIDENCE` | Not enough evidence to determine correctness |

---

## Project Folder Structure

```text
KG-Hallucination-Detection-ANN/
│
├── dataset/
│   ├── source_documents/        # Raw text source documents
│   │   ├── source_01.txt
│   │   └── README.md
│   ├── triples.csv              # KG triples to be verified
│   ├── ground_truth.csv         # Human-annotated final labels
│   └── dataset_README.md        # Dataset documentation
│
├── agents/
│   ├── __init__.py
│   ├── source_verification/     # Source Verification Agent (Member 1)
│   │   ├── __init__.py
│   │   └── source_agent.py
│   └── factual_verification/    # Factual Verification Agent (Member 1)
│       ├── __init__.py
│       ├── factual_agent.py
│       └── AGENT_README.md
│
├── outputs/
│   ├── source_verification/     # Agent output files (auto-generated)
│   └── factual_verification/    # Agent output files (auto-generated)
│
├── config/
│   └── config.py                # Paths, labels, environment variable names
│
├── utils/
│   ├── __init__.py
│   └── data_loader.py           # CSV and document loading utilities
│
├── tests/
│   └── README.md                # Test guidelines
│
├── .env.example                 # API key template (safe to commit)
├── .gitignore
├── requirements.txt
├── main.py                      # Pipeline entry point (placeholder)
└── README.md
```

---

## Team Responsibilities

### Member 1
| Responsibility | Description |
|----------------|-------------|
| Dataset preparation | Collect source documents, extract triples, populate `triples.csv` |
| Source Verification Agent | Verify triples against their linked source documents |
| Factual Verification Agent | Verify triples against external knowledge bases |
| Ground-truth label preparation | Annotate `ground_truth.csv` using combined agent verdicts |

### Member 2
| Responsibility | Description |
|----------------|-------------|
| Graph Consistency Agent | Check triples for logical consistency within the KG |
| Feature extraction | Combine agent verdicts into ANN input feature vectors |
| ANN model | Design, train, and tune the neural network classifier |
| Majority-voting baseline | Implement a simple baseline for comparison |
| Evaluation | Measure accuracy, precision, recall, and F1 score |

---

## Development Status

| Component | Status |
|-----------|--------|
| Project folder structure | ✅ Complete |
| Pilot dataset | ✅ Populated (80 triples; suitable for pipeline testing) |
| Source Verification Agent | ✅ Implemented and tested |
| Factual Verification Agent | ✅ Implemented and tested (Wikidata-backed) |
| Graph Consistency Agent | 🔲 Not started (Member 2) |
| Data utilities | ✅ Implemented |
| ANN model | 🔲 Not started (Member 2) |
| Evaluation | 🔲 Not started (Member 2) |

---

## Getting Started

```bash
# 1. Clone the repository
git clone <repo-url>
cd KG-Hallucination-Detection-ANN

# 2. Create and activate a virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Optionally configure the Wikidata user-agent
cp .env.example .env
# No API key is required; set WIKIDATA_USER_AGENT if desired.
```

---

## Agent Integration

The Source Verification Agent and Factual Verification Agent accept the same
triple records and return the shared fields `triple_id`, `verdict`,
`confidence`, `evidence`, and `explanation`. Their verdicts answer different
questions and must remain separate when joined by `triple_id`. The factual
agent additionally returns `evidence_source`; the source agent returns
`source_document_id`. See
[agents/factual_verification/AGENT_README.md](agents/factual_verification/AGENT_README.md)
for usage, status semantics, and limitations.

## Interactive Knowledge Graph

The separate Member 1 visualization reads `dataset/triples.csv` and writes
`visualization/knowledge_graph.html`. Install project dependencies with
`pip install -r requirements.txt`, then run:

```bash
python -m visualization.visualize_kg
```

Open the generated HTML file in a browser. Nodes can be dragged, the graph can
be zoomed and explored by hover, and the built-in filter menu can filter edges
by their relation. See [visualization/README.md](visualization/README.md).

## Development Rules

- **Python only.** Modular, readable, well-documented code.
- **No paid APIs or hardcoded API keys.** The current factual agent uses the public Wikidata API.
- **No fabricated data.** Only populate CSVs with verified, real entries.
- **Ground truth must be annotated independently**, not generated from agent predictions.
- **No cross-member scope creep.** Member 1 does not implement the ANN or Graph Consistency Agent.
- Commit messages should be descriptive and reference the component changed.

