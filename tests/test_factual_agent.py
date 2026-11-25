"""Reproducible tests for the factual verification agent and Wikidata client."""

from __future__ import annotations

import json

import pytest

from agents.factual_verification import (
    FactualVerificationAgent,
    FactualVerificationResult,
)
from agents.factual_verification.factual_agent import (
    EvidenceAssessment,
    WikidataClient,
)
from agents.source_verification.source_agent import SourceVerificationResult


class FixedProvider:
    def __init__(self, assessment: EvidenceAssessment | Exception) -> None:
        self.assessment = assessment
        self.calls: list[tuple[str, str, str]] = []

    def verify_claim(
        self, subject: str, relation: str, object_value: str
    ) -> EvidenceAssessment:
        self.calls.append((subject, relation, object_value))
        if isinstance(self.assessment, Exception):
            raise self.assessment
        return self.assessment


def _triple(**overrides: object) -> dict[str, object]:
    triple: dict[str, object] = {
        "triple_id": "T0101",
        "subject": "Pakistan",
        "relation": "Capital",
        "object": "Islamabad",
        "source_document_id": "missing_source_document",
        "source_text": "",
    }
    triple.update(overrides)
    return triple


def _assessment(verdict: str) -> EvidenceAssessment:
    has_evidence = verdict != "INSUFFICIENT_EVIDENCE"
    return EvidenceAssessment(
        verdict=verdict,
        confidence=0.85 if has_evidence else 0.0,
        evidence="Retrieved Wikidata statement evidence." if has_evidence else "",
        evidence_source=(
            "https://www.wikidata.org/wiki/Q123" if has_evidence else ""
        ),
        explanation="Assessment from the injected test provider.",
    )


def _wikidata_client(
    monkeypatch: pytest.MonkeyPatch,
    claims: list[dict[str, object]],
    *,
    subject_results: list[dict[str, str]] | None = None,
    object_results: list[dict[str, str]] | None = None,
) -> WikidataClient:
    client = WikidataClient()
    search_results = {
        "Pakistan": subject_results
        if subject_results is not None
        else [{"id": "Q843", "label": "Pakistan"}],
        "Islamabad": object_results
        if object_results is not None
        else [{"id": "Q1362", "label": "Islamabad"}],
        "Lahore": [{"id": "Q11739", "label": "Lahore"}],
    }

    def mock_request(params: dict[str, str]) -> dict[str, object]:
        if params["action"] == "wbsearchentities":
            return {"search": search_results.get(params["search"], [])}
        return {
            "entities": {
                "Q843": {
                    "claims": {
                        "P36": claims,
                        "P38": claims,
                        "P17": claims,
                        "P6": claims,
                    }
                }
            }
        }

    monkeypatch.setattr(client, "_request_json", mock_request)
    return client


def _claim(target_id: str, *, rank: str = "normal", qualifiers=None):
    statement = {
        "rank": rank,
        "mainsnak": {
            "snaktype": "value",
            "datavalue": {
                "type": "wikibase-entityid",
                "value": {"entity-type": "item", "id": target_id},
            },
        },
    }
    if qualifiers is not None:
        statement["qualifiers"] = qualifiers
    return statement


def test_correct_claim_includes_external_evidence(tmp_path):
    provider = FixedProvider(_assessment("FACTUALLY_CORRECT"))
    agent = FactualVerificationAgent(output_dir=str(tmp_path), client=provider)

    result = agent.verify(_triple())

    assert isinstance(result, FactualVerificationResult)
    assert result.verdict == "FACTUALLY_CORRECT"
    assert result.evidence
    assert result.evidence_source.startswith("https://www.wikidata.org/")
    assert provider.calls == [("Pakistan", "Capital", "Islamabad")]


def test_incorrect_claim_is_preserved_as_distinct_verdict(tmp_path):
    provider = FixedProvider(_assessment("FACTUALLY_INCORRECT"))
    result = FactualVerificationAgent(
        output_dir=str(tmp_path), client=provider
    ).verify(_triple(object="Lahore"))

    assert result.verdict == "FACTUALLY_INCORRECT"
    assert result.confidence > 0.0
    assert result.evidence_source


def test_unavailable_evidence_is_insufficient(tmp_path):
    provider = FixedProvider(_assessment("INSUFFICIENT_EVIDENCE"))
    result = FactualVerificationAgent(
        output_dir=str(tmp_path), client=provider
    ).verify(_triple())

    assert result.verdict == "INSUFFICIENT_EVIDENCE"
    assert result.confidence == 0.0
    assert result.evidence == ""


def test_missing_source_document_does_not_affect_fact_check(tmp_path):
    provider = FixedProvider(_assessment("FACTUALLY_CORRECT"))
    result = FactualVerificationAgent(
        output_dir=str(tmp_path), client=provider
    ).verify(_triple(source_document_id="definitely_missing"))

    assert result.verdict == "FACTUALLY_CORRECT"
    assert provider.calls == [("Pakistan", "Capital", "Islamabad")]


@pytest.mark.parametrize(
    "triple",
    [
        None,
        {},
        _triple(subject=""),
        _triple(relation=None),
        _triple(object=123),
    ],
)
def test_empty_or_malformed_triple_returns_structured_insufficient_result(
    tmp_path, triple
):
    provider = FixedProvider(_assessment("FACTUALLY_CORRECT"))
    result = FactualVerificationAgent(
        output_dir=str(tmp_path), client=provider
    ).verify(triple)

    assert result.verdict == "INSUFFICIENT_EVIDENCE"
    assert result.confidence == 0.0
    assert result.evidence == ""
    assert result.explanation.startswith("Invalid triple:")
    assert provider.calls == []


def test_api_failure_is_reported_without_claiming_verification(
    tmp_path, monkeypatch
):
    def fail_urlopen(request, timeout):
        assert request.full_url.startswith(WikidataClient.API_URL)
        assert timeout == 10.0
        raise TimeoutError("service unavailable")

    monkeypatch.setattr(
        "agents.factual_verification.factual_agent.urlopen", fail_urlopen
    )
    result = FactualVerificationAgent(
        output_dir=tmp_path, client=WikidataClient()
    ).verify(_triple())

    assert result.verdict == "INSUFFICIENT_EVIDENCE"
    assert result.confidence == 0.0
    assert result.evidence == ""
    assert "TimeoutError" in result.explanation


def test_ambiguous_entity_resolution_is_inconclusive(monkeypatch):
    client = _wikidata_client(
        monkeypatch,
        [_claim("Q1362")],
        subject_results=[
            {"id": "Q843", "label": "Pakistan"},
            {"id": "Q999", "label": "Pakistan"},
        ],
    )

    result = client.verify_claim("Pakistan", "Capital", "Islamabad")

    assert result.verdict == "INSUFFICIENT_EVIDENCE"
    assert "ambiguous" in result.explanation


def test_wikidata_single_capital_match_is_correct(monkeypatch):
    client = _wikidata_client(monkeypatch, [_claim("Q1362")])

    result = client.verify_claim("Pakistan", "Capital", "Islamabad")

    assert result.verdict == "FACTUALLY_CORRECT"
    assert "P36" in result.evidence
    assert result.evidence_source.endswith("/Q843")


def test_wikidata_single_unqualified_capital_mismatch_is_incorrect(
    monkeypatch,
):
    client = _wikidata_client(monkeypatch, [_claim("Q1362")])

    result = client.verify_claim("Pakistan", "Capital", "Lahore")

    assert result.verdict == "FACTUALLY_INCORRECT"
    assert "Q1362" in result.evidence
    assert "Q11739" in result.evidence


def test_wikidata_qualified_capital_mismatch_is_not_overstated(monkeypatch):
    client = _wikidata_client(
        monkeypatch,
        [_claim("Q1362", qualifiers={"P580": [{"somevalue": {}}]})],
    )

    result = client.verify_claim("Pakistan", "Capital", "Lahore")

    assert result.verdict == "INSUFFICIENT_EVIDENCE"
    assert result.evidence


def test_unsupported_relation_and_multi_value_mismatch_are_inconclusive(
    monkeypatch,
):
    client = _wikidata_client(monkeypatch, [_claim("Q1362")])
    unsupported = client.verify_claim(
        "Pakistan", "Largest city", "Karachi"
    )
    multi_value = client.verify_claim("Pakistan", "Currency", "Lahore")

    assert unsupported.verdict == "INSUFFICIENT_EVIDENCE"
    assert "no configured" in unsupported.explanation
    assert multi_value.verdict == "INSUFFICIENT_EVIDENCE"


def test_head_of_government_uses_p6_mapping(monkeypatch):
    client = _wikidata_client(monkeypatch, [_claim("Q1362")])

    result = client.verify_claim(
        "Pakistan", "Head of Government", "Islamabad"
    )

    assert result.verdict == "FACTUALLY_CORRECT"
    assert "P6" in result.evidence
    assert "head of government" in result.evidence


def test_generic_leader_relation_is_unsupported_without_api_lookup(
    monkeypatch,
):
    client = WikidataClient()
    calls = []

    def unexpected_request(params):
        calls.append(params)
        raise AssertionError("Unsupported relation must not call Wikidata.")

    monkeypatch.setattr(client, "_request_json", unexpected_request)

    result = client.verify_claim("Pakistan", "Leader", "Islamabad")

    assert result.verdict == "INSUFFICIENT_EVIDENCE"
    assert "no configured" in result.explanation
    assert calls == []


def test_country_mismatch_is_not_treated_as_exclusive(monkeypatch):
    client = _wikidata_client(monkeypatch, [_claim("Q1362")])

    result = client.verify_claim("Pakistan", "Country", "Lahore")

    assert result.verdict == "INSUFFICIENT_EVIDENCE"


def test_result_serialization_has_shared_agent_fields(tmp_path):
    provider = FixedProvider(_assessment("FACTUALLY_CORRECT"))
    result = FactualVerificationAgent(
        output_dir=str(tmp_path), client=provider
    ).verify(_triple())
    parsed = json.loads(result.to_json())
    shared_fields = {
        "triple_id",
        "verdict",
        "confidence",
        "evidence",
        "explanation",
    }

    assert shared_fields.issubset(parsed)
    assert "evidence_source" in parsed
    assert parsed["triple_id"] == "T0101"
    source_result = SourceVerificationResult(
        triple_id="T0101",
        verdict="SUPPORTED",
        confidence=0.95,
        evidence="Source sentence.",
        explanation="The source supports the claim.",
        source_document_id="source_01",
    )
    assert shared_fields.issubset(source_result.to_dict())


def test_batch_processing_saves_structured_results(tmp_path):
    provider = FixedProvider(_assessment("FACTUALLY_CORRECT"))
    agent = FactualVerificationAgent(output_dir=str(tmp_path), client=provider)

    results = agent.run_batch([_triple()], filename="batch.json")
    saved = json.loads((tmp_path / "batch.json").read_text(encoding="utf-8"))

    assert len(results) == 1
    assert saved["total_results"] == 1
    assert saved["verdict_counts"] == {"FACTUALLY_CORRECT": 1}
    assert saved["results"][0]["evidence_source"]
