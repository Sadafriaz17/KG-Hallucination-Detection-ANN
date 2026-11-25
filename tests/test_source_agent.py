"""
tests/test_source_agent.py

Unit and integration tests for the Source Verification Agent.

Test coverage
-------------
  TC-01  SUPPORTED verdict  — correct capital triple
  TC-02  SUPPORTED verdict  — correct currency triple
  TC-03  CONTRADICTED verdict — wrong capital triple
  TC-04  CONTRADICTED verdict — wrong currency triple
  TC-05  NOT_MENTIONED verdict — claim absent from source (Largest city)
  TC-06  NOT_MENTIONED verdict — empty source_text field (agent reads full doc)
  TC-07  Error handling — missing source document
  TC-08  Error handling — malformed triple (missing required keys)
  TC-09  Batch run  — mixed verdicts, correct counts
  TC-10  DataLoader integration — load_triples / load_source_document

Important distinction
---------------------
Tests TC-01 through TC-09 are **software tests**: they verify that the
agent code is correct, not that the underlying KG labels are correct.
TC-10 is an integration smoke-test against the real dataset files.

Running
-------
    # From the project root:
    pytest tests/test_source_agent.py -v

    # With coverage:
    pytest tests/test_source_agent.py -v --tb=short
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Allow running from project root without installing the package.
# ---------------------------------------------------------------------------
import sys
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from agents.source_verification.source_agent import (
    SourceVerificationAgent,
    SourceVerificationResult,
)


# ===========================================================================
# Fixtures
# ===========================================================================

@pytest.fixture(scope="module")
def real_docs_dir() -> Path:
    """Path to the actual source_documents/ directory."""
    return _PROJECT_ROOT / "dataset" / "source_documents"


@pytest.fixture(scope="module")
def real_output_dir(tmp_path_factory) -> Path:
    """Temporary output directory shared across the module."""
    return tmp_path_factory.mktemp("sv_output")


@pytest.fixture(scope="module")
def agent(real_docs_dir, real_output_dir) -> SourceVerificationAgent:
    """Agent initialised against the real source documents."""
    return SourceVerificationAgent(
        source_documents_dir=real_docs_dir,
        output_dir=real_output_dir,
    )


# ---------------------------------------------------------------------------
# Helpers — synthetic source document in a temp directory
# ---------------------------------------------------------------------------

@pytest.fixture()
def synthetic_agent(tmp_path) -> SourceVerificationAgent:
    """
    Agent backed by a synthetic source document written to a temp directory.

    The synthetic document (source_synth.txt) contains only:
        1. The headquarters of Acme Corp is Springfield.
        2. The founding year of Acme Corp is 1952.
    """
    docs_dir = tmp_path / "source_documents"
    docs_dir.mkdir()
    out_dir = tmp_path / "outputs" / "source_verification"
    out_dir.mkdir(parents=True)

    doc_text = (
        "CURATED SYNTHETIC DOCUMENT\n"
        "Dataset document ID: source_synth\n\n"
        "1. The headquarters of Acme Corp is Springfield.\n"
        "2. The founding year of Acme Corp is 1952.\n"
    )
    (docs_dir / "source_synth.txt").write_text(doc_text, encoding="utf-8")

    return SourceVerificationAgent(
        source_documents_dir=docs_dir,
        output_dir=out_dir,
    )


def _make_triple(
    triple_id: str,
    subject: str,
    relation: str,
    obj: str,
    source_document_id: str,
    source_text: str = "",
) -> dict:
    return {
        "triple_id": triple_id,
        "subject": subject,
        "relation": relation,
        "object": obj,
        "source_document_id": source_document_id,
        "source_document_url": "",
        "source_text": source_text,
    }


# ===========================================================================
# TC-01  SUPPORTED — correct capital (real dataset)
# ===========================================================================

class TestSupported:
    """TC-01 and TC-02: triples that are explicitly supported by the source."""

    def test_tc01_supported_capital(self, agent):
        """T0101: Pakistan → Capital → Islamabad is explicitly in source_01."""
        triple = _make_triple(
            triple_id="T0101",
            subject="Pakistan",
            relation="Capital",
            obj="Islamabad",
            source_document_id="source_01",
            source_text="The capital city of Pakistan is Islamabad.",
        )
        result = agent.verify(triple)

        assert isinstance(result, SourceVerificationResult)
        assert result.triple_id == "T0101"
        assert result.verdict == "SUPPORTED", (
            f"Expected SUPPORTED, got {result.verdict}. "
            f"Explanation: {result.explanation}"
        )
        assert result.confidence >= 0.80
        assert "Islamabad" in result.evidence or "Islamabad" in result.explanation
        assert result.source_document_id == "source_01"

    def test_tc02_supported_currency(self, agent):
        """T0102: Pakistan → Currency → Pakistani rupee is explicitly in source_01."""
        triple = _make_triple(
            triple_id="T0102",
            subject="Pakistan",
            relation="Currency",
            obj="Pakistani rupee",
            source_document_id="source_01",
            source_text="The currency used in Pakistan is the Pakistani rupee.",
        )
        result = agent.verify(triple)

        assert result.verdict == "SUPPORTED", (
            f"Expected SUPPORTED, got {result.verdict}. "
            f"Explanation: {result.explanation}"
        )
        assert result.confidence >= 0.80
        assert "Pakistani rupee" in result.evidence or \
               "Pakistani rupee" in result.explanation

    def test_supported_another_country(self, agent):
        """T0901: Australia → Capital → Canberra should be SUPPORTED."""
        triple = _make_triple(
            triple_id="T0901",
            subject="Australia",
            relation="Capital",
            obj="Canberra",
            source_document_id="source_09",
        )
        result = agent.verify(triple)
        assert result.verdict == "SUPPORTED"
        assert result.confidence >= 0.80

    def test_supported_result_serialises_to_json(self, agent):
        """SUPPORTED result must serialise cleanly to valid JSON."""
        triple = _make_triple(
            triple_id="T0101",
            subject="Pakistan",
            relation="Capital",
            obj="Islamabad",
            source_document_id="source_01",
        )
        result = agent.verify(triple)
        json_str = result.to_json()
        parsed = json.loads(json_str)

        assert parsed["verdict"] == "SUPPORTED"
        assert "confidence" in parsed
        assert "evidence" in parsed
        assert "explanation" in parsed
        assert "source_document_id" in parsed


# ===========================================================================
# TC-03  CONTRADICTED — wrong capital (real dataset)
# ===========================================================================

class TestContradicted:
    """TC-03 and TC-04: triples the source document actively contradicts."""

    def test_tc03_contradicted_capital(self, agent):
        """T0105: Pakistan → Capital → Lahore. Source says Islamabad."""
        triple = _make_triple(
            triple_id="T0105",
            subject="Pakistan",
            relation="Capital",
            obj="Lahore",
            source_document_id="source_01",
            source_text="The capital city of Pakistan is Islamabad.",
        )
        result = agent.verify(triple)

        assert result.verdict == "CONTRADICTED", (
            f"Expected CONTRADICTED, got {result.verdict}. "
            f"Evidence: {result.evidence}\n"
            f"Explanation: {result.explanation}"
        )
        assert result.confidence >= 0.80
        # The contradicting sentence should be in the evidence.
        assert result.evidence != "", "Evidence must not be empty for CONTRADICTED."
        # The correct city should appear in the evidence sentence.
        assert "Islamabad" in result.evidence

    def test_tc04_contradicted_currency(self, agent):
        """T0106: Pakistan → Currency → Indian rupee. Source says Pakistani rupee."""
        triple = _make_triple(
            triple_id="T0106",
            subject="Pakistan",
            relation="Currency",
            obj="Indian rupee",
            source_document_id="source_01",
            source_text="The currency used in Pakistan is the Pakistani rupee.",
        )
        result = agent.verify(triple)

        assert result.verdict == "CONTRADICTED", (
            f"Expected CONTRADICTED, got {result.verdict}. "
            f"Evidence: {result.evidence}"
        )
        assert result.confidence >= 0.80
        assert "Pakistani rupee" in result.evidence

    def test_contradicted_another_country(self, agent):
        """T1005: Brazil → Capital → Rio de Janeiro. Source says Brasília."""
        triple = _make_triple(
            triple_id="T1005",
            subject="Brazil",
            relation="Capital",
            obj="Rio de Janeiro",
            source_document_id="source_10",
        )
        result = agent.verify(triple)
        assert result.verdict == "CONTRADICTED"
        assert "Brasília" in result.evidence

    def test_contradicted_synthetic(self, synthetic_agent):
        """Synthetic doc: Acme Corp → Headquarters → Shelbyville (wrong)."""
        triple = _make_triple(
            triple_id="SYN-01",
            subject="Acme Corp",
            relation="Headquarters",
            obj="Shelbyville",
            source_document_id="source_synth",
        )
        # The doc says "Springfield" — Shelbyville is not in the doc.
        # The agent should return CONTRADICTED (source mentions Acme+headquarters).
        result = synthetic_agent.verify(triple)
        assert result.verdict == "CONTRADICTED"
        assert result.evidence != ""

    def test_partial_entity_word_is_not_treated_as_a_match(
        self, synthetic_agent
    ):
        triple = _make_triple(
            triple_id="SYN-PARTIAL",
            subject="Acme Corp",
            relation="Headquarters",
            obj="field",
            source_document_id="source_synth",
        )

        result = synthetic_agent.verify(triple)

        assert result.verdict == "CONTRADICTED"
        assert "Springfield" in result.evidence

    def test_partial_multiword_entity_is_not_treated_as_a_match(self, agent):
        triple = _make_triple(
            triple_id="T0201-PARTIAL",
            subject="India",
            relation="Capital",
            obj="Delhi",
            source_document_id="source_02",
        )

        result = agent.verify(triple)

        assert result.verdict == "CONTRADICTED"
        assert "New Delhi" in result.evidence

    def test_negated_object_is_not_treated_as_supported(self, tmp_path):
        docs_dir = tmp_path / "source_documents"
        docs_dir.mkdir()
        (docs_dir / "source_negated.txt").write_text(
            "The capital of Acme Corp is not Springfield.",
            encoding="utf-8",
        )
        agent = SourceVerificationAgent(
            source_documents_dir=docs_dir,
            output_dir=tmp_path / "outputs",
        )
        triple = _make_triple(
            triple_id="SYN-NEGATED",
            subject="Acme Corp",
            relation="Capital",
            obj="Springfield",
            source_document_id="source_negated",
        )

        result = agent.verify(triple)

        assert result.verdict == "CONTRADICTED"
        assert "not Springfield" in result.evidence


# ===========================================================================
# TC-05  NOT_MENTIONED — claim absent from source
# ===========================================================================

class TestNotMentioned:
    """TC-05: source document exists but does not cover the relation."""

    def test_tc05_not_mentioned_largest_city(self, agent):
        """T0103: Pakistan → Largest city → Karachi. Source_01 has no largest-city info."""
        triple = _make_triple(
            triple_id="T0103",
            subject="Pakistan",
            relation="Largest city",
            obj="Karachi",
            source_document_id="source_01",
            source_text="",   # correctly empty after the fix
        )
        result = agent.verify(triple)

        assert result.verdict == "NOT_MENTIONED", (
            f"Expected NOT_MENTIONED, got {result.verdict}. "
            f"Evidence: {result.evidence}\n"
            f"Explanation: {result.explanation}"
        )
        assert result.evidence == "", (
            "evidence must be an empty string for NOT_MENTIONED."
        )
        assert result.confidence > 0.0

    def test_not_mentioned_continent(self, agent):
        """T0104: Pakistan → Continent → Asia. Source_01 never mentions continent."""
        triple = _make_triple(
            triple_id="T0104",
            subject="Pakistan",
            relation="Continent",
            obj="Asia",
            source_document_id="source_01",
        )
        result = agent.verify(triple)
        assert result.verdict == "NOT_MENTIONED"

    def test_not_mentioned_subjective_food(self, agent):
        """T0107: Pakistan → Most popular food → No objectively established answer."""
        triple = _make_triple(
            triple_id="T0107",
            subject="Pakistan",
            relation="Most popular food",
            obj="No objectively established answer",
            source_document_id="source_01",
        )
        result = agent.verify(triple)
        assert result.verdict == "NOT_MENTIONED"

    def test_not_mentioned_synthetic(self, synthetic_agent):
        """Synthetic doc: Acme Corp → Employee count → 500. Not in doc."""
        triple = _make_triple(
            triple_id="SYN-02",
            subject="Acme Corp",
            relation="Employee count",
            obj="500",
            source_document_id="source_synth",
        )
        result = synthetic_agent.verify(triple)
        assert result.verdict == "NOT_MENTIONED"
        assert result.evidence == ""

    def test_ambiguous_value_is_not_reported_as_contradiction(self, tmp_path):
        docs_dir = tmp_path / "source_documents"
        docs_dir.mkdir()
        (docs_dir / "source_ambiguous.txt").write_text(
            "The capital of Acme Corp is disputed.",
            encoding="utf-8",
        )
        agent = SourceVerificationAgent(
            source_documents_dir=docs_dir,
            output_dir=tmp_path / "outputs",
        )
        triple = _make_triple(
            triple_id="SYN-AMBIGUOUS",
            subject="Acme Corp",
            relation="Capital",
            obj="Springfield",
            source_document_id="source_ambiguous",
        )

        result = agent.verify(triple)

        assert result.verdict == "NOT_MENTIONED"
        assert result.confidence == 0.6
        assert result.evidence == ""
        assert "does not establish" in result.explanation

    def test_subject_fragment_does_not_match_entity_name(self, synthetic_agent):
        triple = _make_triple(
            triple_id="SYN-SUBJECT-FRAGMENT",
            subject="Acm",
            relation="Headquarters",
            obj="Springfield",
            source_document_id="source_synth",
        )

        result = synthetic_agent.verify(triple)

        assert result.verdict == "NOT_MENTIONED"


# ===========================================================================
# TC-06  Empty source_text does NOT default to NOT_MENTIONED
# ===========================================================================

class TestEmptySourceText:
    """TC-06: agent reads the full document regardless of source_text value."""

    def test_tc06_empty_source_text_still_finds_support(self, agent):
        """
        When source_text is intentionally left empty, the agent must still
        read the full document and return the correct verdict.

        T0101 with source_text='' should still yield SUPPORTED because the
        full source_01.txt contains the supporting sentence.
        """
        triple = _make_triple(
            triple_id="T0101",
            subject="Pakistan",
            relation="Capital",
            obj="Islamabad",
            source_document_id="source_01",
            source_text="",   # deliberately empty
        )
        result = agent.verify(triple)

        assert result.verdict == "SUPPORTED", (
            "Agent must read the full document even when source_text is empty. "
            f"Got {result.verdict} with explanation: {result.explanation}"
        )

    def test_empty_source_text_contradicted(self, agent):
        """T0105 with source_text='' should still yield CONTRADICTED."""
        triple = _make_triple(
            triple_id="T0105",
            subject="Pakistan",
            relation="Capital",
            obj="Lahore",
            source_document_id="source_01",
            source_text="",
        )
        result = agent.verify(triple)
        assert result.verdict == "CONTRADICTED"


# ===========================================================================
# TC-07  Error handling — missing source document
# ===========================================================================

class TestMissingDocument:
    """TC-07: appropriate error when the source document file does not exist."""

    def test_tc07_missing_document_raises(self, agent):
        """FileNotFoundError must be raised for a non-existent document ID."""
        triple = _make_triple(
            triple_id="T9999",
            subject="Narnia",
            relation="Capital",
            obj="Cair Paravel",
            source_document_id="source_nonexistent",
        )
        with pytest.raises(FileNotFoundError) as exc_info:
            agent.verify(triple)

        assert "source_nonexistent" in str(exc_info.value).lower() or \
               "not found" in str(exc_info.value).lower()

    def test_missing_document_in_batch_does_not_abort(self, agent):
        """
        run_batch must continue processing remaining triples even when one
        triple references a missing document.
        """
        triples = [
            _make_triple(
                triple_id="T0101",
                subject="Pakistan",
                relation="Capital",
                obj="Islamabad",
                source_document_id="source_01",
            ),
            _make_triple(
                triple_id="T9999",
                subject="Narnia",
                relation="Capital",
                obj="Cair Paravel",
                source_document_id="source_nonexistent",
            ),
            _make_triple(
                triple_id="T0201",
                subject="India",
                relation="Capital",
                obj="New Delhi",
                source_document_id="source_02",
            ),
        ]
        results = agent.run_batch(triples, save=False)

        assert len(results) == 3
        assert results[0].verdict == "SUPPORTED"
        assert results[2].verdict == "SUPPORTED"
        # The errored result carries confidence 0.0 and an error message.
        assert results[1].confidence == 0.0
        assert "ERROR" in results[1].explanation or \
               "error" in results[1].explanation.lower()

    def test_malformed_batch_items_do_not_abort_valid_items(self, agent):
        valid = _make_triple(
            triple_id="T0101",
            subject="Pakistan",
            relation="Capital",
            obj="Islamabad",
            source_document_id="source_01",
        )
        missing_field = {
            "triple_id": "BAD-FIELD",
            "subject": "Pakistan",
            "relation": "Capital",
            "object": "Islamabad",
        }

        results = agent.run_batch([["not", "a", "triple"], missing_field, valid], save=False)

        assert len(results) == 3
        assert results[0].triple_id == "UNKNOWN"
        assert results[1].triple_id == "BAD-FIELD"
        assert all(result.confidence == 0.0 for result in results[:2])
        assert all("[AGENT ERROR]" in result.explanation for result in results[:2])
        assert results[2].verdict == "SUPPORTED"


# ===========================================================================
# TC-08  Error handling — malformed triple
# ===========================================================================

class TestMalformedTriple:
    """TC-08: validation errors for incomplete or mis-typed input."""

    def test_tc08_missing_required_key(self, agent):
        """ValueError when a required key (subject) is absent."""
        triple = {
            "triple_id": "T0101",
            # "subject" is missing
            "relation": "Capital",
            "object": "Islamabad",
            "source_document_id": "source_01",
        }
        with pytest.raises(ValueError) as exc_info:
            agent.verify(triple)
        assert "subject" in str(exc_info.value).lower() or \
               "missing" in str(exc_info.value).lower()

    def test_empty_subject_raises(self, agent):
        """ValueError when subject is an empty string."""
        triple = _make_triple(
            triple_id="T0101",
            subject="",        # empty
            relation="Capital",
            obj="Islamabad",
            source_document_id="source_01",
        )
        with pytest.raises(ValueError):
            agent.verify(triple)

    def test_non_dict_input_raises(self, agent):
        """TypeError when verify() receives a non-dict."""
        with pytest.raises(TypeError):
            agent.verify(["T0101", "Pakistan", "Capital", "Islamabad"])

    def test_empty_triple_id_raises(self, agent):
        """ValueError when triple_id is an empty string."""
        triple = _make_triple(
            triple_id="",
            subject="Pakistan",
            relation="Capital",
            obj="Islamabad",
            source_document_id="source_01",
        )
        with pytest.raises(ValueError):
            agent.verify(triple)

    def test_empty_source_document_id_raises(self, agent):
        """ValueError when source_document_id is an empty string."""
        triple = _make_triple(
            triple_id="T0101",
            subject="Pakistan",
            relation="Capital",
            obj="Islamabad",
            source_document_id="",   # empty
        )
        with pytest.raises(ValueError):
            agent.verify(triple)


# ===========================================================================
# TC-09  Batch run — mixed verdicts
# ===========================================================================

class TestBatchRun:
    """TC-09: run_batch processes a mixed list and saves output correctly."""

    def test_tc09_batch_mixed_verdicts(self, agent, real_output_dir):
        """
        Run a batch of 6 triples spanning all three expected verdicts.
        Counts must match expectations.
        """
        triples = [
            # 2 × SUPPORTED
            _make_triple(triple_id="T0101", subject="Pakistan",   relation="Capital",      obj="Islamabad",       source_document_id="source_01"),
            _make_triple(triple_id="T0102", subject="Pakistan",   relation="Currency",     obj="Pakistani rupee", source_document_id="source_01"),
            # 2 × CONTRADICTED
            _make_triple(triple_id="T0105", subject="Pakistan",   relation="Capital",      obj="Lahore",          source_document_id="source_01"),
            _make_triple(triple_id="T0106", subject="Pakistan",   relation="Currency",     obj="Indian rupee",    source_document_id="source_01"),
            # 2 × NOT_MENTIONED
            _make_triple(triple_id="T0103", subject="Pakistan",   relation="Largest city", obj="Karachi",         source_document_id="source_01"),
            _make_triple(triple_id="T0104", subject="Pakistan",   relation="Continent",    obj="Asia",            source_document_id="source_01"),
        ]

        results = agent.run_batch(triples, save=True, filename="test_batch.json")

        assert len(results) == 6

        verdicts = [r.verdict for r in results]
        assert verdicts.count("SUPPORTED")     == 2
        assert verdicts.count("CONTRADICTED")  == 2
        assert verdicts.count("NOT_MENTIONED") == 2

        # Verify the JSON file was written.
        out_file = real_output_dir / "test_batch.json"
        assert out_file.exists(), "Batch output JSON file not found."

        with out_file.open(encoding="utf-8") as fh:
            data = json.load(fh)

        assert data["total_results"] == 6
        assert data["verdict_counts"]["SUPPORTED"]     == 2
        assert data["verdict_counts"]["CONTRADICTED"]  == 2
        assert data["verdict_counts"]["NOT_MENTIONED"] == 2
        assert len(data["results"]) == 6

    def test_batch_all_supported(self, agent):
        """Batch of correct triples across different countries."""
        triples = [
            _make_triple(triple_id="T0201", subject="India",    relation="Capital", obj="New Delhi",   source_document_id="source_02"),
            _make_triple(triple_id="T0301", subject="China",    relation="Capital", obj="Beijing",     source_document_id="source_03"),
            _make_triple(triple_id="T0401", subject="Japan",    relation="Capital", obj="Tokyo",       source_document_id="source_04"),
            _make_triple(triple_id="T0501", subject="France",   relation="Capital", obj="Paris",       source_document_id="source_05"),
            _make_triple(triple_id="T0601", subject="Germany",  relation="Capital", obj="Berlin",      source_document_id="source_06"),
            _make_triple(triple_id="T0701", subject="Italy",    relation="Capital", obj="Rome",        source_document_id="source_07"),
            _make_triple(triple_id="T0801", subject="Canada",   relation="Capital", obj="Ottawa",      source_document_id="source_08"),
            _make_triple(triple_id="T0901", subject="Australia",relation="Capital", obj="Canberra",    source_document_id="source_09"),
            _make_triple(triple_id="T1001", subject="Brazil",   relation="Capital", obj="Brasília",    source_document_id="source_10"),
        ]
        results = agent.run_batch(triples, save=False)
        assert all(r.verdict == "SUPPORTED" for r in results), (
            [r.verdict for r in results]
        )


# ===========================================================================
# TC-10  DataLoader integration
# ===========================================================================

class TestDataLoaderIntegration:
    """TC-10: smoke tests against the real dataset files via DataLoader."""

    def test_load_triples_returns_80_rows(self):
        """DataLoader.load_triples() should return exactly 80 rows."""
        from utils.data_loader import DataLoader
        loader = DataLoader()
        triples = loader.load_triples()
        assert len(triples) == 80

    def test_load_triples_has_required_columns(self):
        """All required columns must be present in every row."""
        from utils.data_loader import DataLoader
        loader = DataLoader()
        triples = loader.load_triples()
        required = {
            "triple_id", "subject", "relation", "object",
            "source_document_id", "source_document_url", "source_text",
        }
        for row in triples:
            assert required.issubset(row.keys()), (
                f"Missing columns in row {row.get('triple_id')}: "
                f"{required - set(row.keys())}"
            )

    def test_load_source_document_returns_text(self):
        """DataLoader.load_source_document() must return non-empty text."""
        from utils.data_loader import DataLoader
        loader = DataLoader()
        for doc_id in [f"source_{i:02d}" for i in range(1, 11)]:
            text = loader.load_source_document(doc_id)
            assert isinstance(text, str)
            assert len(text) > 0, f"Empty text for {doc_id}"

    def test_load_source_document_missing_raises(self):
        """FileNotFoundError for a non-existent document ID."""
        from utils.data_loader import DataLoader
        loader = DataLoader()
        with pytest.raises(FileNotFoundError):
            loader.load_source_document("source_nonexistent")

    def test_agent_processes_all_real_triples(self, agent):
        """
        Integration smoke test: run the agent on all 80 real triples.
        Every result must have a valid verdict and confidence > 0.
        """
        from utils.data_loader import DataLoader
        loader  = DataLoader()
        triples = loader.load_triples()

        results = agent.run_batch(triples, save=False)

        assert len(results) == 80

        valid_verdicts = {"SUPPORTED", "CONTRADICTED", "NOT_MENTIONED"}
        for r in results:
            assert r.verdict in valid_verdicts, (
                f"{r.triple_id}: unexpected verdict '{r.verdict}'"
            )
            assert 0.0 <= r.confidence <= 1.0, (
                f"{r.triple_id}: confidence out of range: {r.confidence}"
            )


# ===========================================================================
# Output format tests
# ===========================================================================

class TestOutputFormat:
    """Verify the structure of SourceVerificationResult."""

    def test_result_dataclass_fields(self, agent):
        """Result must expose all required fields."""
        triple = _make_triple(
            triple_id="T0101",
            subject="Pakistan",
            relation="Capital",
            obj="Islamabad",
            source_document_id="source_01",
        )
        result = agent.verify(triple)
        assert hasattr(result, "triple_id")
        assert hasattr(result, "verdict")
        assert hasattr(result, "confidence")
        assert hasattr(result, "evidence")
        assert hasattr(result, "explanation")
        assert hasattr(result, "source_document_id")

    def test_to_dict_has_all_keys(self, agent):
        """to_dict() must include all six required keys."""
        triple = _make_triple(
            triple_id="T0101",
            subject="Pakistan",
            relation="Capital",
            obj="Islamabad",
            source_document_id="source_01",
        )
        d = agent.verify(triple).to_dict()
        required_keys = {
            "triple_id", "verdict", "confidence",
            "evidence", "explanation", "source_document_id",
        }
        assert required_keys.issubset(d.keys())

    def test_confidence_is_float_in_range(self, agent):
        """Confidence must be a float in [0.0, 1.0]."""
        for obj, expected_verdict in [
            ("Islamabad", "SUPPORTED"),
            ("Lahore",    "CONTRADICTED"),
            ("Karachi",   "NOT_MENTIONED"),
        ]:
            triple = _make_triple(
                triple_id="TEST",
                subject="Pakistan",
                relation="Capital" if obj != "Karachi" else "Largest city",
                obj=obj,
                source_document_id="source_01",
            )
            result = agent.verify(triple)
            assert isinstance(result.confidence, float)
            assert 0.0 <= result.confidence <= 1.0
