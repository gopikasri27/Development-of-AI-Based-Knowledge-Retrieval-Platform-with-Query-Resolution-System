"""
Unit Tests for Conversation Memory & Memory Agent (M3.2)
--------------------------------------------------------
Tests pronoun resolution, follow-up questions, topic tracking, context switching,
missing memory handling, and relevant memory selection.
"""

import sys
import os
import unittest

current_dir = os.path.dirname(os.path.abspath(__file__))
m3_dir = os.path.dirname(current_dir)
root_dir = os.path.dirname(m3_dir)
for p in [m3_dir, root_dir]:
    if p not in sys.path:
        sys.path.insert(0, p)

from memory.conversation_memory import ConversationMemory
from agents.conversation_memory_agent import ConversationMemoryAgent


class TestConversationMemory(unittest.TestCase):

    def setUp(self):
        self.memory = ConversationMemory()
        self.agent = ConversationMemoryAgent(memory_store=self.memory)
        self.session_id = "test_sess_001"

    def test_add_and_retrieve_turn(self):
        """Test adding turns to conversation memory."""
        self.memory.add_turn(
            session_id=self.session_id,
            query="What is IaaS?",
            answer="IaaS stands for Infrastructure as a Service.",
            query_type="factual",
            topic="IaaS"
        )
        history = self.memory.get_session_history(self.session_id)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["query"], "What is IaaS?")

    def test_pronoun_resolution_with_history(self):
        """Test resolving 'its' -> 'IaaS' when prior history exists."""
        self.memory.add_turn(
            session_id=self.session_id,
            query="What is IaaS?",
            answer="IaaS stands for Infrastructure as a Service.",
            topic="IaaS"
        )
        res = self.agent.process_query_context(self.session_id, "What are its benefits?")
        self.assertTrue(res["is_context_dependent"])
        self.assertTrue(res["context_found"])
        self.assertIn("IaaS", res["resolved_query"])

    def test_missing_memory_handling(self):
        """Test handling when context is missing."""
        res = self.agent.process_query_context("non_existent_session", "What are its benefits?")
        self.assertTrue(res["is_context_dependent"])
        self.assertFalse(res["context_found"])
        self.assertEqual(res["resolved_query"], "What are its benefits?")

    def test_relevant_memory_selection(self):
        """Test that relevant memory summary is extracted without dumping full raw history."""
        self.memory.add_turn(
            session_id=self.session_id,
            query="Tell me about CloudSync Pro",
            answer="CloudSync Pro is a desktop syncing tool.",
            sources=[{"document_name": "product_manual.txt"}]
        )
        summary = self.memory.get_recent_entities_and_topics(self.session_id)
        self.assertIn("product_manual.txt", summary["referenced_documents"])

    def test_context_switching_and_clear(self):
        """Test clearing memory on session reset."""
        self.memory.add_turn(self.session_id, "Q1", "A1")
        self.memory.clear_session(self.session_id)
        self.assertEqual(len(self.memory.get_session_history(self.session_id)), 0)


if __name__ == "__main__":
    unittest.main()
