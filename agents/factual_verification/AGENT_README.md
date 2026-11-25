# Factual Verification Agent

**Module:** `agents/factual_verification/factual_agent.py`

## Purpose and separation

`FactualVerificationAgent` checks whether a triple is supported by external
factual evidence. It does not read `source_document_id`, `source_text`, source
documents, or ground-truth labels. Its result is independent of the
Source Verification Agent's verdict: a fact can be true even when its cited
source does not mention it.

The agent returns one of:

| Verdict | Meaning |
|---|---|
| `FACTUALLY_CORRECT` | A retrieved Wikidata statement directly matches the triple. |
| `FACTUALLY_INCORRECT` | A single, unqualified value for a configured exclusive relation conflicts with the triple. |
| `INSUFFICIENT_EVIDENCE` | The claim is unsupported by retrieved data, ambiguous, unavailable, or outside the supported relation mappings. |

## Evidence provider

The default provider queries the free, public Wikidata MediaWiki API using
Python's standard library. No API key, paid service, or added package is
required. The default HTTP timeout is 10 seconds. An optional
`WIKIDATA_USER_AGENT` environment variable can override the default user-agent.

Configured relation mappings are:

| Relation | Wikidata property | Mapping behavior |
|---|---|---|
| `Capital`, `Capital city` | P36 — capital | Single unqualified mismatch may be incorrect |
| `Currency` | P38 — currency | Non-exclusive; mismatches are inconclusive |
| `Continent` | P30 — continent | Non-exclusive; mismatches are inconclusive |
| `Official language` | P37 — official language | Non-exclusive; mismatches are inconclusive |
| `Country` | P17 — country | Non-exclusive; mismatches are inconclusive |
| `Head of government` | P6 — head of government | Non-exclusive; mismatches are inconclusive |

P6 does **not** mean every kind of leader or head of state. The generic
relation `Leader` is deliberately unsupported. Relations used by this pilot
that are also unsupported include `Largest city`, `Most popular food`, and
`Friendliest city`; they return `INSUFFICIENT_EVIDENCE` without an API lookup.
Other unsupported relations are handled the same way. Exact English entity
labels are required; multiple or missing matches are inconclusive. A
mismatching value is called incorrect only for an unqualified single value
of a configured exclusive relation.

The client is injectable so tests and later providers can supply reproducible
evidence without network access.

## Result schema

```json
{
  "triple_id": "T0101",
  "verdict": "FACTUALLY_CORRECT",
  "confidence": 0.9,
  "evidence": "Wikidata item Q... lists item Q... for the capital property (P36).",
  "explanation": "The retrieved Wikidata statement directly matches the claim.",
  "evidence_source": "https://www.wikidata.org/wiki/Q..."
}
```

The factual and source agents share `triple_id`, `verdict`, `confidence`,
`evidence`, and `explanation`. `evidence_source` records external provenance;
the source agent instead records `source_document_id`. Keep the verdict
vocabularies separate when assembling orchestrator features.

## Usage

```python
from agents.factual_verification import FactualVerificationAgent
from utils.data_loader import DataLoader

triples = DataLoader().load_triples()
agent = FactualVerificationAgent()
results = agent.run_batch(triples)  # writes to outputs/factual_verification/
print(results[0].to_dict())
```

For a single triple, call `agent.verify(triple)`. The factual agent only uses
`triple_id`, `subject`, `relation`, and `object`; source-document fields are
not required.

## Testing

Run all tests with `python -m pytest -q`. The factual-agent tests use an
injected mock provider and mocked Wikidata responses; they do not call the
live API.

## Limitations

- Wikidata is a community-maintained knowledge base; the agent does not
  independently corroborate statements against multiple sources.
- Only the configured relation properties and exact English entity labels
  are currently supported.
- `Largest city` is not currently mapped: the Wikidata property and entity
  resolution needed to define this claim consistently are not implemented.
- Wikidata omissions, ambiguous entity names, qualifiers, and multiple
  plausible values result in insufficient evidence rather than a false
  verdict.
- Confidence values are conservative implementation scores, not calibrated
  probabilities or measured accuracy.
- Live API availability, coverage, and freshness are outside the agent's
  control. No research-quality accuracy claim follows from the pilot tests.

## Orchestrator integration

Pass the same triple dictionaries independently to both agents. Preserve
each agent's verdict and confidence as separate features; do not infer
factual correctness from source support (or vice versa). The ANN/orchestrator
can later join results by `triple_id`, carry each agent's evidence provenance,
and map their independent outputs into its feature schema.
