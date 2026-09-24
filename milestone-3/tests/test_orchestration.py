"""
End-to-End Integration Tests for Milestone 3 Agent Orchestrator
-----------------------------------------------------------------
Validates all 5 mandatory end-to-end scenarios:
- Scenario 1: Normal Factual Query
- Scenario 2: Ambiguous Query & Clarification Refinement
- Scenario 3: Follow-Up Query with Conversation Memory ("its" pronoun resolution)
- Scenario 4: Voice / Direct Query
- Scenario 5: No Result / Low Evidence Query
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


class TestMilestone3Orchestration(unittest.TestCase):

    def setUp(self):
        self.orchestrator = Milestone3Orchestrator()
        self.session_id = "e2e_test_session_100"

    def test_scenario_1_normal_query(self):
        """Scenario 1: Factual lookup query."""
        res = self.orchestrator.process_query(
            query="How many days of paid annual leave do employees receive per year?",
            session_id=self.session_id
        )
        self.assertFalse(res["is_clarification"])
        self.assertEqual(res["query_type"], "factual")
        self.assertIn("answer", res)
        self.assertIn("transparency", res)

    def test_scenario_2_ambiguous_query_and_clarification(self):
        """Scenario 2: Ambiguous query triggers clarification, then refines query with response."""
        session = "scenario_2_session"
        # Turn 1: Ambiguous query
        res1 = self.orchestrator.process_query(
            query="Tell me about cloud.",
            session_id=session
        )
        self.assertTrue(res1["is_clarification"])
        self.assertIsNotNone(res1["clarification_question"])
        self.assertIn("cloud computing", res1["clarification_question"].lower())

        # Turn 2: User provides clarification response
        res2 = self.orchestrator.process_query(
            query="Cloud computing.",
            session_id=session
        )
        self.assertFalse(res2["is_clarification"])
        self.assertIn("Tell me about cloud computing", res2.get("refined_query", ""))

    def test_scenario_3_follow_up_query_with_memory(self):
        """Scenario 3: Multi-turn pronoun resolution ('What is IaaS?' -> 'What are its benefits?')."""
        session = "scenario_3_session"
        # Turn 1
        res1 = self.orchestrator.process_query(
            query="What is IaaS?",
            session_id=session
        )

        # Turn 2: Follow-up question using pronoun "its"
        res2 = self.orchestrator.process_query(
            query="What are its benefits?",
            session_id=session
        )
        self.assertFalse(res2["is_clarification"])
        self.assertIn("IaaS", res2.get("refined_query", ""))

    def test_scenario_4_voice_query(self):
        """Scenario 4: Voice query processing."""
        res = self.orchestrator.process_query(
            query="What are the step-by-step instructions to install CloudSync Pro?",
            session_id="scenario_4_session"
        )
        self.assertFalse(res["is_clarification"])
        self.assertEqual(res["query_type"], "procedural")

    def test_scenario_5_no_result_query(self):
        """Scenario 5: No result query returns clear no-information response with low evidence transparency."""
        res = self.orchestrator.process_query(
            query="What is today's weather in Coimbatore?",
            session_id="scenario_5_session"
        )
        self.assertFalse(res["is_clarification"])
        self.assertTrue(res["transparency"]["insufficient_evidence"])


if __name__ == "__main__":
    unittest.main()
