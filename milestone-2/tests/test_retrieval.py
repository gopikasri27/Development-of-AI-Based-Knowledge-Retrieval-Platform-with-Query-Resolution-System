"""
Test Suite for M2.2: Retrieval Agent
-----------------------------------
Validates semantic search, Top-K retrieval, cosine similarity ranking,
metadata preservation, and low-confidence filtering across both knowledge domains.
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
from agents.retrieval_agent import RetrievalAgent


class TestRetrievalAgent(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Set up an isolated test vector store directory
        cls.test_db_dir = os.path.join(parent_dir, "data", "test_vectorstore_m2_retrieval")
        cls.kb_dir = os.path.join(parent_dir, "knowledge_base")
        
        # Reset directory if exists
        if os.path.exists(cls.test_db_dir):
            shutil.rmtree(cls.test_db_dir, ignore_errors=True)
            
        cls.vector_store = VectorStoreManager(
            collection_name="test_m2_retrieval_collection",
            persist_directory=cls.test_db_dir
        )
        # Index both knowledge domain files
        cls.vector_store.index_text_file(
            os.path.join(cls.kb_dir, "hr_policy.txt"),
            document_name="hr_policy.txt"
        )
        cls.vector_store.index_text_file(
            os.path.join(cls.kb_dir, "product_manual.txt"),
            document_name="product_manual.txt"
        )
        cls.agent = RetrievalAgent(vector_store=cls.vector_store, top_k=3, confidence_threshold=0.50)

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.test_db_dir):
            shutil.rmtree(cls.test_db_dir, ignore_errors=True)

    def test_semantic_search_hr_domain_factual(self):
        """Domain 1: HR Policy - Factual Retrieval"""
        query = "How many days of paid annual leave and sick leave do employees receive?"
        retrieval_output = self.agent.retrieve(query=query)

        self.assertEqual(retrieval_output["query"], query)
        self.assertGreater(retrieval_output["result_count"], 0)
        
        top_result = retrieval_output["results"][0]
        self.assertEqual(top_result["document_name"], "hr_policy.txt")
        self.assertIn("leave", top_result["section"].lower())
        self.assertGreaterEqual(top_result["relevance_score"], 0.60)
        self.assertIn("Annual Leave", top_result["content"])

    def test_semantic_search_tech_domain_procedural(self):
        """Domain 2: Tech Manual - Procedural Retrieval"""
        query = "How to install and configure CloudSync Pro using install.sh"
        retrieval_output = self.agent.retrieve(query=query)

        self.assertEqual(retrieval_output["query"], query)
        self.assertGreater(retrieval_output["result_count"], 0)
        
        top_result = retrieval_output["results"][0]
        self.assertEqual(top_result["document_name"], "product_manual.txt")
        self.assertIn("Installation", top_result["section"])
        self.assertGreaterEqual(top_result["relevance_score"], 0.60)
        self.assertIn("cloudsync-admin", top_result["content"])

    def test_semantic_search_comparative(self):
        """Domain 2: Tech Manual - Comparative Retrieval"""
        query = "Difference between CloudSync Standard and Pro edition TPS throughput"
        retrieval_output = self.agent.retrieve(query=query)

        self.assertGreater(retrieval_output["result_count"], 0)
        top_result = retrieval_output["results"][0]
        self.assertEqual(top_result["document_name"], "product_manual.txt")
        self.assertIn("Comparison", top_result["section"])
        self.assertIn("50,000 TPS", top_result["content"])

    def test_top_k_parameter(self):
        """Verifies configurable Top-K chunk retrieval"""
        query = "What is the policy on leave and holidays?"
        res_k1 = self.agent.retrieve(query=query, top_k=1, confidence_threshold=0.0)
        res_k3 = self.agent.retrieve(query=query, top_k=3, confidence_threshold=0.0)

        self.assertEqual(len(res_k1["results"]), 1)
        self.assertEqual(len(res_k3["results"]), 3)

    def test_relevance_ranking(self):
        """Verifies chunks are sorted in descending order of relevance score"""
        query = "remote hybrid work core hours schedule"
        retrieval_output = self.agent.retrieve(query=query, top_k=4, confidence_threshold=0.0)
        scores = [r["relevance_score"] for r in retrieval_output["results"]]

        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_metadata_preservation(self):
        """Verifies all required metadata fields exist on every retrieved chunk"""
        query = "health insurance specialist co-pay"
        retrieval_output = self.agent.retrieve(query=query)

        for r in retrieval_output["results"]:
            self.assertIn("content", r)
            self.assertIn("document_name", r)
            self.assertIn("page", r)
            self.assertIn("section", r)
            self.assertIn("chunk_id", r)
            self.assertIn("relevance_score", r)
            self.assertIsInstance(r["page"], int)
            self.assertIsInstance(r["relevance_score"], float)

    def test_unavailable_out_of_domain_query(self):
        """Verifies that completely irrelevant queries yield zero results above confidence cutoff"""
        query = "quantum gravitational wave astrophysics black hole collision"
        retrieval_output = self.agent.retrieve(query=query, confidence_threshold=0.65)

        self.assertEqual(retrieval_output["result_count"], 0)
        self.assertEqual(len(retrieval_output["results"]), 0)


if __name__ == "__main__":
    unittest.main()
