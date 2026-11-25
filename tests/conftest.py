"""
tests/conftest.py

Pytest configuration for the KG Hallucination Detection test suite.

Adds the project root to sys.path so that imports such as
    from agents.source_verification import SourceVerificationAgent
work correctly when running pytest from any working directory.
"""

import sys
from pathlib import Path

# Project root is one level above this conftest.py file.
PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

