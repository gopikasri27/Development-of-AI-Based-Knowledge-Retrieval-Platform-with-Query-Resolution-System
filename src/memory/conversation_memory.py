"""
Conversation Memory Store (M3.2)
---------------------------------
Maintains per-session interaction history including queries, refined queries,
generated responses, clarification questions/responses, referenced documents,
topics, and key entities.

Ensures conversation memory is distinct from the permanent domain Knowledge Base.
"""

import time
from typing import Dict, Any, List, Optional


class ConversationMemory:
    """
    In-memory session storage manager for tracking multi-turn conversation context.
    """

    def __init__(self, max_turns_per_session: int = 20):
        self.max_turns_per_session = max_turns_per_session
        # Map session_id -> list of turn dicts
        self.sessions: Dict[str, List[Dict[str, Any]]] = {}
        # Map session_id -> pending clarification dict or None
        self.pending_clarifications: Dict[str, Optional[Dict[str, Any]]] = {}

    def get_session_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Returns turn history for a given session."""
        return self.sessions.get(session_id, [])

    def add_turn(
        self,
        session_id: str,
        query: str,
        answer: str,
        refined_query: Optional[str] = None,
        query_type: Optional[str] = None,
        sources: Optional[List[Dict[str, Any]]] = None,
        clarification_question: Optional[str] = None,
        clarification_response: Optional[str] = None,
        entities: Optional[List[str]] = None,
        topic: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Records a single interaction turn into the session memory.
        """
        if session_id not in self.sessions:
            self.sessions[session_id] = []

        turn_index = len(self.sessions[session_id]) + 1
        turn_data = {
            "turn_index": turn_index,
            "timestamp": time.time(),
            "query": query,
            "refined_query": refined_query or query,
            "answer": answer,
            "query_type": query_type or "factual",
            "sources": sources or [],
            "clarification_question": clarification_question,
            "clarification_response": clarification_response,
            "entities": entities or [],
            "topic": topic or self._extract_basic_topic(query)
        }

        self.sessions[session_id].append(turn_data)

        # Enforce max history limit
        if len(self.sessions[session_id]) > self.max_turns_per_session:
            self.sessions[session_id] = self.sessions[session_id][-self.max_turns_per_session:]

        return turn_data

    def set_pending_clarification(
        self,
        session_id: str,
        original_query: str,
        clarification_question: str,
        ambiguity_type: str = "ambiguous"
    ):
        """Stores a pending clarification state for a session."""
        self.pending_clarifications[session_id] = {
            "original_query": original_query,
            "clarification_question": clarification_question,
            "ambiguity_type": ambiguity_type,
            "timestamp": time.time()
        }

    def get_pending_clarification(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Gets active pending clarification for a session, if any."""
        return self.pending_clarifications.get(session_id)

    def clear_pending_clarification(self, session_id: str):
        """Clears pending clarification state for a session."""
        self.pending_clarifications[session_id] = None

    def get_last_turn(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Returns the most recent completed turn in session."""
        history = self.get_session_history(session_id)
        return history[-1] if history else None

    def get_recent_entities_and_topics(self, session_id: str, limit: int = 3) -> Dict[str, Any]:
        """
        Extracts recent entities, document references, and topics from memory.
        """
        history = self.get_session_history(session_id)[-limit:]
        entities = []
        topics = []
        referenced_docs = []

        for turn in reversed(history):
            if turn.get("topic") and turn["topic"] not in topics:
                topics.append(turn["topic"])
            for ent in turn.get("entities", []):
                if ent not in entities:
                    entities.append(ent)
            for src in turn.get("sources", []):
                doc_name = src.get("document_name")
                if doc_name and doc_name not in referenced_docs:
                    referenced_docs.append(doc_name)

        return {
            "topics": topics,
            "entities": entities,
            "referenced_documents": referenced_docs,
            "last_query": history[-1]["query"] if history else None,
            "last_answer": history[-1]["answer"] if history else None
        }

    def clear_session(self, session_id: str):
        """Clears all session memory for a given session ID."""
        if session_id in self.sessions:
            del self.sessions[session_id]
        if session_id in self.pending_clarifications:
            del self.pending_clarifications[session_id]

    def _extract_basic_topic(self, text: str) -> str:
        """Helper to derive a brief topic summary from query string."""
        clean = text.strip()
        words = clean.split()
        if len(words) <= 5:
            return clean
        return " ".join(words[:5]) + "..."
