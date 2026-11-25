# Tests

This directory contains all unit and integration tests for the
**Multi-Agent Knowledge Graph Hallucination Detection** pipeline.

## Purpose

Tests here validate:

| Area | Description |
|------|-------------|
| `DataLoader` | Correct loading and column validation of CSV files |
| `SourceVerificationAgent` | Correct verdict output format and edge cases |
| `FactualVerificationAgent` | Correct verdict output format and edge cases |
| Label preparation logic | Correct mapping of combined verdicts to final labels |

## Guidelines

- Use **pytest** as the test runner.
- Each agent module should have a corresponding test file, e.g.:
  - `test_source_agent.py`
  - `test_factual_agent.py`
  - `test_data_loader.py`
- Use mock data — do not rely on the real `triples.csv` or live APIs in tests.
- Tests must not make external network calls.

## Running Tests (future)

```bash
pytest tests/
```

