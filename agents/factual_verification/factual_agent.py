"""
agents/factual_verification/factual_agent.py

Factual Verification Agent — Placeholder

=============================================================================
RESPONSIBILITY (Member 1)
=============================================================================

This agent independently checks whether a Knowledge Graph triple is factually
correct using reliable external knowledge references, entirely independent of
the source document associated with the triple.

For each triple provided, it will:
    1. Query one or more external knowledge bases (e.g. Wikidata, Wikipedia API).
    2. Retrieve relevant factual information about the subject–relation–object.
    3. Determine one of three verdicts:
        - TRUE    : The triple is factually correct according to external sources.
        - FALSE   : The triple is factually incorrect according to external sources.
        - UNKNOWN : External sources do not contain enough information to decide.
    4. Return a structured result for downstream label aggregation.

=============================================================================
EXPECTED OUTPUT FORMAT (per triple)
=============================================================================

{
    "triple_id"  : str,   # e.g. "T001"
    "verdict"    : str,   # "TRUE" | "FALSE" | "UNKNOWN"
    "confidence" : float, # 0.0 – 1.0
    "evidence"   : str,   # Relevant text retrieved from external reference
    "reference"  : str    # Citation / URL of the external knowledge source
}

=============================================================================
IMPLEMENTATION NOTES (TODO)
=============================================================================

- Do NOT implement external API calls here until the pipeline is ready.
- Potential external sources: Wikidata SPARQL endpoint, Wikipedia REST API.
- API keys / endpoints must be loaded from config/config.py and .env — never
  hardcoded in this file.
- This agent feeds its verdict into the ground-truth label preparation step
  alongside the Source Verification Agent's output.
- Results will be written to: outputs/factual_verification/

=============================================================================
"""


class FactualVerificationAgent:
    """
    Placeholder class for the Factual Verification Agent.

    This agent will independently verify the factual correctness of
    Knowledge Graph triples using external knowledge references.

    Attributes:
        output_dir (str): Path where verification results will be saved.
    """

    def __init__(self, output_dir: str):
        """
        Initialise the Factual Verification Agent.

        Args:
            output_dir (str): Path to outputs/factual_verification/.
        """
        self.output_dir = output_dir
        # TODO: Initialise external knowledge source clients here.

    def verify(self, triple: dict) -> dict:
        """
        Verify the factual correctness of a single triple.

        Args:
            triple (dict): A dictionary with keys:
                - triple_id
                - subject
                - relation
                - object

        Returns:
            dict: Verification result with keys:
                - triple_id
                - verdict    ("TRUE" | "FALSE" | "UNKNOWN")
                - confidence (float, 0.0–1.0)
                - evidence   (str)
                - reference  (str)

        Raises:
            NotImplementedError: Until this method is implemented.
        """
        raise NotImplementedError(
            "FactualVerificationAgent.verify() is not yet implemented. "
            "Implement external knowledge source querying and verdict logic here."
        )

    def run_batch(self, triples: list) -> list:
        """
        Verify a list of triples and return a list of results.

        Args:
            triples (list[dict]): List of triple dictionaries.

        Returns:
            list[dict]: List of verification result dictionaries.

        Raises:
            NotImplementedError: Until this method is implemented.
        """
        raise NotImplementedError(
            "FactualVerificationAgent.run_batch() is not yet implemented."
        )

