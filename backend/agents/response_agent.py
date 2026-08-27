"""
Response Generation Agent
------------------------
Role: Synthesizes a grounded, accurate response using retrieved knowledge chunks.
Integrates with Google Gemini API (gemini-1.5-flash / gemini-2.0-flash / free tier)
and includes explicit source citations. Features an intelligent local synthesis
fallback if an API key is not yet set.
"""

import os
import warnings
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

load_dotenv()

# Suppress deprecation warnings from legacy generativeai if present
warnings.filterwarnings("ignore", category=FutureWarning, module="google.generativeai")

try:
    import google.generativeai as genai
except ImportError:
    genai = None


class ResponseAgent:
    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        self.api_key = os.getenv("GEMINI_API_KEY", "").strip()
        self.model = None
        self.has_gemini = False
        self._init_gemini()

    def _init_gemini(self) -> None:
        """Configures the Google Gemini API client if API key is present."""
        if self.api_key and genai is not None:
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel(self.model_name)
                self.has_gemini = True
            except Exception as e:
                print(f"Warning: Failed to initialize Gemini API: {e}")
                self.model = None
                self.has_gemini = False
        else:
            self.model = None
            self.has_gemini = False

    def build_prompt(
        self,
        query: str,
        query_type: str,
        retrieved_chunks: List[Dict[str, Any]],
        history: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """Constructs a grounded RAG system prompt with source context."""
        history = history or []
        
        # Format context blocks with clear citation tags
        context_blocks = []
        for i, chunk in enumerate(retrieved_chunks):
            source = chunk.get("metadata", {}).get("source", f"Doc_{i+1}")
            chunk_id = chunk.get("metadata", {}).get("chunk_id", f"chunk_{i}")
            similarity = chunk.get("similarity", 0.0)
            text = chunk.get("text", "").strip()
            
            context_blocks.append(
                f"[Source {i+1}: {source} | Chunk: {chunk_id} | Relevance: {int(similarity * 100)}%]\n{text}"
            )
            
        context_text = "\n\n---\n\n".join(context_blocks)
        
        # Format recent conversation context
        history_text = ""
        if history:
            history_lines = []
            for item in history[-3:]:  # last 3 turns
                role = "User" if item.get("role") == "user" else "Assistant"
                history_lines.append(f"{role}: {item.get('message', '')}")
            history_text = "\nRecent Conversation History:\n" + "\n".join(history_lines) + "\n"

        prompt = f"""You are an accurate, helpful AI Knowledge Assistant for an enterprise Retrieval-Augmented Generation (RAG) platform.

Your task is to answer the user's question STRICTLY based on the provided Knowledge Base context.

Rules:
1. Grounding: Rely ONLY on the facts stated in the context. Do NOT make assumptions or hallucinate.
2. Citations: Explicitly cite your sources using tags like [Source: filename] or [Source 1] whenever mentioning specific facts.
3. Query Type Adaptation:
   - Factual ({query_type}): Be crisp, direct, and provide concise facts.
   - Procedural ({query_type}): Provide numbered, step-by-step instructions.
   - Comparative ({query_type}): Structure differences/similarities in bullet points or clear comparisons.
4. If the context does not fully answer the question, state what is known and clarify what is missing.

{history_text}
=== KNOWLEDGE BASE CONTEXT ===
{context_text}
==============================

User Query: {query}

Answer:"""
        return prompt

    def _generate_with_gemini(self, prompt: str) -> str:
        """Calls the Gemini API to generate the response."""
        if not self.model:
            raise RuntimeError("Gemini model is not initialized.")
        response = self.model.generate_content(prompt)
        return response.text.strip()

    def _fallback_local_synthesis(
        self,
        query: str,
        query_type: str,
        retrieved_chunks: List[Dict[str, Any]]
    ) -> str:
        """
        Structured local synthesis engine used when GEMINI_API_KEY is not yet supplied.
        Extracts key excerpts and provides structured answers with citations.
        """
        if not retrieved_chunks:
            return "No matching information was found in the indexed documents to answer this question."

        lines = [
            f"Based on the indexed knowledge base ({len(retrieved_chunks)} relevant source sections found):",
            ""
        ]

        # Present the primary grounded answer from top chunk
        top_chunk = retrieved_chunks[0]
        top_source = top_chunk.get("metadata", {}).get("source", "Document")
        lines.append(f"**Key Findings from [{top_source}] (Relevance: {int(top_chunk.get('similarity', 0)*100)}%):**")
        lines.append(f"> {top_chunk.get('text', '').strip()}")
        lines.append("")

        # Add supplementary insights from additional chunks if available
        if len(retrieved_chunks) > 1:
            lines.append("**Additional Context:**")
            for i, chunk in enumerate(retrieved_chunks[1:3], 2):
                src = chunk.get("metadata", {}).get("source", f"Source {i}")
                preview = chunk.get("text", "").strip()
                if len(preview) > 200:
                    preview = preview[:200] + "..."
                lines.append(f"- **[{src}]**: {preview}")
            lines.append("")

        lines.append("*(Note: To enable generative LLM answers, add your Google Gemini API key to backend/.env)*")
        return "\n".join(lines)

    def process(
        self,
        query_data: Dict[str, Any],
        retrieval_data: Dict[str, Any],
        history: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Executes the response generation agent workflow.
        Returns generated answer, structured citations list, and metadata.
        """
        query = query_data.get("original_query", "")
        query_type = query_data.get("query_type", "factual")
        retrieved_chunks = retrieval_data.get("retrieved_chunks", [])
        
        # Build citations metadata list
        citations = []
        for i, chunk in enumerate(retrieved_chunks):
            meta = chunk.get("metadata", {})
            citations.append({
                "source_index": i + 1,
                "source_file": meta.get("source", "Unknown Document"),
                "chunk_id": meta.get("chunk_id", f"chunk_{i}"),
                "similarity_score": chunk.get("similarity", 0.0),
                "excerpt": chunk.get("text", "")[:180] + "..." if len(chunk.get("text", "")) > 180 else chunk.get("text", "")
            })

        # Re-check gemini configuration in case key was updated in environment
        if not self.has_gemini:
            self.api_key = os.getenv("GEMINI_API_KEY", "").strip()
            self._init_gemini()

        prompt = self.build_prompt(query, query_type, retrieved_chunks, history)
        
        if self.has_gemini and self.model:
            try:
                answer = self._generate_with_gemini(prompt)
                engine = f"Gemini ({self.model_name})"
            except Exception as e:
                print(f"Gemini API invocation error: {e}. Falling back to local synthesis.")
                answer = self._fallback_local_synthesis(query, query_type, retrieved_chunks)
                engine = "Local Synthesis Fallback"
        else:
            answer = self._fallback_local_synthesis(query, query_type, retrieved_chunks)
            engine = "Local Synthesis Engine"

        return {
            "agent": "Response Generation Agent",
            "answer": answer,
            "citations": citations,
            "engine": engine,
            "query_type": query_type,
            "prompt_used": prompt
        }
