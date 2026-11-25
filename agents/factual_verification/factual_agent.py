"""
Factual Verification Agent.

Verifies supported relation types against Wikidata, independently of any
source document associated with a triple. Claims that cannot be resolved
unambiguously or supported by retrieved statements remain inconclusive.
"""

from __future__ import annotations

import json
import os
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, Protocol
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from config.config import Config
from dotenv import load_dotenv


@dataclass(frozen=True)
class EvidenceAssessment:
    """Evidence returned by a factual evidence provider."""

    verdict: str
    confidence: float
    evidence: str = ""
    evidence_source: str = ""
    explanation: str = ""


class FactualEvidenceProvider(Protocol):
    """Interface implemented by factual verification evidence providers."""

    def verify_claim(
        self, subject: str, relation: str, object_value: str
    ) -> EvidenceAssessment:
        """Return a verdict grounded in externally retrieved evidence."""


@dataclass
class FactualVerificationResult:
    """Structured factual-verification output for one triple."""

    triple_id: str
    verdict: str
    confidence: float
    evidence: str
    explanation: str
    evidence_source: str

    def __post_init__(self) -> None:
        valid_verdicts = set(Config.FACTUAL_VERDICTS)
        if self.verdict not in valid_verdicts:
            raise ValueError(
                f"Invalid verdict '{self.verdict}'. "
                f"Must be one of: {sorted(valid_verdicts)}"
            )
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                f"confidence must be in [0.0, 1.0], got {self.confidence}"
            )
        if self.verdict != "INSUFFICIENT_EVIDENCE" and (
            not self.evidence.strip() or not self.evidence_source.strip()
        ):
            raise ValueError(
                "A factual verdict requires retrieved evidence and its source."
            )

    def to_dict(self) -> dict[str, Any]:
        """Return a plain dictionary suitable for JSON serialisation."""
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        """Return this result as JSON."""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)


class WikidataClient:
    """Small stdlib-only client for Wikidata's public MediaWiki API.

    Only relations with an explicit Wikidata property mapping are assessed.
    A mismatching value is called incorrect only for a single, unqualified
    value of a relation marked exclusive; all other mismatches are
    inconclusive rather than inferred to be false.
    """

    API_URL = "https://www.wikidata.org/w/api.php"
    ITEM_URL = "https://www.wikidata.org/wiki/"
    RELATION_PROPERTIES: dict[str, tuple[str, str, bool]] = {
        "capital": ("P36", "capital", True),
        "capital city": ("P36", "capital", True),
        "currency": ("P38", "currency", False),
        "continent": ("P30", "continent", False),
        "official language": ("P37", "official language", False),
        "country": ("P17", "country", False),
        "head of government": ("P6", "head of government", False),
    }

    def __init__(self, timeout: float = 10.0) -> None:
        self.timeout = timeout
        load_dotenv(Config.DATASET_DIR.parent / ".env")
        self.user_agent = os.getenv(
            Config.WIKIDATA_USER_AGENT_ENV,
            "KG-Hallucination-Detection-ANN/1.0",
        )
        self._search_cache: dict[str, list[dict[str, Any]]] = {}
        self._entity_cache: dict[str, dict[str, Any]] = {}

    def verify_claim(
        self, subject: str, relation: str, object_value: str
    ) -> EvidenceAssessment:
        """Resolve the claim and compare it with Wikidata statements."""
        relation_key = " ".join(relation.casefold().replace("_", " ").split())
        property_spec = self.RELATION_PROPERTIES.get(relation_key)
        if property_spec is None:
            return EvidenceAssessment(
                verdict="INSUFFICIENT_EVIDENCE",
                confidence=0.0,
                explanation=(
                    f"The relation '{relation}' has no configured Wikidata "
                    "property mapping; no factual verdict was inferred."
                ),
            )

        subject_match, subject_issue = self._resolve_entity(subject)
        if subject_match is None:
            return self._inconclusive(subject_issue)

        object_match, object_issue = self._resolve_entity(object_value)
        if object_match is None:
            return self._inconclusive(object_issue)

        property_id, property_label, exclusive = property_spec
        subject_id = subject_match["id"]
        object_id = object_match["id"]
        entity = self._get_entity(subject_id)
        raw_statements = entity.get("claims", {}).get(property_id, [])
        if not isinstance(raw_statements, list):
            raise ValueError(f"Wikidata returned malformed {property_id} claims.")

        statements: list[dict[str, Any]] = []
        targets: list[str] = []
        target_statements: list[tuple[dict[str, Any], str]] = []
        complete_values = True
        for raw_statement in raw_statements:
            if not isinstance(raw_statement, dict):
                complete_values = False
                continue
            rank = raw_statement.get("rank", "normal")
            if rank == "deprecated":
                continue
            if rank not in ("normal", "preferred"):
                complete_values = False
                continue
            statements.append(raw_statement)

        preferred_statements = [
            statement
            for statement in statements
            if statement.get("rank") == "preferred"
        ]
        if preferred_statements:
            statements = preferred_statements

        for statement in statements:
            snak = statement.get("mainsnak", {})
            value = snak.get("datavalue", {}).get("value", {})
            target_id = value.get("id") if isinstance(value, dict) else None
            if (
                snak.get("snaktype") != "value"
                or not isinstance(value, dict)
                or value.get("entity-type") != "item"
                or not isinstance(target_id, str)
            ):
                complete_values = False
                continue
            targets.append(target_id)
            target_statements.append((statement, target_id))

        source = f"{self.ITEM_URL}{subject_id}"
        matching_statements = [
            statement
            for statement, target in target_statements
            if target == object_id
        ]
        if matching_statements and any(
            not statement.get("qualifiers")
            for statement in matching_statements
        ):
            return EvidenceAssessment(
                verdict="FACTUALLY_CORRECT",
                confidence=0.9,
                evidence=(
                    f"Wikidata item {subject_id} lists item {object_id} "
                    f"for the {property_label} property ({property_id})."
                ),
                evidence_source=source,
                explanation=(
                    f"The retrieved Wikidata statement directly matches "
                    f"'{subject} — {relation} — {object_value}'."
                ),
            )

        if matching_statements:
            return EvidenceAssessment(
                verdict="INSUFFICIENT_EVIDENCE",
                confidence=0.0,
                evidence=(
                    f"Wikidata item {subject_id} lists item {object_id} "
                    f"for the qualified {property_label} property "
                    f"({property_id})."
                ),
                evidence_source=source,
                explanation=(
                    "The matching statement is qualified, but the triple "
                    "does not specify the relevant qualifier context."
                ),
            )

        if not targets:
            return EvidenceAssessment(
                verdict="INSUFFICIENT_EVIDENCE",
                confidence=0.0,
                evidence="",
                evidence_source=source,
                explanation=(
                    f"The retrieved Wikidata item has no usable "
                    f"{property_label} statement ({property_id}); absence "
                    "of a statement is not evidence that the claim is false."
                ),
            )

        evidence = (
            f"Wikidata item {subject_id} lists {', '.join(targets)} for the "
            f"{property_label} property ({property_id}); the queried object "
            f"is {object_id}."
        )
        can_conclude_incorrect = (
            exclusive
            and complete_values
            and len(statements) == 1
            and len(targets) == 1
            and not statements[0].get("qualifiers")
        )
        if can_conclude_incorrect:
            return EvidenceAssessment(
                verdict="FACTUALLY_INCORRECT",
                confidence=0.8,
                evidence=evidence,
                evidence_source=source,
                explanation=(
                    f"Wikidata records a single unqualified {property_label} "
                    "value that differs from the queried object."
                ),
            )

        return EvidenceAssessment(
            verdict="INSUFFICIENT_EVIDENCE",
            confidence=0.0,
            evidence=evidence,
            evidence_source=source,
            explanation=(
                f"Wikidata does not show the queried object among its "
                f"{property_label} values, but the retrieved statements do "
                "not justify concluding that the claim is false."
            ),
        )

    def _resolve_entity(
        self, label: str
    ) -> tuple[Optional[dict[str, Any]], str]:
        matches = [
            item
            for item in self._search_entities(label)
            if isinstance(item.get("label"), str)
            and item["label"].casefold() == label.casefold()
            and isinstance(item.get("id"), str)
        ]
        if len(matches) == 1:
            return matches[0], ""
        if len(matches) > 1:
            issue = (
                f"Wikidata returned multiple exact English-label matches "
                f"for '{label}'; the entity is ambiguous."
            )
        else:
            issue = (
                f"Wikidata returned no exact English-label match for "
                f"'{label}'; the entity could not be resolved."
            )
        return None, issue

    def _search_entities(self, label: str) -> list[dict[str, Any]]:
        cache_key = label.casefold()
        if cache_key not in self._search_cache:
            payload = self._request_json(
                {
                    "action": "wbsearchentities",
                    "search": label,
                    "language": "en",
                    "uselang": "en",
                    "type": "item",
                    "limit": "50",
                    "format": "json",
                }
            )
            results = payload.get("search", [])
            if not isinstance(results, list):
                raise ValueError("Wikidata returned malformed search results.")
            self._search_cache[cache_key] = [
                item for item in results if isinstance(item, dict)
            ]
        return self._search_cache[cache_key]

    def _get_entity(self, entity_id: str) -> dict[str, Any]:
        if entity_id not in self._entity_cache:
            payload = self._request_json(
                {
                    "action": "wbgetentities",
                    "ids": entity_id,
                    "props": "claims",
                    "format": "json",
                }
            )
            entities = payload.get("entities", {})
            entity = entities.get(entity_id) if isinstance(entities, dict) else None
            if not isinstance(entity, dict):
                raise ValueError(
                    f"Wikidata returned no entity data for {entity_id}."
                )
            claims = entity.get("claims", {})
            if not isinstance(claims, dict):
                raise ValueError(
                    f"Wikidata returned malformed claims for {entity_id}."
                )
            self._entity_cache[entity_id] = entity
        return self._entity_cache[entity_id]

    def _request_json(self, params: Mapping[str, str]) -> dict[str, Any]:
        """Perform one API request and decode its JSON response."""
        url = f"{self.API_URL}?{urlencode(params)}"
        request = Request(url, headers={"User-Agent": self.user_agent})
        with urlopen(request, timeout=self.timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("Wikidata returned a non-object JSON response.")
        return payload

    @staticmethod
    def _inconclusive(explanation: str) -> EvidenceAssessment:
        return EvidenceAssessment(
            verdict="INSUFFICIENT_EVIDENCE",
            confidence=0.0,
            explanation=explanation,
        )


class FactualVerificationAgent:
    """Verify triple facts against external evidence, not source documents."""

    _REQUIRED_FIELDS = ("triple_id", "subject", "relation", "object")

    def __init__(
        self,
        output_dir: Optional[Path | str] = None,
        client: Optional[FactualEvidenceProvider] = None,
    ) -> None:
        self.output_dir = Config.FACTUAL_VERIFICATION_OUTPUT_DIR
        if output_dir is not None:
            self.output_dir = Path(output_dir)
        self.client = client if client is not None else WikidataClient()

    def verify(self, triple: object) -> FactualVerificationResult:
        """Verify one triple; invalid input and provider failures are explicit."""
        triple_id = self._get_triple_id(triple)
        validation_error = self._validate_triple(triple)
        if validation_error:
            return self._insufficient(
                triple_id,
                f"Invalid triple: {validation_error}",
            )

        assert isinstance(triple, Mapping)
        try:
            assessment = self.client.verify_claim(
                triple["subject"].strip(),
                triple["relation"].strip(),
                triple["object"].strip(),
            )
            return FactualVerificationResult(
                triple_id=triple_id,
                verdict=assessment.verdict,
                confidence=assessment.confidence,
                evidence=assessment.evidence,
                explanation=assessment.explanation,
                evidence_source=assessment.evidence_source,
            )
        except Exception as exc:
            return self._insufficient(
                triple_id,
                f"External factual verification failed "
                f"({type(exc).__name__}); no verified evidence was returned.",
            )

    def run_batch(
        self,
        triples: Sequence[object],
        *,
        save: bool = True,
        filename: Optional[str] = None,
    ) -> list[FactualVerificationResult]:
        """Verify triples in input order and optionally save a JSON batch."""
        results = [self.verify(triple) for triple in triples]
        if save:
            self._save_batch(results, filename)
        return results

    @classmethod
    def _validate_triple(cls, triple: object) -> str:
        if not isinstance(triple, Mapping):
            return f"expected a mapping, got {type(triple).__name__}."
        for field in cls._REQUIRED_FIELDS:
            value = triple.get(field)
            if not isinstance(value, str) or not value.strip():
                return f"'{field}' must be a non-empty string."
        return ""

    @staticmethod
    def _get_triple_id(triple: object) -> str:
        if isinstance(triple, Mapping):
            triple_id = triple.get("triple_id")
            if isinstance(triple_id, str) and triple_id.strip():
                return triple_id.strip()
        return "UNKNOWN"

    @staticmethod
    def _insufficient(
        triple_id: str, explanation: str
    ) -> FactualVerificationResult:
        return FactualVerificationResult(
            triple_id=triple_id,
            verdict="INSUFFICIENT_EVIDENCE",
            confidence=0.0,
            evidence="",
            explanation=explanation,
            evidence_source="",
        )

    def _save_batch(
        self,
        results: Sequence[FactualVerificationResult],
        filename: Optional[str] = None,
    ) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        if filename is None:
            timestamp = datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S")
            filename = f"factual_verification_batch_{timestamp}.json"

        verdict_counts: dict[str, int] = {}
        for result in results:
            verdict_counts[result.verdict] = (
                verdict_counts.get(result.verdict, 0) + 1
            )
        payload = {
            "generated_at": datetime.now(tz=timezone.utc).isoformat(),
            "total_results": len(results),
            "verdict_counts": verdict_counts,
            "results": [result.to_dict() for result in results],
        }
        (self.output_dir / filename).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
