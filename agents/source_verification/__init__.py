"""
agents/source_verification/__init__.py

Sub-package for the Source Verification Agent.

Public API
----------
    SourceVerificationAgent  : The agent class.
    SourceVerificationResult : Dataclass returned by verify() / run_batch().

Usage
-----
    from agents.source_verification import SourceVerificationAgent

    agent = SourceVerificationAgent()
    result = agent.verify(triple_dict)
    print(result.verdict, result.confidence)
"""

from agents.source_verification.source_agent import (
    SourceVerificationAgent,
    SourceVerificationResult,
)

__all__ = ["SourceVerificationAgent", "SourceVerificationResult"]
