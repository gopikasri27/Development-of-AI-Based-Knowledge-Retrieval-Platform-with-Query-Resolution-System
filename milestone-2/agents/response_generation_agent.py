"""
Response Generation Agent (M2.3)
--------------------------------
Synthesizes natural, grounded, and fact-verified answers strictly using retrieved context.
Generates structured JSON output with:
- answer: Clear, user-friendly response grounded in retrieved evidence.
- sources: Structured list of source attributions (document_name, page, chunk_id).
- confidence: Non-fabricated application confidence indicator (score, label: High/Medium/Low).

Handles insufficient evidence, anti-hallucination guardrails, and offline local synthesis.
"""

import os
import re
from typing import Dict, Any, List, Optional

try:
    import google.generativeai as genai
except ImportError:
    genai = None

INSUFFICIENT_INFO_MESSAGE = "Sufficient information was not found in the knowledge base to provide a reliable answer."


class ResponseGenerationAgent:
    """
    M2.3 Response Generation Agent for grounded answer synthesis and source attribution.
    """
    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-1.5-flash"):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.model_name = model_name
        if self.api_key and genai:
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel(self.model_name)
            except Exception:
                self.model = None
        else:
            self.model = None

    def generate_response(
        self,
        query: str,
        query_classification: Optional[Dict[str, Any]] = None,
        retrieved_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generates grounded response payload.
        
        Args:
            query (str): User question.
            query_classification (Optional[dict]): Intent classification from M2.1.
            retrieved_data (Optional[dict]): Retrieval output from M2.2 containing "results".
            
        Returns:
            {
                "answer": str,
                "sources": [
                    {
                        "document_name": str,
                        "page": int,
                        "chunk_id": str
                    }
                ],
                "confidence": {
                    "score": float,
                    "label": "High" | "Medium" | "Low"
                }
            }
        """
        results: List[Dict[str, Any]] = []
        if retrieved_data and "results" in retrieved_data:
            results = retrieved_data["results"]

        # If query is ambiguous or no retrieved results, return safe insufficient response
        is_ambiguous = (query_classification and query_classification.get("query_type") == "ambiguous")
        if is_ambiguous or not results:
            return {
                "answer": INSUFFICIENT_INFO_MESSAGE,
                "sources": [],
                "confidence": {
                    "score": 0.0,
                    "label": "Low"
                }
            }

        # Compute application confidence score from top retrieved chunk relevance
        top_score = float(results[0].get("relevance_score", 0.0))
        if top_score >= 0.75:
            confidence_label = "High"
        elif top_score >= 0.50:
            confidence_label = "Medium"
        else:
            confidence_label = "Low"

        # If highest score is below 0.50 threshold, treat as insufficient
        if top_score < 0.50:
            return {
                "answer": INSUFFICIENT_INFO_MESSAGE,
                "sources": [],
                "confidence": {
                    "score": round(top_score, 4),
                    "label": "Low"
                }
            }

        # Build unique structured sources list
        sources: List[Dict[str, Any]] = []
        seen_chunks = set()
        for r in results:
            cid = r.get("chunk_id", "")
            if cid and cid not in seen_chunks:
                seen_chunks.add(cid)
                sources.append({
                    "document_name": r.get("document_name", "unknown"),
                    "page": r.get("page", 1),
                    "chunk_id": cid
                })

        # Synthesize answer using Gemini LLM if available, else deterministic local generator
        q_type = query_classification.get("query_type", "factual") if query_classification else "factual"
        answer = None

        if self.model:
            try:
                answer = self._generate_llm_answer(query, q_type, results)
            except Exception:
                answer = None

        if not answer:
            answer = self._generate_local_grounded_answer(query, q_type, results)

        return {
            "answer": answer,
            "sources": sources,
            "confidence": {
                "score": round(top_score, 4),
                "label": confidence_label
            }
        }

    def _generate_llm_answer(self, query: str, query_type: str, results: List[Dict[str, Any]]) -> str:
        """
        Prompt Gemini with strict anti-hallucination grounding instructions.
        """
        context_blocks = []
        for idx, r in enumerate(results, 1):
            doc = r.get("document_name", "unknown")
            sec = r.get("section", "General")
            cid = r.get("chunk_id", f"chunk_{idx}")
            content = r.get("content", "").strip()
            context_blocks.append(
                f"[Source {idx}: {doc} | Section: {sec} | Chunk: {cid}]\n{content}"
            )
        context_str = "\n\n".join(context_blocks)

        system_instruction = (
            "You are a factual AI Knowledge Assistant in an enterprise retrieval system.\n"
            "STRICT GROUNDING RULES:\n"
            "1. Answer the user query using ONLY the verified facts from the RETRIEVED CONTEXT below.\n"
            "2. Do NOT use any external knowledge or assumptions not directly supported by the context.\n"
            "3. If the context does not contain the answer, say exactly: "
            f"'{INSUFFICIENT_INFO_MESSAGE}'\n"
            "4. Structure your response clearly according to the query type:\n"
            "   - Factual: Provide a direct, concise, and clear factual answer.\n"
            "   - Procedural: Provide clear numbered step-by-step instructions.\n"
            "   - Comparative: Provide a clear side-by-side or bulleted comparison.\n"
            "5. Cite document sources naturally where applicable."
        )

        prompt = f"""{system_instruction}

--- RETRIEVED CONTEXT ---
{context_str}
-------------------------

Query Type: {query_type}
User Query: {query}

Grounded Answer:"""

        response = self.model.generate_content(prompt)
        text = response.text.strip()
        return text

    def _generate_local_grounded_answer(
        self,
        query: str,
        query_type: str,
        results: List[Dict[str, Any]]
    ) -> str:
        """
        Deterministic local grounded synthesis engine when LLM API is unavailable.
        Extracts relevant facts directly from retrieved chunks and presents them coherently.
        """
        top_chunk = results[0]
        top_content = top_chunk.get("content", "").strip()
        doc_name = top_chunk.get("document_name", "document")
        sec_name = top_chunk.get("section", "Overview")

        if query_type == "procedural":
            # Extract procedural steps or lines
            steps = []
            for line in top_content.splitlines():
                line_s = line.strip()
                if line_s.startswith("Step") or re.match(r"^\d+\.", line_s) or line_s.startswith("-"):
                    steps.append(line_s)
            if steps:
                formatted_steps = "\n".join(steps)
                return f"Based on the technical documentation ({doc_name} – Section: {sec_name}), follow these steps:\n\n{formatted_steps}"
            return f"According to {doc_name} ({sec_name}):\n\n{top_content}"

        elif query_type == "comparative":
            # Extract comparison bullet points if available
            bullets = []
            for line in top_content.splitlines():
                line_s = line.strip()
                if line_s.startswith("-") or line_s.startswith("•") or ":" in line_s:
                    if not line_s.startswith("#"):
                        bullets.append(line_s)
            if bullets:
                formatted_bullets = "\n".join(bullets)
                return f"According to the comparative specifications in {doc_name} ({sec_name}):\n\n{formatted_bullets}"
            return f"Comparison details from {doc_name} ({sec_name}):\n\n{top_content}"

        else: # factual
            return f"According to {doc_name} ({sec_name}):\n\n{top_content}"
