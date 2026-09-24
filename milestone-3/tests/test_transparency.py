"""
Unit Tests for Response Transparency Panel & Metadata Structure (M3.4)
----------------------------------------------------------------------
Tests actual source document mapping, chunk IDs, similarity scores,
confidence indicators, and no-result / low-confidence transparency info.
"""

import sys
import os
import unittest
import importlib.util

current_dir = os.path.dirname(os.path.abspath(__file__))
m3_dir = os.path.dirname(current_dir)
root_dir = os.path.dirname(m3_dir)
m2_dir = os.path.join(root_dir, "milestone-2")

for p in [m2_dir, m3_dir, root_dir]:
    if p not in sys.path:
        sys.path.insert(0, p)

import agents
if hasattr(agents, "__path__"):
    for dir_path in [os.path.join(m2_dir, "agents"), os.path.join(m3_dir, "agents")]:
        if dir_path not in agents.__path__:
            agents.__path__.append(dir_path)

orchestration_path = os.path.join(m3_dir, "orchestration", "milestone3_orchestrator.py")
spec = importlib.util.spec_from_file_location("milestone3_orchestrator", orchestration_path)
m3_orch_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m3_orch_module)
Milestone3Orchestrator = m3_orch_module.Milestone3Orchestrator


class TestTransparencyPanel(unittest.TestCase):

    def setUp(self):
        self.orchestrator = Milestone3Orchestrator()

    def test_transparency_metadata_structure(self):
        """Test that returned payload contains non-fabricated metadata."""
        res = self.orchestrator.process_query(
            query="How many days of paid annual leave do employees receive per year?",
            session_id="transparency_test_01"
        )
        self.assertIn("transparency", res)
        transparency = res["transparency"]

        self.assertIn("confidence_score", transparency)
        self.assertIn("confidence_label", transparency)
        self.assertIn("sources", transparency)

        if transparency["sources"]:
            src = transparency["sources"][0]
            self.assertIn("document_name", src)
            self.assertIn("chunk_id", src)
            self.assertIn("relevance_score", src)
            self.assertIn("content", src)

    def test_low_confidence_transparency(self):
        """Test transparency output for low-confidence or out-of-domain query."""
        res = self.orchestrator.process_query(
            query="What is today's weather in Coimbatore?",
            session_id="transparency_test_02"
        )
        transparency = res["transparency"]
        self.assertTrue(transparency["insufficient_evidence"])
        self.assertEqual(transparency["confidence_label"], "Low")


if __name__ == "__main__":
    unittest.main()
