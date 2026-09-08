"""
Test Suite for M2.3: Response Generation Agent
----------------------------------------------
Validates grounded generation, source attribution mapping, confidence calculations,
insufficient evidence handling, and anti-hallucination guardrails.
"""

import os
import sys
import unittest

# Add project root to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from agents.response_generation_agent import ResponseGenerationAgent, INSUFFICIENT_INFO_MESSAGE


class TestResponseGenerationAgent(unittest.TestCase):
    def setUp(self):
        self.agent = ResponseGenerationAgent()

    def test_grounded_factual_response(self):
        """Validates factual response synthesis, source attribution, and high confidence"""
        query = "How many days of annual leave do employees receive?"
        query_classification = {
            "query": query,
            "query_type": "factual",
            "classification_confidence": 0.95,
            "routing": "retrieval"
        }
        retrieved_data = {
            "query": query,
            "results": [
                {
                    "content": "All full-time employees at GlobalTech are entitled to 20 days of paid Annual Leave per calendar year. Annual leave accrues on the first day of each month at a rate of 1.66 days.",
                    "document_name": "hr_policy.txt",
                    "page": 1,
                    "section": "Annual Leave and Sick Leave Policy",
                    "chunk_id": "hr_policy.txt_chunk_0",
                    "relevance_score": 0.885
                }
            ],
            "result_count": 1
        }

        response = self.agent.generate_response(
            query=query,
            query_classification=query_classification,
            retrieved_data=retrieved_data
        )

        self.assertIn("20 days", response["answer"])
        self.assertEqual(len(response["sources"]), 1)
        self.assertEqual(response["sources"][0]["document_name"], "hr_policy.txt")
        self.assertEqual(response["sources"][0]["chunk_id"], "hr_policy.txt_chunk_0")
        self.assertEqual(response["confidence"]["label"], "High")
        self.assertAlmostEqual(response["confidence"]["score"], 0.885, places=3)

    def test_grounded_procedural_response(self):
        """Validates procedural response generation with step-by-step guidance"""
        query = "What are the steps to install CloudSync Pro?"
        query_classification = {
            "query": query,
            "query_type": "procedural",
            "classification_confidence": 0.92,
            "routing": "retrieval"
        }
        retrieved_data = {
            "query": query,
            "results": [
                {
                    "content": "Follow these step-by-step instructions to configure CloudSync Pro:\nStep 1: Download the binary bundle using curl.\nStep 2: Initialize the cluster configuration.",
                    "document_name": "product_manual.txt",
                    "page": 1,
                    "section": "Installation and Initial Configuration Procedure",
                    "chunk_id": "product_manual.txt_chunk_1",
                    "relevance_score": 0.890
                }
            ],
            "result_count": 1
        }

        response = self.agent.generate_response(
            query=query,
            query_classification=query_classification,
            retrieved_data=retrieved_data
        )

        self.assertIn("Step 1", response["answer"])
        self.assertEqual(response["sources"][0]["document_name"], "product_manual.txt")
        self.assertEqual(response["confidence"]["label"], "High")

    def test_grounded_comparative_response(self):
        """Validates comparative response generation"""
        query = "Compare CloudSync Standard and Pro edition throughput"
        query_classification = {
            "query": query,
            "query_type": "comparative",
            "classification_confidence": 0.94,
            "routing": "retrieval"
        }
        retrieved_data = {
            "query": query,
            "results": [
                {
                    "content": "- Throughput: Standard Edition handles up to 5,000 transactions per second (TPS), whereas Pro Edition scales to 50,000 TPS.\n- Encryption: Standard provides AES-128; Pro provides AES-256-GCM.",
                    "document_name": "product_manual.txt",
                    "page": 1,
                    "section": "CloudSync Standard vs CloudSync Pro Edition Comparison",
                    "chunk_id": "product_manual.txt_chunk_2",
                    "relevance_score": 0.865
                }
            ],
            "result_count": 1
        }

        response = self.agent.generate_response(
            query=query,
            query_classification=query_classification,
            retrieved_data=retrieved_data
        )

        self.assertIn("5,000", response["answer"])
        self.assertIn("50,000", response["answer"])
        self.assertEqual(response["confidence"]["label"], "High")

    def test_insufficient_information_empty_results(self):
        """Validates that empty retrieved context produces standard insufficient info message"""
        query = "What is the stock price prediction for next month?"
        query_classification = {
            "query": query,
            "query_type": "factual",
            "classification_confidence": 0.80,
            "routing": "retrieval"
        }
        retrieved_data = {"query": query, "results": [], "result_count": 0}

        response = self.agent.generate_response(
            query=query,
            query_classification=query_classification,
            retrieved_data=retrieved_data
        )

        self.assertEqual(response["answer"], INSUFFICIENT_INFO_MESSAGE)
        self.assertEqual(len(response["sources"]), 0)
        self.assertEqual(response["confidence"]["label"], "Low")
        self.assertEqual(response["confidence"]["score"], 0.0)

    def test_low_confidence_retrieval_guardrail(self):
        """Validates that retrieval scores below 0.50 trigger insufficient information fallback"""
        query = "random query with irrelevant match"
        query_classification = {
            "query": query,
            "query_type": "factual",
            "classification_confidence": 0.60,
            "routing": "retrieval"
        }
        retrieved_data = {
            "query": query,
            "results": [
                {
                    "content": "Irrelevant text excerpt...",
                    "document_name": "hr_policy.txt",
                    "page": 1,
                    "section": "General",
                    "chunk_id": "hr_policy.txt_chunk_0",
                    "relevance_score": 0.320 # Below 0.50 threshold
                }
            ],
            "result_count": 1
        }

        response = self.agent.generate_response(
            query=query,
            query_classification=query_classification,
            retrieved_data=retrieved_data
        )

        self.assertEqual(response["answer"], INSUFFICIENT_INFO_MESSAGE)
        self.assertEqual(len(response["sources"]), 0)
        self.assertEqual(response["confidence"]["label"], "Low")


if __name__ == "__main__":
    unittest.main()
