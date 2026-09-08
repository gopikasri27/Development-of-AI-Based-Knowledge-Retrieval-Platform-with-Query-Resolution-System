"""
Retrieval Agent (M2.2)
----------------------
Executes semantic nearest-neighbor search over the indexed knowledge base.
Accepts user query and query classification metadata.
Retrieves Top-K ranked document chunks, applies low-confidence threshold filtering,
preserves document metadata (document name, page, section, chunk ID, relevance score),
and handles no-result or low-confidence cases.
"""

from typing import Dict, Any, List, Optional
import os
import sys

# Ensure local imports resolve
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from retrieval.vector_store import VectorStoreManager, DEFAULT_COLLECTION_NAME, DEFAULT_PERSIST_DIR


class RetrievalAgent:
    """
    M2.2 Semantic Retrieval Agent for vector search and passage ranking.
    """
    def __init__(
        self,
        vector_store: Optional[VectorStoreManager] = None,
        top_k: int = 5,
        confidence_threshold: float = 0.50,
        collection_name: str = DEFAULT_COLLECTION_NAME,
        persist_directory: str = DEFAULT_PERSIST_DIR
    ):
        self.vector_store = vector_store or VectorStoreManager(
            collection_name=collection_name,
            persist_directory=persist_directory
        )
        self.top_k = top_k
        self.confidence_threshold = confidence_threshold

    def retrieve(
        self,
        query: str,
        query_classification: Optional[Dict[str, Any]] = None,
        top_k: Optional[int] = None,
        confidence_threshold: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Retrieves Top-K relevant chunks for the query.
        
        Args:
            query (str): The user search question.
            query_classification (Optional[dict]): Output from QueryUnderstandingAgent.
            top_k (Optional[int]): Number of chunks to retrieve (overrides default).
            confidence_threshold (Optional[float]): Minimum similarity score filter.
            
        Returns:
            {
                "query": str,
                "results": [
                    {
                        "content": str,
                        "document_name": str,
                        "page": int,
                        "section": str,
                        "chunk_id": str,
                        "relevance_score": float
                    }
                ],
                "result_count": int
            }
        """
        k = top_k if top_k is not None else self.top_k
        threshold = confidence_threshold if confidence_threshold is not None else self.confidence_threshold

        if not query or not query.strip():
            return {
                "query": query or "",
                "results": [],
                "result_count": 0
            }

        # If query was marked ambiguous by query understanding agent and routing is clarification,
        # we can still perform search or return empty if desired.
        if query_classification and query_classification.get("routing") == "clarification":
            # For ambiguous queries, search may produce low relevance results which will be filtered
            pass

        # Perform semantic vector search
        raw_results = self.vector_store.query(
            query_text=query,
            top_k=k,
            score_threshold=threshold
        )

        # Ensure output contract compliance
        formatted_results: List[Dict[str, Any]] = []
        for item in raw_results:
            formatted_results.append({
                "content": item.get("content", ""),
                "document_name": item.get("document_name", "unknown"),
                "page": item.get("page", 1),
                "section": item.get("section", "General"),
                "chunk_id": item.get("chunk_id", "chunk_0"),
                "relevance_score": round(float(item.get("relevance_score", 0.0)), 4)
            })

        return {
            "query": query,
            "results": formatted_results,
            "result_count": len(formatted_results)
        }
