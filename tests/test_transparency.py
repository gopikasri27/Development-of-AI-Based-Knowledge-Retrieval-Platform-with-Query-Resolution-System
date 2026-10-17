"""
Unit Tests for Response Transparency Panel & Metadata Structure (M3.4)
----------------------------------------------------------------------
Tests actual source document mapping, chunk IDs, similarity scores,
confidence indicators, and no-result / low-confidence transparency info.
"""

import os
import sys
_current_dir = os.path.dirname(os.path.abspath(__file__))
_root_dir = os.path.dirname(_current_dir)
_src_dir = os.path.join(_root_dir, "src")
for _p in [_src_dir, _root_dir]:
    if _p not in sys.path:
        sys.path.insert(0, _p)



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

from orchestration.orchestrator import MultiAgentOrchestrator as Milestone3Orchestrator


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
