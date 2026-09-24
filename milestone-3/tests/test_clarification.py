"""
Unit Tests for Clarification Agent (M3.1)
----------------------------------------
Tests ambiguity detection, incomplete queries, context dependency, multi-part query logic,
clear query pass-through, and query refinement.
"""

import sys
import os
import unittest

# Ensure path resolution
current_dir = os.path.dirname(os.path.abspath(__file__))
m3_dir = os.path.dirname(current_dir)
root_dir = os.path.dirname(m3_dir)
for p in [m3_dir, root_dir]:
    if p not in sys.path:
        sys.path.insert(0, p)

from agents.clarification_agent import ClarificationAgent


class TestClarificationAgent(unittest.TestCase):

    def setUp(self):
        self.agent = ClarificationAgent()

    def test_ambiguous_query_detection(self):
        """Test detection of vague/ambiguous query like 'Tell me about cloud.'"""
        res = self.agent.evaluate_query("Tell me about cloud.")
        self.assertTrue(res["clarification_required"])
        self.assertEqual(res["ambiguity_type"], "multi_interpretation")
        self.assertIn("cloud computing", res["clarification_question"].lower())

    def test_incomplete_query_detection(self):
        """Test single keyword underspecified query."""
        res = self.agent.evaluate_query("leave")
        self.assertTrue(res["clarification_required"])
        self.assertEqual(res["ambiguity_type"], "vague_term")
        self.assertIsNotNone(res["clarification_question"])

    def test_context_dependent_query_missing_memory(self):
        """Test context-dependent query when previous memory is missing."""
        memory_ctx = {"context_found": False, "is_context_dependent": True}
        res = self.agent.evaluate_query("What are its benefits?", memory_context=memory_ctx)
        self.assertTrue(res["clarification_required"])
        self.assertEqual(res["ambiguity_type"], "missing_context")

    def test_multipart_query_with_clear_entities(self):
        """Test multi-part query with explicit entities processes directly without clarification."""
        query = "Compare AWS and Azure and tell me which one is cheaper and how to deploy it."
        res = self.agent.evaluate_query(query)
        self.assertFalse(res["clarification_required"])

    def test_clear_query(self):
        """Test clear factual query does not require clarification."""
        res = self.agent.evaluate_query("How many days of paid annual leave do employees receive per year?")
        self.assertFalse(res["clarification_required"])
        self.assertIsNone(res["clarification_question"])

    def test_refine_query(self):
        """Test refinement logic combining original query + clarification response."""
        refined = self.agent.refine_query(
            original_query="Tell me about cloud.",
            clarification_response="Cloud computing."
        )
        self.assertEqual(refined, "Tell me about cloud computing.")


if __name__ == "__main__":
    unittest.main()
