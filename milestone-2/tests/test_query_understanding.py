"""
Test Suite for M2.1: Query Understanding Agent
----------------------------------------------
Validates classification into factual, procedural, comparative, and ambiguous
across both Milestone 1 knowledge domains (HR Policy & Technical Manual).
"""

import os
import sys
import unittest

# Add project root to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from agents.query_understanding_agent import QueryUnderstandingAgent


class TestQueryUnderstandingAgent(unittest.TestCase):
    def setUp(self):
        self.agent = QueryUnderstandingAgent()

    def test_factual_query_hr_domain(self):
        """Domain 1: HR Policy - Factual Lookup"""
        query = "How many days of paid annual leave do full-time employees receive?"
        result = self.agent.analyze_query(query)

        self.assertEqual(result["query"], query)
        self.assertEqual(result["query_type"], "factual")
        self.assertGreaterEqual(result["classification_confidence"], 0.70)
        self.assertEqual(result["routing"], "retrieval")

    def test_factual_query_tech_domain(self):
        """Domain 2: Technical Product - Factual Lookup"""
        query = "What are the system requirements and memory needed for CloudSync Pro?"
        result = self.agent.analyze_query(query)

        self.assertEqual(result["query"], query)
        self.assertEqual(result["query_type"], "factual")
        self.assertGreaterEqual(result["classification_confidence"], 0.70)
        self.assertEqual(result["routing"], "retrieval")

    def test_procedural_query_hr_domain(self):
        """Domain 1: HR Policy - Procedural Workflow"""
        query = "How do I submit a medical certificate for sick leave exceeding 3 days?"
        result = self.agent.analyze_query(query)

        self.assertEqual(result["query"], query)
        self.assertEqual(result["query_type"], "procedural")
        self.assertGreaterEqual(result["classification_confidence"], 0.70)
        self.assertEqual(result["routing"], "retrieval")

    def test_procedural_query_tech_domain(self):
        """Domain 2: Technical Product - Procedural Steps"""
        query = "What are the step-by-step instructions to install and configure CloudSync Pro?"
        result = self.agent.analyze_query(query)

        self.assertEqual(result["query"], query)
        self.assertEqual(result["query_type"], "procedural")
        self.assertGreaterEqual(result["classification_confidence"], 0.70)
        self.assertEqual(result["routing"], "retrieval")

    def test_comparative_query_tech_domain(self):
        """Domain 2: Technical Product - Edition Comparison"""
        query = "Compare CloudSync Standard vs CloudSync Pro edition throughput and encryption"
        result = self.agent.analyze_query(query)

        self.assertEqual(result["query"], query)
        self.assertEqual(result["query_type"], "comparative")
        self.assertGreaterEqual(result["classification_confidence"], 0.70)
        self.assertEqual(result["routing"], "retrieval")

    def test_ambiguous_queries(self):
        """Vague, uninformative, or ambiguous queries"""
        queries = ["help", "tell me something", "policy", "stuff and things", "what can you do"]
        for q in queries:
            result = self.agent.analyze_query(q)
            self.assertEqual(result["query"], q)
            self.assertEqual(result["query_type"], "ambiguous")
            self.assertEqual(result["routing"], "clarification")
            self.assertGreaterEqual(result["classification_confidence"], 0.70)

    def test_empty_and_whitespace_query(self):
        """Empty or blank inputs"""
        for empty_q in ["", "   ", "\t\n"]:
            result = self.agent.analyze_query(empty_q)
            self.assertEqual(result["query_type"], "ambiguous")
            self.assertEqual(result["routing"], "clarification")


if __name__ == "__main__":
    unittest.main()
