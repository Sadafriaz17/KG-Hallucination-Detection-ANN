"""
utils/data_loader.py

Data loading utilities for the KG Hallucination Detection pipeline.

This module provides a DataLoader class that:
    - Loads Knowledge Graph triples from dataset/triples.csv.
    - Loads ground-truth labels from dataset/ground_truth.csv.
    - Reads raw source documents from dataset/source_documents/.
    - Validates required columns on every load.

Usage:
    from utils.data_loader import DataLoader

    loader = DataLoader()
    triples       = loader.load_triples()
    ground_truth  = loader.load_ground_truth()
    text          = loader.load_source_document("source_01")
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, List, Optional

from config.config import Config


class DataLoader:
    """
    Utility class for loading and validating project data files.

    Attributes:
        cfg (Config): Project configuration instance.
    """

    # Required columns in each CSV file.
    TRIPLES_REQUIRED_COLUMNS: tuple = (
        "triple_id",
        "subject",
        "relation",
        "object",
        "source_document_id",
        "source_document_url",
        "source_text",
    )

    GROUND_TRUTH_REQUIRED_COLUMNS: tuple = (
        "triple_id",
        "final_label",
        "verification_evidence",
        "verification_reference",
    )

    def __init__(self, cfg: Optional[Config] = None) -> None:
        """
        Initialise DataLoader with the project configuration.

        Args:
            cfg (Config, optional): Configuration object. Defaults to Config().
        """
        self.cfg = cfg or Config()

    # ------------------------------------------------------------------
    # Public loaders
    # ------------------------------------------------------------------

    def load_triples(self) -> List[Dict[str, str]]:
        """
        Load Knowledge Graph triples from triples.csv.

        Returns:
            List[Dict[str, str]]: One dict per triple row, keys are column
            names from the CSV header.

        Raises:
            FileNotFoundError: If triples.csv does not exist at the
                configured path.
            ValueError: If any required column is absent from the file.
        """
        path = self.cfg.TRIPLES_CSV
        if not path.exists():
            raise FileNotFoundError(
                f"triples.csv not found at: {path}\n"
                "Ensure the dataset has been placed inside dataset/."
            )

        with open(path, encoding="utf-8-sig", newline="") as fh:
            rows = list(csv.DictReader(fh))

        self._validate_columns(rows, self.TRIPLES_REQUIRED_COLUMNS, "triples.csv")
        return rows

    def load_ground_truth(self) -> List[Dict[str, str]]:
        """
        Load ground-truth labels from ground_truth.csv.

        .. warning::
            This file must **never** be passed to any verification agent as
            input.  It is used only for evaluation after agent predictions
            have been produced independently.

        Returns:
            List[Dict[str, str]]: One dict per ground-truth row, keys are
            column names from the CSV header.

        Raises:
            FileNotFoundError: If ground_truth.csv does not exist.
            ValueError: If any required column is absent.
        """
        path = self.cfg.GROUND_TRUTH_CSV
        if not path.exists():
            raise FileNotFoundError(
                f"ground_truth.csv not found at: {path}\n"
                "Ensure the dataset has been placed inside dataset/."
            )

        with open(path, encoding="utf-8-sig", newline="") as fh:
            rows = list(csv.DictReader(fh))

        self._validate_columns(
            rows, self.GROUND_TRUTH_REQUIRED_COLUMNS, "ground_truth.csv"
        )
        return rows

    def load_source_document(self, source_document_id: str) -> str:
        """
        Read a source document by its ID (filename without extension).

        Args:
            source_document_id (str): The source document ID as it appears
                in the ``source_document_id`` column of triples.csv,
                e.g. ``"source_01"``.

        Returns:
            str: The full UTF-8 text content of the source document.

        Raises:
            FileNotFoundError: If no matching ``.txt`` file exists inside
                ``source_documents/``.
            ValueError: If ``source_document_id`` is empty or None.
        """
        if not source_document_id:
            raise ValueError(
                "source_document_id must be a non-empty string."
            )

        doc_path = self.cfg.SOURCE_DOCUMENTS_DIR / f"{source_document_id}.txt"
        if not doc_path.exists():
            raise FileNotFoundError(
                f"Source document not found: {doc_path}\n"
                f"Expected a file named '{source_document_id}.txt' inside "
                f"{self.cfg.SOURCE_DOCUMENTS_DIR}."
            )

        return doc_path.read_text(encoding="utf-8")

    def list_source_document_ids(self) -> List[str]:
        """
        Return the IDs of all source documents currently on disk.

        Returns:
            List[str]: Sorted list of document IDs (filenames without
            ``.txt`` extension).
        """
        return sorted(
            p.stem
            for p in self.cfg.SOURCE_DOCUMENTS_DIR.glob("*.txt")
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _validate_columns(
        self,
        rows: List[Dict],
        required: tuple,
        filename: str,
    ) -> None:
        """
        Validate that all required columns are present.

        Args:
            rows (List[Dict]): Rows returned by csv.DictReader.
            required (tuple): Column names that must be present.
            filename (str): CSV filename used in error messages.

        Raises:
            ValueError: If any required column is missing.
        """
        if not rows:
            return  # Empty file — nothing to validate yet.
        actual = set(rows[0].keys())
        missing = set(required) - actual
        if missing:
            raise ValueError(
                f"'{filename}' is missing required columns: "
                f"{sorted(missing)}"
            )
