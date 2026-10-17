"""
Embeddings Generation Module for Milestone 2
--------------------------------------------
Generates 384-dimensional dense semantic embeddings using
sentence-transformers (all-MiniLM-L6-v2) as specified in Milestone 1 architecture.
Includes cosine similarity utilities and normalized vector representations.
"""

import numpy as np
from typing import List, Optional

DEFAULT_MODEL_NAME = "all-MiniLM-L6-v2"
_EMBEDDING_MODEL = None


def get_embedding_model(model_name: str = DEFAULT_MODEL_NAME):
    """
    Lazy-loads and caches the SentenceTransformer embedding model.
    """
    global _EMBEDDING_MODEL
    if _EMBEDDING_MODEL is None:
        from sentence_transformers import SentenceTransformer
        _EMBEDDING_MODEL = SentenceTransformer(model_name)
    return _EMBEDDING_MODEL


def generate_embeddings(
    texts: List[str],
    model_name: str = DEFAULT_MODEL_NAME
) -> List[List[float]]:
    """
    Generates normalized 384-d dense vector embeddings for a list of strings.
    """
    if not texts:
        return []

    model = get_embedding_model(model_name)
    embeddings = model.encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False
    )
    return embeddings.tolist()


def generate_single_embedding(
    text: str,
    model_name: str = DEFAULT_MODEL_NAME
) -> List[float]:
    """
    Generates normalized embedding for a single text query.
    """
    if not text or not text.strip():
        return [0.0] * 384

    embeddings = generate_embeddings([text], model_name)
    return embeddings[0] if embeddings else [0.0] * 384


def compute_cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Computes cosine similarity between two float vectors in [0.0, 1.0].
    """
    a = np.array(vec1, dtype=np.float32)
    b = np.array(vec2, dtype=np.float32)

    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)

    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    dot = np.dot(a, b) / (norm_a * norm_b)
    # Clamp between 0.0 and 1.0
    return float(np.clip(dot, 0.0, 1.0))
