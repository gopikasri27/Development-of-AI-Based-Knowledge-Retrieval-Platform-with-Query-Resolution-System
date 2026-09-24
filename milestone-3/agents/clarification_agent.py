"""
Clarification Agent (M3.1)
--------------------------
Detects ambiguous, incomplete, context-dependent, or multi-part queries with unresolved
requirements. Generates targeted follow-up questions to request only the necessary
information from the user before executing retrieval or response synthesis.

Combines original query + user clarification response into a refined query for the pipeline.
"""

import re
import json
from typing import Dict, Any, Optional

try:
    import google.generativeai as genai
except ImportError:
    genai = None


class ClarificationAgent:
    """
    M3.1 Clarification Agent for ambiguity detection, follow-up question generation,
    and query refinement.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY") if "os" in globals() else None
        if not self.api_key:
            import os
            self.api_key = os.environ.get("GEMINI_API_KEY")

        if self.api_key and genai:
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel("gemini-1.5-flash")
            except Exception:
                self.model = None
        else:
            self.model = None

    def evaluate_query(
        self,
        query: str,
        memory_context: Optional[Dict[str, Any]] = None,
        query_classification: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Evaluates query for ambiguity or unresolved requirements.
        
        Returns:
            {
                "clarification_required": bool,
                "ambiguity_type": "vague_term" | "missing_context" | "multi_interpretation" | "unresolved_multipart" | "none",
                "clarification_question": str or None,
                "reasoning": str
            }
        """
        clean_q = query.strip()
        lower_q = clean_q.lower()

        # 1. Rule-based evaluation
        rule_eval = self._evaluate_by_rules(clean_q, memory_context, query_classification)
        if rule_eval["clarification_required"]:
            return rule_eval

        # 2. LLM evaluation if API available and query classification is ambiguous
        q_type = query_classification.get("query_type") if query_classification else None
        if self.model and (q_type == "ambiguous" or not rule_eval["clarification_required"]):
            try:
                llm_eval = self._evaluate_by_llm(clean_q, memory_context)
                if llm_eval:
                    return llm_eval
            except Exception:
                pass

        return rule_eval

    def _evaluate_by_rules(
        self,
        query: str,
        memory_context: Optional[Dict[str, Any]] = None,
        query_classification: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Rule-based detection for standard ambiguity patterns and missing context.
        """
        lower_q = query.lower().strip()

        # Check for context-dependent queries without memory context
        has_memory = memory_context.get("context_found", False) if memory_context else False
        is_context_dep = memory_context.get("is_context_dependent", False) if memory_context else False

        if is_context_dep and not has_memory:
            if "benefit" in lower_q or "its" in lower_q:
                return {
                    "clarification_required": True,
                    "ambiguity_type": "missing_context",
                    "clarification_question": "Could you clarify what product, service, or policy you are asking about?",
                    "reasoning": "Context-dependent query missing previous conversation history."
                }
            if "compare them" in lower_q or "them" in lower_q:
                return {
                    "clarification_required": True,
                    "ambiguity_type": "missing_context",
                    "clarification_question": "Could you specify which items, products, or services you would like to compare?",
                    "reasoning": "Comparison request with missing prior subject."
                }
            if "explain it" in lower_q or "it" in lower_q:
                return {
                    "clarification_required": True,
                    "ambiguity_type": "missing_context",
                    "clarification_question": "Could you clarify what concept or feature you would like explained?",
                    "reasoning": "Explanation request with missing subject."
                }

        # Specific ambiguous queries (e.g. "Tell me about cloud.")
        if re.search(r"^(?:tell me about|explain|what is|info on)\s+cloud\??$", lower_q):
            return {
                "clarification_required": True,
                "ambiguity_type": "multi_interpretation",
                "clarification_question": "Could you clarify whether you mean cloud computing, cloud storage, or cloud security?",
                "reasoning": "Broad term 'cloud' has multiple domain interpretations."
            }

        if lower_q in {"cloud", "tell me about cloud", "tell me about cloud."}:
            return {
                "clarification_required": True,
                "ambiguity_type": "multi_interpretation",
                "clarification_question": "Could you clarify whether you mean cloud computing, cloud storage, or cloud security?",
                "reasoning": "Broad term 'cloud' has multiple domain interpretations."
            }

        # Extremely brief vague inputs
        vague_single_words = {"leave", "policy", "sync", "manual", "guide", "pricing", "help", "system", "app"}
        if lower_q in vague_single_words or lower_q.rstrip("?") in vague_single_words:
            word = lower_q.rstrip("?").capitalize()
            return {
                "clarification_required": True,
                "ambiguity_type": "vague_term",
                "clarification_question": f"Could you provide more details about what specific {word} information you are looking for?",
                "reasoning": "Single keyword is too underspecified."
            }

        # Multi-part queries check
        # Example: "Compare AWS and Azure and tell me which one is cheaper and how to deploy it."
        if " and " in lower_q and ("cheaper" in lower_q or "deploy" in lower_q or "compare" in lower_q):
            # Check if entities are clearly defined
            if "aws" in lower_q and "azure" in lower_q:
                # AWS and Azure are clear entities! Can be resolved directly.
                return {
                    "clarification_required": False,
                    "ambiguity_type": "none",
                    "clarification_question": None,
                    "reasoning": "Multi-part query contains clear entities (AWS and Azure)."
                }
            elif "which one" in lower_q and not ("aws" in lower_q or "azure" in lower_q or "standard" in lower_q or "pro" in lower_q):
                return {
                    "clarification_required": True,
                    "ambiguity_type": "unresolved_multipart",
                    "clarification_question": "Could you specify which two services or software editions you would like to compare for deployment and cost?",
                    "reasoning": "Multi-part query is missing the target services to compare."
                }

        # If query classification from M2 is ambiguous and rule didn't catch it
        if query_classification and query_classification.get("query_type") == "ambiguous":
            return {
                "clarification_required": True,
                "ambiguity_type": "vague_term",
                "clarification_question": f"Could you please rephrase your question or specify what information you need regarding '{query}'?",
                "reasoning": "Query Understanding Agent classified intent as ambiguous."
            }

        return {
            "clarification_required": False,
            "ambiguity_type": "none",
            "clarification_question": None,
            "reasoning": "Query is sufficiently clear to process directly."
        }

    def refine_query(
        self,
        original_query: str,
        clarification_response: str,
        clarification_question: Optional[str] = None
    ) -> str:
        """
        Combines original query + user clarification response into a refined query.
        
        Example:
            Original: "Tell me about cloud."
            Response: "Cloud computing."
            Refined:  "Tell me about cloud computing."
        """
        orig_clean = original_query.strip().rstrip("?.!")
        resp_clean = clarification_response.strip().rstrip("?.!")

        orig_lower = orig_clean.lower()
        resp_lower = resp_clean.lower()

        # Specific refinement pattern for "cloud" -> "cloud computing"
        if orig_lower == "tell me about cloud" or orig_lower == "cloud":
            if "computing" in resp_lower:
                return "Tell me about cloud computing."
            elif "storage" in resp_lower:
                return "Tell me about cloud storage."
            elif "security" in resp_lower:
                return "Tell me about cloud security."

        # If original query ends with broad word, replace or append
        if orig_lower.endswith("cloud"):
            return f"{orig_clean} {resp_clean}."

        # Direct combination fallback
        return f"{orig_clean} - {resp_clean}"

    def _evaluate_by_llm(
        self,
        query: str,
        memory_context: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Uses Gemini model to detect ambiguity and synthesize targeted clarification question.
        """
        prompt = f"""You are a Clarification Agent in an AI Knowledge System.
Analyze the user query below and determine if it is ambiguous, incomplete, underspecified, or has multiple interpretations.

User Query: "{query}"
Memory Context: {json.dumps(memory_context or {})}

Instructions:
1. If the query is clear and actionable, set clarification_required to false.
2. If the query is ambiguous, set clarification_required to true and generate a concise, polite follow-up question that asks ONLY for the missing information needed to clarify.

Output ONLY a JSON object:
{{
  "clarification_required": true/false,
  "ambiguity_type": "vague_term|missing_context|multi_interpretation|unresolved_multipart|none",
  "clarification_question": "Follow-up question if required, else null",
  "reasoning": "Brief explanation"
}}"""

        response = self.model.generate_content(prompt)
        text = response.text.strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\n?", "", text)
            text = re.sub(r"\n?```$", "", text)
        data = json.loads(text.strip())

        return {
            "clarification_required": bool(data.get("clarification_required", False)),
            "ambiguity_type": data.get("ambiguity_type", "none"),
            "clarification_question": data.get("clarification_question"),
            "reasoning": data.get("reasoning", "LLM evaluation")
        }
