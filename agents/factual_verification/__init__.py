"""
agents/factual_verification/__init__.py

Sub-package for the Factual Verification Agent.

Public API:
    FactualVerificationAgent
    FactualVerificationResult
"""

from agents.factual_verification.factual_agent import (
    FactualVerificationAgent,
    FactualVerificationResult,
)

__all__ = ["FactualVerificationAgent", "FactualVerificationResult"]

