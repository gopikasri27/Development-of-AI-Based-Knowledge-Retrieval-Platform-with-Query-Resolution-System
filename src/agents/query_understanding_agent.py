"""
Query Understanding Agent (M2.1)
--------------------------------
Analyzes incoming user queries and classifies them into exactly one of:
- factual: Specific lookups, policies, definitions, dates, quantities, allowances.
- procedural: Step-by-step guides, workflows, installation, configuration instructions.
- comparative: Comparisons, differences, vs evaluations between editions/features.
- ambiguous: Vague, fragmented, underspecified, or out-of-domain inquiries.

Generates structured JSON output with query, query_type, classification_confidence, and routing.
"""

import os
import re
import json
from typing import Dict, Any, Optional

try:
    import google.generativeai as genai
except ImportError:
    genai = None


class QueryUnderstandingAgent:
    """
    M2.1 Query Understanding Agent for intent classification and query routing.
    """
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if self.api_key and genai:
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel("gemini-1.5-flash")
            except Exception:
                self.model = None
        else:
            self.model = None

    def analyze_query(self, query: str) -> Dict[str, Any]:
        """
        Main entry point. Analyzes and classifies the input query.
        Returns:
            {
                "query": str,
                "query_type": "factual" | "procedural" | "comparative" | "ambiguous",
                "classification_confidence": float (0.0 to 1.0),
                "routing": "retrieval" | "clarification"
            }
        """
        if not query or not query.strip():
            return {
                "query": query or "",
                "query_type": "ambiguous",
                "classification_confidence": 0.99,
                "routing": "clarification"
            }

        cleaned_query = query.strip()

        # Rule-based syntactic & semantic classification
        rule_result = self._classify_by_rules(cleaned_query)

        # If LLM model is active and rule confidence is moderate, refine with LLM
        if self.model and rule_result["classification_confidence"] < 0.85:
            try:
                llm_result = self._classify_by_llm(cleaned_query)
                if llm_result:
                    return llm_result
            except Exception:
                pass

        return rule_result

    def _classify_by_rules(self, query: str) -> Dict[str, Any]:
        """
        Deterministic rule-based intent classification engine based on linguistic patterns.
        """
        lower_q = query.lower().strip()
        words = re.findall(r'\b\w+\b', lower_q)

        # 1. Ambiguity & Vague Inquiries Detection
        ambiguous_exact = {
            "help", "test", "info", "information", "hello", "hi", "hey",
            "things", "stuff", "details", "explain everything", "tell me something",
            "what can you do", "who are you", "what is this", "anything", "etc",
            "policy", "manual", "guide", "leave", "sync", "cloud", "random query",
            "stuff and things", "things and stuff", "give me info", "can you help"
        }

        if lower_q in ambiguous_exact:
            return {
                "query": query,
                "query_type": "ambiguous",
                "classification_confidence": 0.95,
                "routing": "clarification"
            }

        ambiguous_regex_patterns = [
            r"^what can (?:you|the bot|the system) do\??$",
            r"^who are you\??$",
            r"^tell me (?:something|everything|anything)\??$",
            r"^explain (?:everything|anything|things|stuff)\??$",
            r"^(?:stuff|things)\s+and\s+(?:stuff|things)$",
            r"^just (?:testing|checking|a test)$",
            r"^(?:can you|could you)\s+help(?:\s+me)?\??$"
        ]
        for pat in ambiguous_regex_patterns:
            if re.match(pat, lower_q):
                return {
                    "query": query,
                    "query_type": "ambiguous",
                    "classification_confidence": 0.95,
                    "routing": "clarification"
                }

        # Single generic word
        if len(words) <= 1:
            return {
                "query": query,
                "query_type": "ambiguous",
                "classification_confidence": 0.92,
                "routing": "clarification"
            }

        # 2. Comparative Intent Patterns
        comparative_patterns = [
            r"\bcompare\b",
            r"\bcomparison\b",
            r"\bversus\b",
            r"\bvs\b",
            r"\bdifference\b",
            r"\bdifferences\b",
            r"\bdistinguish\b",
            r"\bwhich is better\b",
            r"\bbetter than\b",
            r"\bstandard (?:edition |tier )?vs (?:pro |enterprise )?",
            r"\bpro (?:edition |tier )?vs (?:standard )?",
            r"\bstandard (?:or|and) pro\b",
            r"\bhow does .* differ from\b"
        ]
        for pat in comparative_patterns:
            if re.search(pat, lower_q):
                return {
                    "query": query,
                    "query_type": "comparative",
                    "classification_confidence": 0.96,
                    "routing": "retrieval"
                }

        # 3. Procedural Intent Patterns
        procedural_patterns = [
            r"\bhow (?:do|can|should|to|would) (?:i|we|a user|one)\b",
            r"\bhow to\b",
            r"\bstep[s]? (?:to|for|involved)\b",
            r"\bprocedure\b",
            r"\binstructions\b",
            r"\bguide\b",
            r"\bworkflow\b",
            r"\binstall(?:ation)?\b",
            r"\bsetup\b",
            r"\bconfigure\b",
            r"\bconfiguration\b",
            r"\bdeploy(?:ment)?\b",
            r"\btroubleshoot(?:ing)?\b",
            r"\bexecute\b",
            r"\binitialize\b",
            r"\bcommand[s]? to\b",
            r"\bprocess of\b",
            r"\bhow do i apply\b",
            r"\bhow do i submit\b"
        ]
        for pat in procedural_patterns:
            if re.search(pat, lower_q):
                return {
                    "query": query,
                    "query_type": "procedural",
                    "classification_confidence": 0.94,
                    "routing": "retrieval"
                }

        # 4. Factual Intent Patterns
        factual_patterns = [
            r"\bwhat (?:is|are|was|were)\b",
            r"\bwho (?:is|are|handles)\b",
            r"\bwhen (?:is|are|does|do)\b",
            r"\bwhere (?:is|are)\b",
            r"\bhow many\b",
            r"\bhow much\b",
            r"\bwhat percentage\b",
            r"\bwhat rate\b",
            r"\bwhat date\b",
            r"\bwhat allowance\b",
            r"\bwhat policy\b",
            r"\bwhat limit\b",
            r"\bwhat rating\b",
            r"\bdoes (?:the|an|globaltech|cloudsync)\b",
            r"\bis (?:it|there|annual leave|hybrid|remote)\b",
            r"\bare employees\b",
            r"\bentitled to\b",
            r"\bannual leave policy\b",
            r"\bsick leave policy\b",
            r"\bhealth insurance\b",
            r"\bwellness allowance\b",
            r"\bper diem\b",
            r"\brate limit\b",
            r"\bsystem requirements\b"
        ]
        for pat in factual_patterns:
            if re.search(pat, lower_q):
                return {
                    "query": query,
                    "query_type": "factual",
                    "classification_confidence": 0.95,
                    "routing": "retrieval"
                }

        # Default fallback: If query has sufficient tokens, treat as factual lookup
        if len(words) >= 3:
            return {
                "query": query,
                "query_type": "factual",
                "classification_confidence": 0.80,
                "routing": "retrieval"
            }

        # If too brief and unrecognized, mark ambiguous
        return {
            "query": query,
            "query_type": "ambiguous",
            "classification_confidence": 0.88,
            "routing": "clarification"
        }

    def _classify_by_llm(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Uses Google Gemini model for zero-shot intent classification into strict schema.
        """
        prompt = f"""You are a Query Understanding Agent in an enterprise knowledge system.
Analyze the following user query and classify it into EXACTLY ONE of these categories:
- factual: Specific facts, policy details, limits, allowances, dates, definitions, eligibility.
- procedural: Step-by-step instructions, installation, configuration, troubleshooting, procedures.
- comparative: Comparing two entities, tiers, editions, or options (e.g. Standard vs Pro).
- ambiguous: Incomplete, vague, fragmented, or uninterpretable query.

Rules for routing:
- factual, procedural, comparative -> routing: "retrieval"
- ambiguous -> routing: "clarification"

User Query: "{query}"

Output ONLY a raw JSON object with this exact structure:
{{
  "query": "{query}",
  "query_type": "factual|procedural|comparative|ambiguous",
  "classification_confidence": 0.95,
  "routing": "retrieval|clarification"
}}"""
        response = self.model.generate_content(prompt)
        text = response.text.strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\n?", "", text)
            text = re.sub(r"\n?```$", "", text)
        data = json.loads(text.strip())

        valid_types = {"factual", "procedural", "comparative", "ambiguous"}
        q_type = data.get("query_type", "factual").lower()
        if q_type not in valid_types:
            q_type = "factual"

        routing = "clarification" if q_type == "ambiguous" else "retrieval"
        confidence = float(data.get("classification_confidence", 0.90))
        confidence = max(0.0, min(1.0, confidence))

        return {
            "query": query,
            "query_type": q_type,
            "classification_confidence": round(confidence, 2),
            "routing": routing
        }
