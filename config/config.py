"""
config/config.py

Central configuration for the KG Hallucination Detection pipeline.

All file paths, model settings, and environment variable names are
defined here. Actual secret values (API keys, tokens) must be stored
in a .env file and loaded at runtime — never hardcoded in this file.

Usage:
    from config.config import Config

    cfg = Config()
    print(cfg.DATASET_DIR)
"""

from pathlib import Path

# ---------------------------------------------------------------------------
# Project root — resolved relative to this file's location.
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Config:
    """
    Central configuration object.

    All paths are absolute and resolved from the project root.
    External service settings reference environment variable names; optional
    values may be set in the .env file (never committed to git).
    """

    # -----------------------------------------------------------------------
    # Dataset paths
    # -----------------------------------------------------------------------
    DATASET_DIR: Path = PROJECT_ROOT / "dataset"
    SOURCE_DOCUMENTS_DIR: Path = DATASET_DIR / "source_documents"
    TRIPLES_CSV: Path = DATASET_DIR / "triples.csv"
    GROUND_TRUTH_CSV: Path = DATASET_DIR / "ground_truth.csv"

    # -----------------------------------------------------------------------
    # Output paths
    # -----------------------------------------------------------------------
    OUTPUTS_DIR: Path = PROJECT_ROOT / "outputs"
    SOURCE_VERIFICATION_OUTPUT_DIR: Path = OUTPUTS_DIR / "source_verification"
    FACTUAL_VERIFICATION_OUTPUT_DIR: Path = OUTPUTS_DIR / "factual_verification"

    # -----------------------------------------------------------------------
    # Environment variable names for optional external service settings.
    # -----------------------------------------------------------------------
    # -----------------------------------------------------------------------
    WIKIDATA_USER_AGENT_ENV: str = "WIKIDATA_USER_AGENT"

    # -----------------------------------------------------------------------
    # Label definitions
    # -----------------------------------------------------------------------
    FINAL_LABELS: tuple = (
        "SOURCE_SUPPORTED",
        "TRUE_BUT_SOURCE_UNSUPPORTED",
        "FACTUALLY_INCORRECT",
        "INSUFFICIENT_EVIDENCE",
    )

    SOURCE_VERDICTS: tuple = (
        "SUPPORTED",
        "CONTRADICTED",
        "NOT_MENTIONED",
    )

    FACTUAL_VERDICTS: tuple = (
        "FACTUALLY_CORRECT",
        "FACTUALLY_INCORRECT",
        "INSUFFICIENT_EVIDENCE",
    )

