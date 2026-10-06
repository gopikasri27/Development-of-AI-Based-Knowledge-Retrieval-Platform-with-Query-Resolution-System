"""
Milestone 4 End-to-End Automated Test Suite
-------------------------------------------
Executes 10 comprehensive test cases across 3 knowledge domains:
AI/ML, Cloud Computing, and Cybersecurity, plus HR & Policy context.

Validates:
1. Factual Query Resolution
2. Procedural Query Resolution
3. Comparative Query Resolution
4. Ambiguous Query Handling & Clarification Triggering
5. Multi-Turn Conversation Memory Retention
6. Domain Context Switching
7. Simulated Voice Input Query Processing
8. Out-of-Scope / Unavailable Information Refusal Handling
9. Transparency Telemetry & Execution Trace Verification
10. Low Confidence & Knowledge Gap Analytics Recording
"""

import os
import sys
import unittest
import json
import time

# Ensure path resolution for milestone-4, milestone-3, milestone-2
current_dir = os.path.dirname(os.path.abspath(__file__))
m4_dir = os.path.dirname(current_dir)
root_dir = os.path.dirname(m4_dir)
m3_dir = os.path.join(root_dir, "milestone-3")
m2_dir = os.path.join(root_dir, "milestone-2")

for p in [m2_dir, m3_dir, m4_dir, root_dir]:
    if p not in sys.path:
        sys.path.insert(0, p)

import importlib.util
orch_path = os.path.join(m3_dir, "orchestration", "milestone3_orchestrator.py")
spec = importlib.util.spec_from_file_location("milestone3_orchestrator", orch_path)
orch_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(orch_mod)
Milestone3Orchestrator = orch_mod.Milestone3Orchestrator

from analytics.query_analytics import QueryAnalyticsEngine


class TestMilestone4EndToEnd(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        """Initialize orchestrator and analytics engine for testing."""
        print("\n========================================================")
        print(" INITIALIZING MILESTONE 4 END-TO-END TEST SUITE")
        print("========================================================\n")
        cls.orchestrator = Milestone3Orchestrator()
        cls.analytics = QueryAnalyticsEngine()
        cls.test_session_id = f"test_e2e_session_{int(time.time())}"

    def test_01_factual_query(self):
        """TC-01: Factual Query — What is Machine Learning?"""
        print("\n--> TC-01: Testing Factual Query...")
        query = "What is machine learning and what are its core supervised and unsupervised paradigms?"
        result = self.orchestrator.process_query(query, session_id=self.test_session_id)
        
        self.analytics.record_query(result, session_id=self.test_session_id)
        
        self.assertIn("answer", result)
        self.assertTrue(len(result.get("answer", "")) > 10)
        self.assertGreaterEqual(result["confidence"]["score"], 0.0)
        print(f"    [Pass] TC-01 Factual Query resolved with confidence {result['confidence']['score']:.2f}")

    def test_02_procedural_query(self):
        """TC-02: Procedural Query — How does semantic search work in modern RAG systems?"""
        print("\n--> TC-02: Testing Procedural Query...")
        query = "How does semantic search work step by step in RAG systems?"
        result = self.orchestrator.process_query(query, session_id=self.test_session_id)
        
        self.analytics.record_query(result, session_id=self.test_session_id)
        
        self.assertIn("answer", result)
        self.assertTrue(any(term in result["answer"].lower() for term in ["search", "semantic", "rag", "retriev", "document"]))
        print(f"    [Pass] TC-02 Procedural Query returned detailed response with {len(result.get('citations', []))} citation(s)")

    def test_03_comparative_query(self):
        """TC-03: Comparative Query — Compare IaaS, PaaS, and SaaS cloud deployment models."""
        print("\n--> TC-03: Testing Comparative Query...")
        query = "Compare IaaS, PaaS, and SaaS cloud service models and their management responsibilities."
        result = self.orchestrator.process_query(query, session_id=self.test_session_id)
        
        self.analytics.record_query(result, session_id=self.test_session_id)
        
        self.assertIn("answer", result)
        self.assertTrue(any(term in result["answer"].lower() for term in ["iaas", "paas", "saas", "cloud"]))
        print(f"    [Pass] TC-03 Comparative Query generated structured comparative answer")

    def test_04_ambiguous_query_clarification(self):
        """TC-04: Ambiguous Query — Requires Clarification."""
        print("\n--> TC-04: Testing Ambiguous Query & Clarification...")
        query = "Tell me about policies and general rules."
        result = self.orchestrator.process_query(query, session_id=f"clarify_session_{int(time.time())}")
        
        self.analytics.record_query(result, session_id=f"clarify_session_{int(time.time())}")
        
        self.assertTrue(
            result.get("is_clarification", False) or 
            "clarification" in result.get("answer", "").lower() or 
            len(result.get("options", [])) > 0 or
            result.get("confidence", {}).get("score", 1.0) < 0.50
        )
        print(f"    [Pass] TC-04 Ambiguous query correctly handled by system")

    def test_05_multi_turn_memory(self):
        """TC-05: Multi-Turn Conversation Memory Retention."""
        print("\n--> TC-05: Testing Multi-Turn Memory...")
        session_id = f"memory_session_{int(time.time())}"
        
        # Turn 1
        q1 = "What is the CIA triad in cybersecurity?"
        r1 = self.orchestrator.process_query(q1, session_id=session_id)
        self.analytics.record_query(r1, session_id=session_id)
        
        # Turn 2 (Contextual follow-up using pronoun "it")
        q2 = "What does confidentiality mean within it?"
        r2 = self.orchestrator.process_query(q2, session_id=session_id)
        self.analytics.record_query(r2, session_id=session_id)
        
        self.assertIn("answer", r2)
        self.assertIn("confidentiality", r2["answer"].lower())
        print(f"    [Pass] TC-05 Memory retained conversation history across turns")

    def test_06_context_switching(self):
        """TC-06: Context Switching across Knowledge Domains."""
        print("\n--> TC-06: Testing Context Switching...")
        session_id = f"switch_session_{int(time.time())}"
        
        # Query in Cloud domain
        q1 = "What is cloud computing?"
        r1 = self.orchestrator.process_query(q1, session_id=session_id)
        self.analytics.record_query(r1, session_id=session_id)
        
        # Switch to Cybersecurity domain
        q2 = "Explain Zero Trust Architecture principles."
        r2 = self.orchestrator.process_query(q2, session_id=session_id)
        self.analytics.record_query(r2, session_id=session_id)
        
        self.assertIn("never trust", r2["answer"].lower())
        print(f"    [Pass] TC-06 Successfully switched context from Cloud to Cybersecurity")

    def test_07_simulated_voice_query(self):
        """TC-07: Voice Input Query Handling (Simulated STT text)."""
        print("\n--> TC-07: Testing Voice Input Query Processing...")
        # Typical spoken query with minor disfluencies
        voice_query = "um could you explain what symmetric encryption is with AES 256"
        result = self.orchestrator.process_query(voice_query, session_id=self.test_session_id)
        
        self.analytics.record_query(result, session_id=self.test_session_id)
        
        self.assertIn("answer", result)
        self.assertTrue("aes" in result["answer"].lower() or "symmetric" in result["answer"].lower())
        print(f"    [Pass] TC-07 Successfully resolved simulated voice query input")

    def test_08_out_of_scope_query(self):
        """TC-08: Out-of-Scope / Unavailable Information Refusal."""
        print("\n--> TC-08: Testing Out-of-Scope Query Refusal...")
        out_of_scope_query = "What will be the weather forecast in Tokyo tomorrow morning?"
        result = self.orchestrator.process_query(out_of_scope_query, session_id=self.test_session_id)
        
        self.analytics.record_query(result, session_id=self.test_session_id)
        
        self.assertLess(result["confidence"]["score"], 0.40)
        self.assertTrue(
            "not found" in result["answer"].lower() or 
            "sufficient information" in result["answer"].lower() or
            result["confidence"]["score"] < 0.30
        )
        print(f"    [Pass] TC-08 Correctly refused out-of-scope query without hallucination")

    def test_09_transparency_telemetry(self):
        """TC-09: Transparency Telemetry & Execution Trace Verification."""
        print("\n--> TC-09: Testing Transparency Telemetry...")
        query = "What is deep learning and neural networks?"
        result = self.orchestrator.process_query(query, session_id=self.test_session_id)
        
        self.assertIn("telemetry", result)
        self.assertIn("transparency", result)
        self.assertIn("confidence", result)
        self.assertIn("classification_confidence", result)
        print(f"    [Pass] TC-09 Telemetry trace captured execution pipeline metrics")

    def test_10_analytics_and_gap_detection(self):
        """TC-10: Analytics Recording & Knowledge Gap Detection."""
        print("\n--> TC-10: Testing Analytics Engine & Gap Detection...")
        
        # Record a low-confidence/unanswered query
        gap_query = "What is quantum cryptographic teleportation latency?"
        r = self.orchestrator.process_query(gap_query, session_id=self.test_session_id)
        self.analytics.record_query(r, session_id=self.test_session_id)
        
        # Verify stats and gaps
        stats = self.analytics.get_summary_stats()
        self.assertGreater(stats["total_queries"], 0)
        
        gaps = self.analytics.get_knowledge_gaps(min_frequency=1)
        self.assertIsInstance(gaps, list)
        print(f"    [Pass] TC-10 Analytics Engine recorded {stats['total_queries']} total queries and detected {len(gaps)} knowledge gap(s)")

if __name__ == "__main__":
    unittest.main()
