"""
Milestone 2 Retrieval Package
-----------------------------
Includes chunking, embedding generation, and ChromaDB vector store utilities.
"""

from .chunking import chunk_document, extract_sections_and_chunk
from .embeddings import generate_embeddings, generate_single_embedding, compute_cosine_similarity
from .vector_store import VectorStoreManager

__all__ = [
    "chunk_document",
    "extract_sections_and_chunk",
    "generate_embeddings",
    "generate_single_embedding",
    "compute_cosine_similarity",
    "VectorStoreManager"
]
