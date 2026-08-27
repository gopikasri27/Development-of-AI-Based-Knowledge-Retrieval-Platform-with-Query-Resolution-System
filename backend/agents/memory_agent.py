"""
Conversation Memory Agent
------------------------
Role: Maintains multi-turn conversation memory per session (last 5 turns).
Persists history via the metadata SQLite database for cross-request continuity.
"""

from typing import Dict, Any, List
from utils.db import save_chat_message, get_recent_history


class MemoryAgent:
    def __init__(self, max_history_turns: int = 5):
        self.max_history_turns = max_history_turns

    def get_history(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Retrieves the last N conversational turns for the active session.
        """
        if not session_id:
            return []
        return get_recent_history(session_id, limit=self.max_history_turns)

    def record_user_turn(self, session_id: str, message: str, query_type: str = None):
        """
        Records the user's incoming turn into session memory.
        """
        if not session_id:
            return
        save_chat_message(
            session_id=session_id,
            role="user",
            message=message,
            query_type=query_type
        )

    def record_assistant_turn(
        self,
        session_id: str,
        message: str,
        sources: List[Dict[str, Any]] = None,
        query_type: str = None
    ):
        """
        Records the assistant's response turn into session memory.
        """
        if not session_id:
            return
        save_chat_message(
            session_id=session_id,
            role="assistant",
            message=message,
            query_type=query_type,
            sources=sources
        )

    def process(
        self,
        session_id: str,
        user_query: str,
        agent_response: str,
        sources: List[Dict[str, Any]] = None,
        query_type: str = None
    ) -> Dict[str, Any]:
        """
        Updates session memory with both user and assistant interactions.
        """
        self.record_user_turn(session_id, user_query, query_type)
        self.record_assistant_turn(session_id, agent_response, sources, query_type)
        
        updated_history = self.get_history(session_id)
        
        return {
            "agent": "Conversation Memory Agent",
            "session_id": session_id,
            "turns_stored": len(updated_history),
            "recent_turns": updated_history
        }
