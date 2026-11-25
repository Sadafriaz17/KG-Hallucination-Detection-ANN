"""
agents/source_verification/source_agent.py

Source Verification Agent
=========================

Determines whether a Knowledge Graph triple is SUPPORTED, CONTRADICTED,
or NOT_MENTIONED by its associated source document.

Algorithm
---------
For each triple the agent:
  1.  Validates the triple structure (required keys present, non-empty values).
  2.  Loads the **complete** source document from disk via source_document_id.
      The ``source_text`` field is used only as a retrieval aid; the agent
      never trusts it blindly.
  3.  Splits the document into individual sentences.
  4.  Scores every sentence for relevance to (subject, relation) using
      keyword matching and term-overlap heuristics.
  5.  From the top-ranked relevant sentences, determines one verdict:
        - SUPPORTED     : a relevant sentence contains the object as a
                          standalone entity phrase and does not negate it.
        - CONTRADICTED  : the source explicitly denies the object or gives
                          another value in a simple relation-value sentence.
        - NOT_MENTIONED : no relevant sentences were found at all.
  6.  Assigns a confidence score based on evidence strength.
  7.  Returns a ``SourceVerificationResult`` dataclass that serialises to JSON.

Design constraints honoured
---------------------------
- No country-specific or domain-specific facts are hardcoded.
- The agent never reads ``ground_truth.csv``.
- The agent never calls the Factual Verification Agent.
- No external network calls are made.
- Empty ``source_text`` does NOT default to NOT_MENTIONED.

Confidence calibration
----------------------
  SUPPORTED (object phrase in top relevant sentence) : 0.95
  SUPPORTED (object phrase in another relevant sentence): 0.80
  CONTRADICTED (explicit denial or alternative value): 0.90
  NOT_MENTIONED (relation discussed, answer unclear) : 0.60
  NOT_MENTIONED (no relevant sentences found)        : 0.80

Outputs
-------
Results are written as JSON to ``outputs/source_verification/``.
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Allow running from the project root with: python -m agents.source_verification
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from config.config import Config


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass
class SourceVerificationResult:
    """
    Structured output produced by the Source Verification Agent for one triple.

    Attributes:
        triple_id:          Matches the triple's ``triple_id`` column.
        verdict:            One of ``SUPPORTED | CONTRADICTED | NOT_MENTIONED``.
        confidence:         Float in [0.0, 1.0]; reflects strength of source
                            evidence, **not** general factual belief.
        evidence:           Verbatim sentence(s) extracted from the source
                            document that led to this verdict.
                            Empty string when verdict is NOT_MENTIONED.
        explanation:        Natural-language justification.
        source_document_id: ID of the source document that was read.
    """

    triple_id: str
    verdict: str
    confidence: float
    evidence: str
    explanation: str
    source_document_id: str

    # ------------------------------------------------------------------
    def to_dict(self) -> Dict:
        """Return a plain dict suitable for JSON serialisation."""
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        """Return a JSON string representation."""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

    # ------------------------------------------------------------------
    def __post_init__(self) -> None:
        valid_verdicts = set(Config.SOURCE_VERDICTS)
        if self.verdict not in valid_verdicts:
            raise ValueError(
                f"Invalid verdict '{self.verdict}'. "
                f"Must be one of: {sorted(valid_verdicts)}"
            )
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError(
                f"confidence must be in [0.0, 1.0], got {self.confidence}"
            )


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

class SourceVerificationAgent:
    """
    Verifies Knowledge Graph triples against their source documents.

    This agent uses keyword-based sentence retrieval to locate passages in a
    source document that are relevant to a given (subject, relation) pair,
    then checks whether the object value is confirmed or denied by those
    passages.

    It is intentionally free of hardcoded domain facts.  Relation-to-keyword
    mappings are general vocabulary associations (e.g. "Capital" → "capital
    city") rather than country-specific assertions.

    Attributes:
        source_documents_dir (Path): Directory containing ``.txt`` source files.
        output_dir (Path):           Directory where JSON results are saved.
        cfg (Config):                Project configuration instance.
    """

    # ------------------------------------------------------------------
    # Relation keyword vocabulary
    # ------------------------------------------------------------------
    # Maps a relation name to additional search terms used when scanning
    # document sentences for relevance.  The relation name itself is always
    # included automatically; these are SYNONYMS only.
    # No country-specific or object-specific facts are stored here.
    # ------------------------------------------------------------------
    RELATION_KEYWORDS: Dict[str, List[str]] = {
        "Capital":           ["capital city", "seat of government",
                              "administrative capital", "capital of"],
        "Currency":          ["currency", "currencies", "legal tender",
                              "monetary unit", "denomination"],
        "Largest city":      ["largest city", "most populous city",
                              "largest urban area", "biggest city",
                              "largest municipality"],
        "Continent":         ["continent", "continental", "located in",
                              "situated in"],
        "Official language": ["official language", "national language",
                              "spoken language"],
        "Population":        ["population", "inhabitants", "residents"],
        "Leader":            ["president", "prime minister", "head of state",
                              "chancellor", "premier", "leader"],
        "Founded":           ["founded", "established", "created", "formed"],
        "Area":              ["area", "land area", "square kilometres",
                              "square kilometers", "sq km"],
        "Friendliest city":  ["friendliest", "friendliness", "hospitality"],
        "Most popular food": ["popular food", "cuisine", "national dish",
                              "traditional food"],
    }

    # Minimum sentence length (characters) to consider as a candidate.
    _MIN_SENTENCE_LEN: int = 8

    # Lines that begin with these prefixes are preamble / metadata and are
    # excluded from sentence candidates before relevance scoring.
    # This prevents header lines like "CURATED SOURCE EXCERPT: Pakistan"
    # from being treated as evidence sentences.
    _PREAMBLE_PREFIXES: Tuple[str, ...] = (
        "curated source excerpt",
        "dataset document id",
        "original source page",
        "retrieved/prepared",
        "source attribution",
        "dataset design note",
        "for academic use",
        "other true facts",
        "a claim can be",
        "http",
    )

    # Required keys in every triple dict passed to verify().
    _REQUIRED_TRIPLE_KEYS: Tuple[str, ...] = (
        "triple_id",
        "subject",
        "relation",
        "object",
        "source_document_id",
    )

    # ------------------------------------------------------------------
    def __init__(
        self,
        source_documents_dir: Optional[Path] = None,
        output_dir: Optional[Path] = None,
        cfg: Optional[Config] = None,
    ) -> None:
        """
        Initialise the Source Verification Agent.

        Args:
            source_documents_dir (Path, optional):
                Path to the ``source_documents/`` directory.
                Defaults to ``Config.SOURCE_DOCUMENTS_DIR``.
            output_dir (Path, optional):
                Path to ``outputs/source_verification/``.
                Defaults to ``Config.SOURCE_VERIFICATION_OUTPUT_DIR``.
            cfg (Config, optional):
                Project configuration.  Defaults to ``Config()``.
        """
        self.cfg = cfg or Config()
        self.source_documents_dir = (
            Path(source_documents_dir)
            if source_documents_dir is not None
            else self.cfg.SOURCE_DOCUMENTS_DIR
        )
        self.output_dir = (
            Path(output_dir)
            if output_dir is not None
            else self.cfg.SOURCE_VERIFICATION_OUTPUT_DIR
        )
        self.output_dir.mkdir(parents=True, exist_ok=True)

    # ==================================================================
    # Public API
    # ==================================================================

    def verify(self, triple: Dict[str, str]) -> SourceVerificationResult:
        """
        Verify a single triple against its source document.

        The agent reads the **complete** source document from disk and
        independently determines its verdict.  It never trusts the
        ``source_text`` field as ground truth.

        Args:
            triple (Dict[str, str]): Must contain at minimum:
                ``triple_id``, ``subject``, ``relation``, ``object``,
                ``source_document_id``.
                ``source_text`` is optional (used only as a hint in the
                explanation, not for the verdict decision).

        Returns:
            SourceVerificationResult: Structured verdict with confidence,
            evidence, and explanation.

        Raises:
            TypeError: If ``triple`` is not a dict.
            ValueError: If the triple is missing required keys or contains
                empty values for mandatory fields.
            FileNotFoundError: If the referenced source document does not
                exist on disk.
        """
        self._validate_triple(triple)

        triple_id          = triple["triple_id"].strip()
        subject            = triple["subject"].strip()
        relation           = triple["relation"].strip()
        object_value       = triple["object"].strip()
        source_document_id = triple["source_document_id"].strip()

        # 1. Load the full source document.
        doc_text = self._load_document(source_document_id)

        # 2. Split document into individual sentences.
        sentences = self._split_into_sentences(doc_text)

        # 3. Find sentences relevant to (subject, relation).
        relevant = self._find_relevant_sentences(sentences, subject, relation)

        # 4. Determine verdict from relevant sentences.
        verdict, confidence, evidence, explanation = self._determine_verdict(
            relevant_sentences=relevant,
            subject=subject,
            relation=relation,
            object_value=object_value,
        )

        return SourceVerificationResult(
            triple_id=triple_id,
            verdict=verdict,
            confidence=round(confidence, 4),
            evidence=evidence,
            explanation=explanation,
            source_document_id=source_document_id,
        )

    def run_batch(
        self,
        triples: List[object],
        *,
        save: bool = True,
        filename: Optional[str] = None,
    ) -> List[SourceVerificationResult]:
        """
        Verify a list of triples and optionally save results to disk.

        Processing is sequential; each triple is verified independently.
        Invalid triples are recorded as ``NOT_MENTIONED`` with zero
        confidence and an explicit ``[AGENT ERROR]`` explanation, preserving
        the established verdict schema while allowing later items to run.

        Args:
            triples (List[object]): List of triple dicts, possibly malformed.
            save (bool): If True (default), write results to
                ``outputs/source_verification/`` as a JSON file.
            filename (str, optional): Override the auto-generated output
                filename.  Should end in ``.json``.

        Returns:
            List[SourceVerificationResult]: One result per input triple,
            in the same order.
        """
        results: List[SourceVerificationResult] = []

        for triple in triples:
            try:
                result = self.verify(triple)
            except (TypeError, ValueError, FileNotFoundError) as exc:
                # Produce an error result instead of crashing the batch.
                tid = "UNKNOWN"
                source_document_id = ""
                if isinstance(triple, dict):
                    candidate_id = triple.get("triple_id")
                    candidate_document_id = triple.get("source_document_id")
                    if isinstance(candidate_id, str) and candidate_id.strip():
                        tid = candidate_id.strip()
                    if isinstance(candidate_document_id, str):
                        source_document_id = candidate_document_id.strip()
                result = SourceVerificationResult(
                    triple_id=tid,
                    verdict="NOT_MENTIONED",   # safest fallback for downstream
                    confidence=0.0,
                    evidence="",
                    explanation=f"[AGENT ERROR] {type(exc).__name__}: {exc}",
                    source_document_id=source_document_id,
                )
            results.append(result)

        if save:
            self._save_batch(results, filename=filename)

        return results

    def save_result(self, result: SourceVerificationResult) -> Path:
        """
        Save a single result as a JSON file.

        Args:
            result (SourceVerificationResult): The result to persist.

        Returns:
            Path: Absolute path of the written file.
        """
        out_path = self.output_dir / f"{result.triple_id}.json"
        out_path.write_text(result.to_json(), encoding="utf-8")
        return out_path

    # ==================================================================
    # Private — document loading
    # ==================================================================

    def _load_document(self, source_document_id: str) -> str:
        """
        Load the full text of a source document from disk.

        Args:
            source_document_id (str): Document ID (no ``.txt`` extension).

        Returns:
            str: Full document text.

        Raises:
            FileNotFoundError: If the file does not exist.
        """
        doc_path = self.source_documents_dir / f"{source_document_id}.txt"
        if not doc_path.exists():
            raise FileNotFoundError(
                f"Source document not found: {doc_path}\n"
                f"Confirm that '{source_document_id}.txt' exists inside "
                f"{self.source_documents_dir}."
            )
        return doc_path.read_text(encoding="utf-8")

    # ==================================================================
    # Private — text processing
    # ==================================================================

    def _split_into_sentences(self, text: str) -> List[str]:
        """
        Split document text into individual sentences.

        Handles:
          - Numbered list items (``1. ..., 2. ...``).
          - Paragraph and line breaks.
          - Standard sentence-terminal punctuation (``.``, ``!``, ``?``).

        Args:
            text (str): Full document text.

        Returns:
            List[str]: Non-empty sentences, stripped of leading/trailing
            whitespace and numbered-list prefixes.
        """
        sentences: List[str] = []

        # Split on newlines first to handle numbered lists correctly.
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue

            # Skip preamble / metadata lines that carry no factual claims.
            line_lower = line.lower()
            if any(line_lower.startswith(prefix) for prefix in self._PREAMBLE_PREFIXES):
                continue

            # Remove numbered-list prefixes: "1. ", "2. ", etc.
            line = re.sub(r"^\d+\.\s+", "", line)

            # Further split on sentence boundaries within the line.
            parts = re.split(r"(?<=[.!?])\s+", line)
            for part in parts:
                part = part.strip()
                if len(part) >= self._MIN_SENTENCE_LEN:
                    sentences.append(part)

        return sentences

    def _get_relation_terms(self, relation: str) -> List[str]:
        """
        Return all search terms for a given relation.

        Always includes the relation name itself (lowercased) plus any
        synonyms from ``RELATION_KEYWORDS``.

        Args:
            relation (str): The relation / predicate string.

        Returns:
            List[str]: List of lowercased search terms.
        """
        base_terms = [relation.casefold()]
        synonyms = next(
            (
                terms
                for name, terms in self.RELATION_KEYWORDS.items()
                if name.casefold() == relation.casefold()
            ),
            [],
        )
        return base_terms + [term.casefold() for term in synonyms]

    def _score_sentence_relevance(
        self,
        sentence: str,
        subject: str,
        relation_terms: List[str],
    ) -> float:
        """
        Score how relevant a sentence is to the (subject, relation) pair.

        Scoring rules (additive):
          +2.0  if the subject appears in the sentence (case-insensitive).
          +1.0  for each relation term that appears in the sentence.

        Args:
            sentence (str):       A single document sentence.
            subject (str):        The triple's subject entity.
            relation_terms (List[str]): Search terms for the relation.

        Returns:
            float: Relevance score (higher = more relevant).
        """
        score = 0.0

        if self._contains_phrase(subject, sentence, entity=True):
            score += 2.0

        for term in relation_terms:
            if self._contains_phrase(term, sentence):
                score += 1.0

        return score

    def _find_relevant_sentences(
        self,
        sentences: List[str],
        subject: str,
        relation: str,
        *,
        min_score: float = 3.0,
    ) -> List[str]:
        """
        Return sentences that are relevant to the (subject, relation) pair,
        ranked by relevance score descending.

        A sentence qualifies only if it scores >= ``min_score``.
        The default threshold of 3.0 requires the subject (score +2) AND
        at least one relation term (score +1) to both appear in the sentence.
        This prevents subject-only matches (e.g. a sentence about Pakistan's
        capital from being treated as relevant to 'Largest city').

        Args:
            sentences (List[str]):  All sentences extracted from the document.
            subject (str):          Triple's subject entity.
            relation (str):         Triple's relation / predicate.
            min_score (float):      Minimum score to include a sentence.

        Returns:
            List[str]: Relevant sentences, highest-scoring first.
        """
        relation_terms = self._get_relation_terms(relation)
        scored = [
            (self._score_sentence_relevance(s, subject, relation_terms), s)
            for s in sentences
        ]
        # Keep only sentences that meet the threshold, sorted by score desc.
        relevant = [
            s for score, s in sorted(scored, key=lambda x: x[0], reverse=True)
            if score >= min_score
        ]
        return relevant

    # ==================================================================
    # Private — verdict logic
    # ==================================================================

    def _contains_phrase(
        self, phrase: str, sentence: str, *, entity: bool = False
    ) -> bool:
        """Match a phrase without matching word fragments or partial names."""
        phrase = phrase.strip()
        if not phrase:
            return False
        pattern = re.compile(
            rf"(?<!\w){re.escape(phrase)}(?!\w)",
            flags=re.IGNORECASE | re.UNICODE,
        )
        for match in pattern.finditer(sentence):
            if entity and len(phrase.split()) == 1:
                before = sentence[:match.start()].rstrip()
                after = sentence[match.end():]
                previous_word = re.search(r"([\w]+)$", before, re.UNICODE)
                next_word = re.match(r"\s+([\w]+)", after, re.UNICODE)
                if (
                    previous_word
                    and previous_word.group(1)[0].isupper()
                ) or (
                    next_word
                    and next_word.group(1)[0].isupper()
                ):
                    continue
            return True
        return False

    def _object_in_sentence(self, object_value: str, sentence: str) -> bool:
        """
        Case-insensitive check whether the object appears in a sentence.

        Strips surrounding whitespace from both inputs before comparison.

        Args:
            object_value (str): The triple's object string.
            sentence (str):     A document sentence.

        Returns:
            bool: True if the object is found (case-insensitive).
        """
        return self._contains_phrase(object_value, sentence, entity=True)

    @staticmethod
    def _object_is_negated(object_value: str, sentence: str) -> bool:
        """Detect direct English negation immediately before an object phrase."""
        phrase = re.escape(object_value.strip())
        if not phrase:
            return False
        pattern = re.compile(
            rf"\b(?:not|never|no|isn't|aren't|wasn't|weren't)\s+"
            rf"(?:(?:the|a|an)\s+)?{phrase}(?!\w)",
            flags=re.IGNORECASE | re.UNICODE,
        )
        return pattern.search(sentence) is not None

    def _has_explicit_alternative_value(
        self, sentence: str, subject: str, relation: str
    ) -> bool:
        """Recognize simple subject/relation/copula/value statements."""
        subject_pattern = re.compile(
            rf"(?<!\w){re.escape(subject.strip())}(?!\w)",
            flags=re.IGNORECASE | re.UNICODE,
        )
        copula_pattern = re.compile(
            r"\b(?:is|are|was|were)\b", flags=re.IGNORECASE
        )
        uncertain_values = {
            "disputed",
            "unclear",
            "unknown",
            "uncertain",
            "undetermined",
            "not established",
            "not specified",
            "not known",
        }
        relation_terms = self._get_relation_terms(relation)
        subject_matches = list(subject_pattern.finditer(sentence))
        relation_matches = [
            match
            for term in relation_terms
            for match in re.finditer(
                rf"(?<!\w){re.escape(term)}(?!\w)",
                sentence,
                flags=re.IGNORECASE | re.UNICODE,
            )
        ]
        for subject_match in subject_matches:
            for relation_match in relation_matches:
                statement_end = max(subject_match.end(), relation_match.end())
                copula = copula_pattern.search(sentence, statement_end)
                if copula is None:
                    continue
                value = re.split(r"[,;.!?]", sentence[copula.end():], maxsplit=1)[0]
                value = re.sub(r"^\s*(?:the|a|an)\s+", "", value.strip(), flags=re.IGNORECASE)
                value = " ".join(value.split())
                if (
                    value
                    and value.casefold() not in uncertain_values
                    and not value.casefold().startswith(
                        ("not ", "no ", "never ")
                    )
                ):
                    return True
        return False

    def _determine_verdict(
        self,
        relevant_sentences: List[str],
        subject: str,
        relation: str,
        object_value: str,
    ) -> Tuple[str, float, str, str]:
        """
        Apply verdict logic given the ranked relevant sentences.

        Rules
        -----
        1. No relevant sentences found → NOT_MENTIONED (0.80).
        2. Object found in a relevant sentence → SUPPORTED.
           - Confidence 0.95 if the highest-scoring sentence contains it.
           - Confidence 0.80 if only a lower-ranked sentence contains it.
        3. A direct denial or explicit alternative value → CONTRADICTED (0.90).
        4. Relation mentioned but no explicit answer → NOT_MENTIONED (0.60).

        Args:
            relevant_sentences (List[str]): Ranked relevant sentences.
            subject (str):      Triple's subject.
            relation (str):     Triple's relation.
            object_value (str): Triple's object.

        Returns:
            Tuple[str, float, str, str]:
                (verdict, confidence, evidence_text, explanation_text)
        """
        # ── Case 1: nothing relevant found ────────────────────────────
        if not relevant_sentences:
            explanation = (
                f"No sentences in the source document discuss "
                f"'{subject}' in relation to '{relation}'. "
                f"The claim cannot be verified from this source."
            )
            return "NOT_MENTIONED", 0.80, "", explanation

        # ── Case 2: check for SUPPORTED ────────────────────────────────
        # Walk sentences in rank order; first hit gets highest confidence.
        for rank, sentence in enumerate(relevant_sentences):
            if (
                self._object_in_sentence(object_value, sentence)
                and not self._object_is_negated(object_value, sentence)
            ):
                confidence = 0.95 if rank == 0 else 0.80
                explanation = (
                    f"The source document explicitly states '{sentence}', "
                    f"which confirms the triple's claim that "
                    f"'{subject}' has '{relation}' = '{object_value}'."
                )
                return "SUPPORTED", confidence, sentence, explanation

        # A negated object is direct evidence against the queried claim.
        for sentence in relevant_sentences:
            if self._object_is_negated(object_value, sentence):
                explanation = (
                    f"The source document explicitly negates "
                    f"'{object_value}' in its discussion of "
                    f"'{subject}' and '{relation}'."
                )
                return "CONTRADICTED", 0.90, sentence, explanation

        # Only treat a mismatch as contradiction when a simple statement
        # explicitly supplies another value; mere topical overlap is not enough.
        for sentence in relevant_sentences:
            if self._has_explicit_alternative_value(sentence, subject, relation):
                explanation = (
                    f"The source document states an alternative value for "
                    f"'{subject}' and '{relation}' in: \"{sentence}\"."
                )
                return "CONTRADICTED", 0.90, sentence, explanation

        # Relation was mentioned, but the available wording does not establish
        # either the queried object or a contradictory value.
        best_sentence = relevant_sentences[0]
        explanation = (
            f"The source document mentions '{subject}' and '{relation}' "
            f"(best matching sentence: \"{best_sentence}\"), but it does not "
            f"establish '{object_value}' or an alternative value."
        )
        return "NOT_MENTIONED", 0.60, "", explanation

    # ==================================================================
    # Private — validation
    # ==================================================================

    def _validate_triple(self, triple: Dict) -> None:
        """
        Check that a triple dict contains all required keys with
        non-empty string values.

        Args:
            triple (Dict): The triple to validate.

        Raises:
            TypeError:  If ``triple`` is not a dict.
            ValueError: If any required key is missing or its value is
                empty / non-string.
        """
        if not isinstance(triple, dict):
            raise TypeError(
                f"triple must be a dict, got {type(triple).__name__}."
            )

        missing_keys = [
            k for k in self._REQUIRED_TRIPLE_KEYS if k not in triple
        ]
        if missing_keys:
            raise ValueError(
                f"Triple is missing required keys: {missing_keys}. "
                f"Received keys: {list(triple.keys())}"
            )

        for key in ("triple_id", "subject", "relation", "object",
                    "source_document_id"):
            val = triple.get(key)
            if not isinstance(val, str) or not val.strip():
                raise ValueError(
                    f"Triple field '{key}' must be a non-empty string, "
                    f"got: {val!r}"
                )

    # ==================================================================
    # Private — I/O
    # ==================================================================

    def _save_batch(
        self,
        results: List[SourceVerificationResult],
        *,
        filename: Optional[str] = None,
    ) -> Path:
        """
        Persist a list of results to a single JSON file.

        Args:
            results (List[SourceVerificationResult]): Results to save.
            filename (str, optional): Override the auto-generated name.

        Returns:
            Path: Absolute path of the written file.
        """
        if filename is None:
            ts = datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S")
            filename = f"source_verification_batch_{ts}.json"

        payload = {
            "generated_at": datetime.now(tz=timezone.utc).isoformat(),
            "total_results": len(results),
            "verdict_counts": self._count_verdicts(results),
            "results": [r.to_dict() for r in results],
        }
        out_path = self.output_dir / filename
        out_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return out_path

    @staticmethod
    def _count_verdicts(
        results: List[SourceVerificationResult],
    ) -> Dict[str, int]:
        """Return a dict of verdict → count for a list of results."""
        counts: Dict[str, int] = {}
        for r in results:
            counts[r.verdict] = counts.get(r.verdict, 0) + 1
        return counts
