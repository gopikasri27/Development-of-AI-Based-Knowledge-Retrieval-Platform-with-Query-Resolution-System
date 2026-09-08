"""
Test Suite for M2.4: Multi-Agent Orchestration Layer
----------------------------------------------------
Validates complete sequential multi-agent coordination, inter-agent data passing,
fallback handling for component failures, and end-to-end execution across both knowledge domains.
"""

import os
import sys
import unittest
import shutil

# Add project root to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from retrieval.vector_store import VectorStoreManager
from agents.query_understanding_agent import QueryUnderstandingAgent
from agents.retrieval_agent import RetrievalAgent
from agents.response_generation_agent import ResponseGenerationAgent, INSUFFICIENT_INFO_MESSAGE
from orchestration.agent_orchestrator import MultiAgentOrchestrator


class TestMultiAgentOrchestration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Set up an isolated test vector store directory
        cls.test_db_dir = os.path.join(parent_dir, "data", "test_vectorstore_m2_orchestration")
        cls.kb_dir = os.path.join(parent_dir, "knowledge_base")

        if os.path.exists(cls.test_db_dir):
            shutil.rmtree(cls.test_db_dir, ignore_errors=True)

        cls.vector_store = VectorStoreManager(
            collection_name="test_m2_orchestrator_collection",
            persist_directory=cls.test_db_dir
        )
        cls.vector_store.index_text_file(
            os.path.join(cls.kb_dir, "hr_policy.txt"),
            document_name="hr_policy.txt"
        )
        cls.vector_store.index_text_file(
            os.path.join(cls.kb_dir, "product_manual.txt"),
            document_name="product_manual.txt"
        )

        cls.query_agent = QueryUnderstandingAgent()
        cls.retrieval_agent = RetrievalAgent(vector_store=cls.vector_store, top_k=3, confidence_threshold=0.50)
        cls.response_agent = ResponseGenerationAgent()

        cls.orchestrator = MultiAgentOrchestrator(
            query_agent=cls.query_agent,
            retrieval_agent=cls.retrieval_agent,
            response_agent=cls.response_agent
        )

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.test_db_dir):
            shutil.rmtree(cls.test_db_dir, ignore_errors=True)

    def test_e2e_factual_hr_domain(self):
        """End-to-End: Domain 1 (HR Policy) Factual Query Resolution"""
        query = "How many days of paid annual leave do full-time employees get?"
        result = self.orchestrator.process_query(query)

        self.assertEqual(result["query"], query)
        self.assertEqual(result["query_type"], "factual")
        self.assertGreater(len(result["sources"]), 0)
        self.assertEqual(result["sources"][0]["document_name"], "hr_policy.txt")
        self.assertIn("20 days", result["answer"])
        self.assertIn(result["confidence"]["label"], ["High", "Medium"])
        self.assertIn("telemetry", result)
        self.assertEqual(len(result["telemetry"]["pipeline_steps"]), 3)

    def test_e2e_procedural_tech_domain(self):
        """End-to-End: Domain 2 (Tech Manual) Procedural Query Resolution"""
        query = "How do I install and configure CloudSync Pro cluster?"
        result = self.orchestrator.process_query(query)

        self.assertEqual(result["query"], query)
        self.assertEqual(result["query_type"], "procedural")
        self.assertGreater(len(result["sources"]), 0)
        self.assertEqual(result["sources"][0]["document_name"], "product_manual.txt")
        self.assertIn("cloudsync", result["answer"].lower())
        self.assertIn(result["confidence"]["label"], ["High", "Medium"])

    def test_e2e_comparative_tech_domain(self):
        """End-to-End: Domain 2 (Tech Manual) Comparative Query Resolution"""
        query = "Compare CloudSync Standard vs CloudSync Pro edition features"
        result = self.orchestrator.process_query(query)

        self.assertEqual(result["query"], query)
        self.assertEqual(result["query_type"], "comparative")
        self.assertGreater(len(result["sources"]), 0)
        self.assertEqual(result["sources"][0]["document_name"], "product_manual.txt")
        self.assertIn(result["confidence"]["label"], ["High", "Medium"])

    def test_e2e_ambiguous_query_handling(self):
        """End-to-End: Ambiguous Query marked for clarification and safe handling"""
        query = "help"
        result = self.orchestrator.process_query(query)

        self.assertEqual(result["query"], query)
        self.assertEqual(result["query_type"], "ambiguous")
        self.assertEqual(result["answer"], INSUFFICIENT_INFO_MESSAGE)
        self.assertEqual(len(result["sources"]), 0)
        self.assertEqual(result["confidence"]["label"], "Low")

    def test_e2e_unavailable_out_of_domain_query(self):
        """End-to-End: Out-of-domain query with no matching knowledge chunks"""
        query = "What is the orbital speed of the International Space Station?"
        result = self.orchestrator.process_query(query)

        self.assertEqual(result["answer"], INSUFFICIENT_INFO_MESSAGE)
        self.assertEqual(len(result["sources"]), 0)
        self.assertEqual(result["confidence"]["label"], "Low")

    def test_orchestration_classification_failure_resilience(self):
        """Validates that orchestrator recovers gracefully if Query Agent fails"""
        class FaultyQueryAgent:
            def analyze_query(self, q):
                raise RuntimeError("Simulated query classification failure")

        faulty_orch = MultiAgentOrchestrator(
            query_agent=FaultyQueryAgent(),
            retrieval_agent=self.retrieval_agent,
            response_agent=self.response_agent
        )
        result = faulty_orch.process_query("What is the annual leave allowance?")
        self.assertIn("answer", result)
        self.assertEqual(result["telemetry"]["pipeline_steps"][0]["status"], "error_fallback")

    def test_orchestration_retrieval_failure_resilience(self):
        """Validates that orchestrator recovers gracefully if Retrieval Agent fails"""
        class FaultyRetrievalAgent:
            def retrieve(self, query, query_classification=None):
                raise ConnectionError("Simulated database timeout")

        faulty_orch = MultiAgentOrchestrator(
            query_agent=self.query_agent,
            retrieval_agent=FaultyRetrievalAgent(),
            response_agent=self.response_agent
        )
        result = faulty_orch.process_query("How to install CloudSync Pro?")
        self.assertEqual(result["answer"], INSUFFICIENT_INFO_MESSAGE)
        self.assertEqual(result["confidence"]["label"], "Low")
        self.assertEqual(result["telemetry"]["pipeline_steps"][1]["status"], "error_fallback")

    def test_orchestration_generation_failure_resilience(self):
        """Validates that orchestrator recovers gracefully if Response Agent fails"""
        class FaultyResponseAgent:
            def generate_response(self, query, query_classification=None, retrieved_data=None):
                raise ValueError("Simulated LLM synthesis exception")

        faulty_orch = MultiAgentOrchestrator(
            query_agent=self.query_agent,
            retrieval_agent=self.retrieval_agent,
            response_agent=FaultyResponseAgent()
        )
        result = faulty_orch.process_query("How many days of annual leave?")
        self.assertEqual(result["answer"], INSUFFICIENT_INFO_MESSAGE)
        self.assertEqual(result["confidence"]["label"], "Low")
        self.assertEqual(result["telemetry"]["pipeline_steps"][2]["status"], "error_fallback")


if __name__ == "__main__":
    unittest.main()
