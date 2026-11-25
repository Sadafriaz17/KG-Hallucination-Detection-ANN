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
│       └── factual_agent.py
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
| Dataset files (headers) | ✅ Created (empty — to be populated) |
| Source Verification Agent | 🔲 Placeholder only |
| Factual Verification Agent | 🔲 Placeholder only |
| Graph Consistency Agent | 🔲 Not started (Member 2) |
| Data utilities | 🔲 Placeholder only |
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

# 4. Configure environment variables
cp .env.example .env
# Edit .env and add your API keys (never commit .env)
```

---

## Development Rules

- **Python only.** Modular, readable, well-documented code.
- **No real API keys** in the repository. Use `.env` and `.env.example`.
- **No fabricated data.** Only populate CSVs with verified, real entries.
- **No cross-member scope creep.** Member 1 does not implement the ANN or Graph Consistency Agent.
- Commit messages should be descriptive and reference the component changed.

