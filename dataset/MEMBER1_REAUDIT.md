# Member 1 Dataset and Agent Re-audit

**Audit date:** 2026-11-25  
**Scope:** Dataset, ground truth, Source Verification Agent, Factual Verification
Agent, their tests and documentation, and the separate KG visualization.

## Summary

The pilot contains 80 triples, 80 ground-truth rows, and 10 local source-text
files. Structural checks confirm that triple IDs are unique and align exactly
between the two CSV files, all labels use the configured vocabulary, every
source-document ID resolves to a local file, and every non-empty `source_text`
value occurs in its corresponding local source file.

The label distribution after this review is:

| Label | Count |
|---|---:|
| `SOURCE_SUPPORTED` | 20 |
| `TRUE_BUT_SOURCE_UNSUPPORTED` | 18 |
| `FACTUALLY_INCORRECT` | 22 |
| `INSUFFICIENT_EVIDENCE` | 20 |

Two labels changed: **T0203** and **T0903**. The city-size convention and
row-level evidence are recorded below and in `ground_truth.csv`. No triple
values, source text, or source-document files were changed for visualization.

## Ground-truth review

All 80 rows were reviewed by their construction groups across the 10 country
profiles:

- `x01` and `x02`: capital and currency claims; local excerpts state these
  values and the archived country profiles corroborate them.
- `x03`: largest-city claims; checked against the defined population field
  below. Eight remain true-but-source-unsupported; two are incorrect under
  this measure.
- `x04`: continent claims; use the seven-continent model and principal
  territory convention below. The local excerpts do not mention continents.
- `x05` and `x06`: deliberately wrong capital/currency values; both the local
  excerpt and archived profile identify the corresponding correct value.
- `x07` and `x08`: subjective claims without a defined metric or survey;
  retained as `INSUFFICIENT_EVIDENCE`.

### Operational definition for “Largest city”

For consistency, this pilot interprets `Largest city` as the first-ranked city
in the CIA World Factbook's **“Major urban areas - population”** field, using
its 2023 estimates in the 2025-labelled edition. This is an urban-area proxy;
the field does not provide a uniform city-proper or metropolitan-boundary
definition. Thus these labels are conditional on that explicit field, not
universal claims about all definitions of “city.”

| ID | Triple object | Top entries in archived field (millions) | Decision |
|---|---|---|---|
| T0103 | Karachi | Karachi 17.236; Lahore 13.979 | Retained `TRUE_BUT_SOURCE_UNSUPPORTED` |
| T0203 | Mumbai | New Delhi 32.941; Mumbai 21.297 | Changed to `FACTUALLY_INCORRECT` |
| T0303 | Shanghai | Shanghai 29.211; Beijing 21.766 | Retained `TRUE_BUT_SOURCE_UNSUPPORTED` |
| T0403 | Tokyo | Tokyo 37.194; Osaka 19.013 | Retained `TRUE_BUT_SOURCE_UNSUPPORTED` |
| T0503 | Paris | Paris 11.208; Lyon 1.761 | Retained `TRUE_BUT_SOURCE_UNSUPPORTED` |
| T0603 | Berlin | Berlin 3.574; Hamburg 1.788 | Retained `TRUE_BUT_SOURCE_UNSUPPORTED` |
| T0703 | Rome | Rome 4.316; Milan 3.155 | Retained `TRUE_BUT_SOURCE_UNSUPPORTED` |
| T0803 | Toronto | Toronto 6.372; Montreal 4.308 | Retained `TRUE_BUT_SOURCE_UNSUPPORTED` |
| T0903 | Sydney | Melbourne 5.235; Sydney 5.121 | Changed to `FACTUALLY_INCORRECT` |
| T1003 | São Paulo | São Paulo 22.620; Rio de Janeiro 13.728 | Retained `TRUE_BUT_SOURCE_UNSUPPORTED` |

The two changed rows have their exact comparisons and caveat written into
`ground_truth.csv`. If the research definition later requires city-proper or
metro-area populations, manually re-adjudicate all ten rows rather than
reusing these labels.

### Continent convention

`Continent` uses the seven-continent model and assigns a country by its
principal territory; overseas territories do not change the assigned
continent. The intended labels are Asia for Pakistan, India, China, and Japan;
Europe for France, Germany, and Italy; North America for Canada; Oceania for
Australia; and South America for Brazil. These rows remain
`TRUE_BUT_SOURCE_UNSUPPORTED` because the local source excerpts do not state
the continent.

### References and source-text limitations

The original CIA country-profile URLs are no longer live: the CIA announced
that the World Factbook had sunset on February 4, 2026. Ground-truth references
now point to a **third-party archive** of the 2025-labelled edition, whose
source snapshot is dated January 22, 2026. It is an archival copy, not a current
CIA service or an independent second source. For example, see [Pakistan],
[India], [China], [Japan], [France], [Germany], [Italy], [Canada], [Australia],
and [Brazil], and the [CIA sunset announcement].

The `.txt` files are short, manually curated summaries. The populated
`source_text` cells match sentences in those local files exactly, but the
local sentences are **not verified verbatim quotations** from their linked
Wikipedia articles. The Source Verification Agent reads each complete local
file, not the full external article. This bounds what its source verdict can
claim.

## Agent contracts and limitations

Both agents accept the same triple dictionary independently. Their common
result fields are `triple_id`, `verdict`, `confidence`, `evidence`, and
`explanation`. The Source Verification Agent additionally returns
`source_document_id`; the Factual Verification Agent additionally returns
`evidence_source`. Their verdict vocabularies remain distinct and neither
agent loads ground-truth data.

The factual agent uses the public Wikidata API and supports:

| Input relation | Property | Notes |
|---|---|---|
| `Capital`, `Capital city` | P36 | Only an unqualified single-value mismatch can be called incorrect |
| `Currency` | P38 | Non-exclusive |
| `Continent` | P30 | Non-exclusive |
| `Official language` | P37 | Non-exclusive |
| `Country` | P17 | Non-exclusive |
| `Head of government` | P6 | Specifically head of government, not every meaning of “leader” |

Generic `Leader`, `Largest city`, `Most popular food`, and `Friendliest city`
are unsupported and return `INSUFFICIENT_EVIDENCE` without claiming external
verification. Exact English entity-label matching can be ambiguous; omitted,
qualified, or multiple Wikidata values also produce an inconclusive verdict.
Confidence values are implementation scores, not calibrated probabilities.

The Source Verification Agent now uses boundary-aware matching, rejects a
single-word entity match embedded in a capitalized multi-word name, checks
direct negation, and only returns `CONTRADICTED` for a direct denial or a simple
explicit alternative-value statement. Ambiguous mentions return
`NOT_MENTIONED` at lower confidence. These are conservative lexical heuristics,
not semantic parsing or entity recognition. Batch errors preserve the
established output schema and are marked with zero confidence and an explicit
`[AGENT ERROR]` explanation.

## Member 1 handoff

The agents are ready to be called independently and joined by `triple_id`.
Keep source support separate from factual correctness; preserve each verdict,
confidence, evidence, and provenance field. Do not treat this pilot or its
labels as an expert-validated benchmark. The graph-consistency agent,
orchestrator, feature extraction, ANN, majority baseline, and system-level
evaluation remain outside Member 1's scope.

## References

- [CIA announcement that The World Factbook had sunset](https://www.cia.gov/stories/story/spotlighting-the-world-factbook-as-we-bid-a-fond-farewell/)
- [2025-labelled CIA Factbook archive](https://worldfactbookarchive.org/)
- [Pakistan]: https://worldfactbookarchive.org/archive/2025/PK
- [India]: https://worldfactbookarchive.org/archive/2025/IN
- [China]: https://worldfactbookarchive.org/archive/2025/CN
- [Japan]: https://worldfactbookarchive.org/archive/2025/JP
- [France]: https://worldfactbookarchive.org/archive/2025/FR
- [Germany]: https://worldfactbookarchive.org/archive/2025/DE
- [Italy]: https://worldfactbookarchive.org/archive/2025/IT
- [Canada]: https://worldfactbookarchive.org/archive/2025/CA
- [Australia]: https://worldfactbookarchive.org/archive/2025/AU
- [Brazil]: https://worldfactbookarchive.org/archive/2025/BR
