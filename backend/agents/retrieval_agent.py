"""
Retrieval Agent
--------------
Role: Performs semantic vector search over ChromaDB knowledge base.
Fetches top-k relevant chunks (default k=5) with similarity scores.
"""

from typing import Dict, Any, List
from utils.embeddings import query_collection


class RetrievalAgent:
    def __init__(self, default_top_k: int = 5, min_confidence_threshold: float = 0.50):
        self.default_top_k = default_top_k
        self.min_confidence_threshold = min_confidence_threshold

    def process(self, query_agent_output: Dict[str, Any], top_k: int = None) -> Dict[str, Any]:
        """
        Executes semantic vector retrieval based on the processed query.
        
        Returns:
            Dict containing:
            - retrieved_chunks: list of top matching chunks with scores & metadata
            - top_similarity: highest cosine similarity score in the result
            - avg_similarity: average similarity score across top results
            - has_high_confidence: boolean flag indicating if results surpass threshold
        """
        k = top_k or self.default_top_k
        search_query = query_agent_output.get("reformulated_query") or query_agent_output.get("cleaned_query")
        
        chunks = query_collection(search_query, top_k=k)
        
        if not chunks:
            return {
                "agent": "Retrieval Agent",
                "search_query": search_query,
                "chunks_count": 0,
                "retrieved_chunks": [],
                "top_similarity": 0.0,
                "avg_similarity": 0.0,
                "has_high_confidence": False,
                "status": "empty"
            }
            
        similarities = [c["similarity"] for c in chunks]
        top_sim = max(similarities) if similarities else 0.0
        avg_sim = sum(similarities) / len(similarities) if similarities else 0.0
        
        has_confidence = top_sim >= self.min_confidence_threshold
        
        return {
            "agent": "Retrieval Agent",
            "search_query": search_query,
            "chunks_count": len(chunks),
            "retrieved_chunks": chunks,
            "top_similarity": round(top_sim, 4),
            "avg_similarity": round(avg_sim, 4),
            "has_high_confidence": has_confidence,
            "status": "success" if has_confidence else "low_confidence"
        }
