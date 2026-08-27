"""
Query Understanding Agent
------------------------
Role: Parses, cleans, and classifies the incoming user query.
Identifies:
1. Query Type: 'factual', 'procedural', 'comparative', or 'unavailable-info'
2. Core Intent & Normalized Search Query
3. Extracted Keywords/Entities
"""

import re
from typing import Dict, Any, List


class QueryAgent:
    def __init__(self):
        # Patterns for classification
        self.procedural_patterns = [
            r"\bhow (to|do|can|should|would|must)\b",
            r"\bsteps (to|for)\b",
            r"\bprocess of\b",
            r"\bguide (to|for)\b",
            r"\binstructions for\b",
            r"\bprocedure for\b",
            r"\bway to\b",
            r"\bsetup\b",
            r"\bconfigure\b",
            r"\bhow do i\b",
            r"\bwalk me through\b"
        ]
        
        self.comparative_patterns = [
            r"\bcompare\b",
            r"\bcomparison\b",
            r"\bdifference between\b",
            r"\bdifferences between\b",
            r"\bversus\b",
            r"\bvs\.?\b",
            r"\bbetter than\b",
            r"\bsimilar to\b",
            r"\bpros and cons\b",
            r"\bhow does .* differ from\b"
        ]
        
        self.factual_patterns = [
            r"\bwhat is\b",
            r"\bwhat are\b",
            r"\bwho is\b",
            r"\bwho are\b",
            r"\bwhen is\b",
            r"\bwhen was\b",
            r"\bwhere is\b",
            r"\bwhich\b",
            r"\bhow much\b",
            r"\bhow many\b",
            r"\bis there\b",
            r"\bdefine\b",
            r"\blist of\b",
            r"\btell me about\b"
        ]

    def classify_query_type(self, query: str) -> str:
        """
        Classifies query into 'procedural', 'comparative', or 'factual'.
        """
        q_lower = query.lower().strip()
        
        # Check comparative first
        for pattern in self.comparative_patterns:
            if re.search(pattern, q_lower):
                return "comparative"
                
        # Check procedural
        for pattern in self.procedural_patterns:
            if re.search(pattern, q_lower):
                return "procedural"
                
        # Check factual
        for pattern in self.factual_patterns:
            if re.search(pattern, q_lower):
                return "factual"
                
        # Default to factual for direct phrases / terminology lookups
        return "factual"

    def extract_keywords(self, query: str) -> List[str]:
        """Extracts meaningful terms and entities by removing stopwords."""
        stopwords = {
            "a", "an", "the", "in", "on", "at", "to", "for", "of", "with", "by",
            "is", "are", "was", "were", "be", "been", "being", "have", "has", "had",
            "do", "does", "did", "can", "could", "should", "would", "will", "shall",
            "and", "or", "but", "if", "then", "else", "what", "which", "who", "whom",
            "this", "that", "these", "those", "am", "i", "you", "he", "she", "it",
            "we", "they", "me", "him", "her", "us", "them", "my", "your", "his",
            "their", "our", "tell", "explain", "describe", "give", "please"
        }
        words = re.findall(r"\b[a-zA-Z0-9_-]+\b", query.lower())
        keywords = [w for w in words if w not in stopwords and len(w) > 2]
        return keywords

    def reformulate_with_history(self, current_query: str, history: List[Dict[str, Any]]) -> str:
        """
        If the current query uses pronouns like 'it', 'they', 'this',
        supplements the query with entities from the latest conversational turn.
        """
        q_lower = current_query.lower()
        pronoun_triggers = [" it", " this", " that", " these", " those", " they", " their", " its"]
        needs_context = any(t in q_lower for t in pronoun_triggers) or len(current_query.split()) <= 3
        
        if needs_context and history:
            last_turn = history[-1]
            last_user_msg = last_turn.get("message", "")
            last_keywords = self.extract_keywords(last_user_msg)
            if last_keywords:
                augmented = f"{current_query} (context: {' '.join(last_keywords[:4])})"
                return augmented
                
        return current_query

    def process(self, query: str, history: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Executes the Query Understanding Agent workflow.
        Returns parsed intent, classification, and enriched search query.
        """
        history = history or []
        query_cleaned = query.strip()
        query_type = self.classify_query_type(query_cleaned)
        keywords = self.extract_keywords(query_cleaned)
        reformulated_query = self.reformulate_with_history(query_cleaned, history)
        
        return {
            "agent": "Query Understanding Agent",
            "original_query": query,
            "cleaned_query": query_cleaned,
            "reformulated_query": reformulated_query,
            "query_type": query_type,
            "keywords": keywords,
            "is_ambiguous": len(keywords) == 0 or len(query_cleaned) < 4
        }
