"""
Conversation Memory Agent (M3.2)
--------------------------------
Analyzes user queries in the context of recent session interaction memory.
Resolves context-dependent queries (e.g. "What are its benefits?", "Compare them",
"Explain it"), extracts relevant entity/topic references, and selectively builds
query context for downstream agents without overloading LLM prompts.
"""

import re
from typing import Dict, Any, List, Optional
import os
import sys

# Ensure local imports resolve
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from memory.conversation_memory import ConversationMemory


class ConversationMemoryAgent:
    """
    M3.2 Conversation Memory Agent for multi-turn context resolution and pronoun disambiguation.
    """

    def __init__(self, memory_store: Optional[ConversationMemory] = None):
        self.memory_store = memory_store or ConversationMemory()

    def process_query_context(
        self,
        session_id: str,
        query: str
    ) -> Dict[str, Any]:
        """
        Analyzes the query against existing session memory.
        
        Returns:
            {
                "original_query": str,
                "resolved_query": str,
                "is_context_dependent": bool,
                "context_found": bool,
                "relevant_memory": Dict[str, Any],
                "pronoun_resolved": Optional[str],
                "topic": str
            }
        """
        clean_q = query.strip()
        history = self.memory_store.get_session_history(session_id)

        if not history:
            # Check if query uses pronouns when no memory is available
            is_context_dependent, pronoun = self._detect_context_dependency(clean_q)
            return {
                "original_query": query,
                "resolved_query": query,
                "is_context_dependent": is_context_dependent,
                "context_found": False,
                "relevant_memory": {},
                "pronoun_resolved": None,
                "topic": self.memory_store._extract_basic_topic(query)
            }

        last_turn = history[-1]
        is_context_dependent, pronoun = self._detect_context_dependency(clean_q)

        # Attempt to extract subject/entity from last turn
        last_subject = self._extract_subject_from_turn(last_turn)

        resolved_query = query
        pronoun_resolved = None

        if is_context_dependent and last_subject:
            resolved_query = self._substitute_pronoun(query, pronoun, last_subject)
            pronoun_resolved = f"Replaced '{pronoun}' with '{last_subject}'"
        elif is_context_dependent and not last_subject:
            # Context-dependent query but last subject unknown
            pass

        # Selectively extract relevant memory context (not entire history)
        relevant_memory = {
            "last_query": last_turn.get("query"),
            "last_answer_snippet": last_turn.get("answer", "")[:200],
            "last_subject": last_subject,
            "last_sources": [s.get("document_name") for s in last_turn.get("sources", []) if s.get("document_name")],
            "turns_count": len(history)
        }

        return {
            "original_query": query,
            "resolved_query": resolved_query,
            "is_context_dependent": is_context_dependent,
            "context_found": True,
            "relevant_memory": relevant_memory,
            "pronoun_resolved": pronoun_resolved,
            "topic": last_subject or self.memory_store._extract_basic_topic(query)
        }

    def _detect_context_dependency(self, query: str) -> tuple[bool, Optional[str]]:
        """
        Detects if query contains ambiguous pronouns or context-dependent references.
        """
        lower = query.lower()
        pronoun_patterns = [
            (r"\bits\b", "its"),
            (r"\bit\b", "it"),
            (r"\bthem\b", "them"),
            (r"\bthey\b", "they"),
            (r"\btheir\b", "their"),
            (r"\bthis\b", "this"),
            (r"\bthat\b", "that"),
            (r"\bthese\b", "these"),
            (r"\bthose\b", "those"),
            (r"\bthe former\b", "the former"),
            (r"\bthe latter\b", "the latter")
        ]

        for pattern, token in pronoun_patterns:
            if re.search(pattern, lower):
                return True, token

        # Check for vague short follow-ups
        short_followups = [
            r"^what are the benefits\??$",
            r"^tell me more\??$",
            r"^how do i install it\??$",
            r"^explain more\??$",
            r"^why\??$"
        ]
        for pat in short_followups:
            if re.match(pat, lower):
                return True, "it"

        return False, None

    def _extract_subject_from_turn(self, turn: Dict[str, Any]) -> Optional[str]:
        """
        Extracts key subject entity from a previous turn.
        """
        query = turn.get("query", "")
        # Common acronyms & technical terms (excluding question stop-words)
        stop_words = {"What", "How", "Why", "When", "Where", "Which", "Who", "Tell", "Explain", "Compare", "Does", "Have", "Show"}
        tech_terms = [t for t in re.findall(r"\b[A-Z][A-Za-z0-9_]{1,}\b|\b[A-Z]{2,}\b", query) if t not in stop_words]
        if tech_terms:
            return tech_terms[0]

        # Check for "what is X", "tell me about X", "compare X"
        match = re.search(r"(?:what is|what are|explain|tell me about|compare|about)\s+([A-Za-z0-9_\s\-]+)", query, re.IGNORECASE)
        if match:
            extracted = match.group(1).strip().rstrip("?.!")
            # Clean stop words
            extracted = re.sub(r"^(?:a|an|the)\s+", "", extracted, flags=re.IGNORECASE)
            if len(extracted) > 1 and len(extracted.split()) <= 4:
                return extracted

        # Fallback to turn topic
        topic = turn.get("topic")
        if topic and topic != query:
            return topic

        return None

    def _substitute_pronoun(self, query: str, pronoun: Optional[str], subject: str) -> str:
        """
        Replaces pronoun with the explicit subject in the query string.
        """
        if not pronoun:
            return f"{query} (regarding {subject})"

        lower_q = query.lower()

        if pronoun == "its":
            # "What are its benefits?" -> "What are the benefits of IaaS?"
            if re.search(r"\bwhat are its benefits\b", lower_q):
                return f"What are the benefits of {subject}?"
            return re.sub(r"\bits\b", f"{subject}'s", query, flags=re.IGNORECASE)

        elif pronoun == "it":
            # "Explain it." -> "Explain IaaS."
            if re.search(r"\bexplain it\b", lower_q):
                return f"Explain {subject}."
            if re.search(r"\bwhat is it\b", lower_q):
                return f"What is {subject}?"
            return re.sub(r"\bit\b", subject, query, flags=re.IGNORECASE)

        elif pronoun in ("them", "they", "their", "these", "those"):
            return re.sub(rf"\b{pronoun}\b", subject, query, flags=re.IGNORECASE)

        return f"{query} ({subject})"
