"""
Unit & Integration Tests for Telemetry and Synthesis Engine Distinction
------------------------------------------------------------------------
Tests verify that:
1. Gemini success sets synthesis_engine="gemini" and model_name="gemini-1.5-flash".
2. Gemini API failures gracefully fall back to synthesis_engine="local_fallback" with model_name=None.
3. Missing API key correctly initializes without a model and uses synthesis_engine="local_fallback".
4. Local fallback returns synthesis_engine="local_fallback" and model_name=None.
5. Orchestrator properly propagates synthesis_engine and model_name into Step 5 telemetry and top-level response.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

_current_dir = os.path.dirname(os.path.abspath(__file__))
_root_dir = os.path.dirname(_current_dir)
_src_dir = os.path.join(_root_dir, "src")
for _p in [_src_dir, _root_dir]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from agents.response_generation_agent import ResponseGenerationAgent
from orchestration.orchestrator import Milestone3Orchestrator


class TestSynthesisEngineTelemetry(unittest.TestCase):

    def setUp(self):
        self.sample_query = "What is the paid annual leave policy?"
        self.sample_query_classification = {
            "query": self.sample_query,
            "query_type": "factual",
            "classification_confidence": 0.95,
            "routing": "retrieval"
        }
        self.sample_retrieved_data = {
            "query": self.sample_query,
            "results": [
                {
                    "content": "All full-time employees are entitled to 20 days of paid Annual Leave per calendar year.",
                    "document_name": "hr_policy.txt",
                    "page": 1,
                    "section": "Annual Leave",
                    "chunk_id": "hr_policy.txt_chunk_0",
                    "relevance_score": 0.88
                }
            ],
            "result_count": 1
        }

    def test_gemini_success(self):
        """When Gemini API succeeds, synthesis_engine must be 'gemini' and model_name must be present."""
        agent = ResponseGenerationAgent(api_key="fake-test-key", model_name="gemini-1.5-flash")
        
        # Mock Gemini GenerativeModel
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Employees receive 20 days of paid annual leave per calendar year."
        mock_model.generate_content.return_value = mock_response
        agent.model = mock_model

        res = agent.generate_response(
            query=self.sample_query,
            query_classification=self.sample_query_classification,
            retrieved_data=self.sample_retrieved_data
        )

        self.assertEqual(res["synthesis_engine"], "gemini")
        self.assertEqual(res["model_name"], "gemini-1.5-flash")
        self.assertEqual(res["answer"], "Employees receive 20 days of paid annual leave per calendar year.")
        self.assertEqual(len(res["sources"]), 1)

    def test_gemini_failure_fallback(self):
        """When Gemini API call raises an exception, it must fall back to 'local_fallback' and model_name=None."""
        agent = ResponseGenerationAgent(api_key="fake-test-key", model_name="gemini-1.5-flash")
        
        mock_model = MagicMock()
        mock_model.generate_content.side_effect = Exception("API quota exceeded or network timeout")
        agent.model = mock_model

        res = agent.generate_response(
            query=self.sample_query,
            query_classification=self.sample_query_classification,
            retrieved_data=self.sample_retrieved_data
        )

        self.assertEqual(res["synthesis_engine"], "local_fallback")
        self.assertIsNone(res["model_name"])
        self.assertTrue(res["answer"].startswith("According to hr_policy.txt"))
        self.assertEqual(len(res["sources"]), 1)

    def test_gemini_empty_response_fallback(self):
        """When Gemini API returns an empty text response, fallback to local generation."""
        agent = ResponseGenerationAgent(api_key="fake-test-key", model_name="gemini-1.5-flash")
        
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "   "
        mock_model.generate_content.return_value = mock_response
        agent.model = mock_model

        res = agent.generate_response(
            query=self.sample_query,
            query_classification=self.sample_query_classification,
            retrieved_data=self.sample_retrieved_data
        )

        self.assertEqual(res["synthesis_engine"], "local_fallback")
        self.assertIsNone(res["model_name"])
        self.assertTrue(res["answer"].startswith("According to hr_policy.txt"))

    def test_missing_api_key(self):
        """When GEMINI_API_KEY is not provided, agent.model is None and synthesis_engine is 'local_fallback'."""
        with patch.dict(os.environ, {}, clear=True):
            agent = ResponseGenerationAgent(api_key=None)
            self.assertIsNone(agent.model)

            res = agent.generate_response(
                query=self.sample_query,
                query_classification=self.sample_query_classification,
                retrieved_data=self.sample_retrieved_data
            )

            self.assertEqual(res["synthesis_engine"], "local_fallback")
            self.assertIsNone(res["model_name"])

    def test_local_fallback_directly(self):
        """Direct local fallback without model returns local_fallback and valid answer."""
        agent = ResponseGenerationAgent(api_key=None)
        agent.model = None

        res = agent.generate_response(
            query=self.sample_query,
            query_classification=self.sample_query_classification,
            retrieved_data=self.sample_retrieved_data
        )

        self.assertEqual(res["synthesis_engine"], "local_fallback")
        self.assertIsNone(res["model_name"])
        self.assertIn("20 days of paid Annual Leave", res["answer"])
        self.assertEqual(res["confidence"]["label"], "High")

    def test_orchestrator_gemini_success_telemetry(self):
        """Orchestrator propagates gemini telemetry to Step 5 details and top-level response."""
        orchestrator = Milestone3Orchestrator()
        
        # Mock ResponseGenerationAgent on orchestrator
        mock_agent = MagicMock()
        mock_agent.generate_response.return_value = {
            "answer": "Mock Gemini synthesized response",
            "sources": [{"document_name": "hr_policy.txt", "page": 1, "chunk_id": "c1"}],
            "confidence": {"score": 0.88, "label": "High"},
            "synthesis_engine": "gemini",
            "model_name": "gemini-1.5-flash"
        }
        orchestrator.response_agent = mock_agent

        result = orchestrator.process_query(
            query="How many days of annual leave do employees get?",
            session_id="test_gemini_session"
        )

        # Check top-level response
        self.assertEqual(result["synthesis_engine"], "gemini")
        self.assertEqual(result["model_name"], "gemini-1.5-flash")

        # Check Step 5 telemetry details
        step5 = next(s for s in result["telemetry"]["pipeline_steps"] if s["step"] == 5)
        self.assertEqual(step5["status"], "success")
        self.assertEqual(step5["details"]["synthesis_engine"], "gemini")
        self.assertEqual(step5["details"]["model_name"], "gemini-1.5-flash")

    def test_orchestrator_local_fallback_telemetry(self):
        """Orchestrator propagates local_fallback telemetry to Step 5 details and top-level response."""
        orchestrator = Milestone3Orchestrator()
        orchestrator.response_agent.model = None  # Ensure fallback

        result = orchestrator.process_query(
            query="How many days of paid annual leave do employees receive per year?",
            session_id="test_fallback_session"
        )

        # Check top-level response
        self.assertEqual(result["synthesis_engine"], "local_fallback")
        self.assertIsNone(result["model_name"])

        # Check Step 5 telemetry details
        step5 = next(s for s in result["telemetry"]["pipeline_steps"] if s["step"] == 5)
        self.assertEqual(step5["status"], "success")
        self.assertEqual(step5["details"]["synthesis_engine"], "local_fallback")
        self.assertIsNone(step5["details"]["model_name"])

    def test_orchestrator_step5_exception_handling(self):
        """Orchestrator Step 5 error fallback properly sets synthesis_engine to local_fallback."""
        orchestrator = Milestone3Orchestrator()
        mock_agent = MagicMock()
        mock_agent.generate_response.side_effect = RuntimeError("Fatal generation agent crash")
        orchestrator.response_agent = mock_agent

        result = orchestrator.process_query(
            query="How many days of paid annual leave do employees receive per year?",
            session_id="test_crash_session"
        )

        # Check top-level response
        self.assertEqual(result["synthesis_engine"], "local_fallback")
        self.assertIsNone(result["model_name"])

        # Check Step 5 telemetry details
        step5 = next(s for s in result["telemetry"]["pipeline_steps"] if s["step"] == 5)
        self.assertEqual(step5["status"], "error_fallback")
        self.assertEqual(step5["details"]["synthesis_engine"], "local_fallback")
        self.assertIsNone(step5["details"]["model_name"])


if __name__ == "__main__":
    unittest.main()
