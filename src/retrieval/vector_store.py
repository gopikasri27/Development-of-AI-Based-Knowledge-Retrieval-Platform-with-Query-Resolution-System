"""
Lightweight NumPy Vector Store Manager
--------------------------------------
Pure NumPy in-memory vector store using Cosine Similarity ranking.
Replaces ChromaDB to eliminate C++ compilation, SQLite version incompatibilities,
and heavy dependencies for serverless (Vercel) and constrained memory (Render Free).
Preserves full document metadata, chunk IDs, sections, page numbers, and relevance scores.
"""

import os
import json
import threading
from typing import List, Dict, Any, Optional
import numpy as np

try:
    from .chunking import chunk_document
except ImportError:
    from retrieval.chunking import chunk_document

try:
    from .embeddings import generate_embeddings, generate_single_embedding, compute_cosine_similarity, EMBEDDING_DIM
except ImportError:
    from retrieval.embeddings import generate_embeddings, generate_single_embedding, compute_cosine_similarity, EMBEDDING_DIM

DEFAULT_COLLECTION_NAME = "milestone2_knowledge_base"
DEFAULT_PERSIST_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "data", "vectorstore")
)


class VectorStoreManager:
    """
    In-memory NumPy vector database with Cosine Similarity ranking
    and optional compressed JSON/NPZ persistence.
    """
    def __init__(
        self,
        collection_name: str = DEFAULT_COLLECTION_NAME,
        persist_directory: str = DEFAULT_PERSIST_DIR
    ):
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        self._lock = threading.RLock()

        # In-memory storage
        self.chunks: List[Dict[str, Any]] = []
        self.embeddings: Optional[np.ndarray] = None  # shape (N, 768), float32

        if self.persist_directory:
            os.makedirs(self.persist_directory, exist_ok=True)
            self._load_from_disk()

        if self.count() == 0 and self.collection_name == DEFAULT_COLLECTION_NAME:
            self._initialize_default_docs()

    def _initialize_default_docs(self):
        """Indexes default knowledge base documents on startup if store is empty."""
        kb_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "knowledge_base"))
        if os.path.exists(kb_path):
            domain_files = [
                "ai_ml_knowledge.txt",
                "cloud_computing_knowledge.txt",
                "cybersecurity_knowledge.txt",
                "hr_policy.txt",
                "product_manual.txt"
            ]
            for filename in domain_files:
                fpath = os.path.join(kb_path, filename)
                if os.path.exists(fpath):
                    try:
                        self.index_text_file(fpath, document_name=filename)
                    except Exception:
                        pass

    @property
    def persist_file(self) -> str:
        return os.path.join(self.persist_directory, f"{self.collection_name}.npz")

    def _save_to_disk(self):
        """Optionally saves in-memory vector index to disk if writable."""
        if not self.persist_directory:
            return
        try:
            with self._lock:
                if self.embeddings is not None and len(self.chunks) > 0:
                    metadata_json = json.dumps(self.chunks, ensure_ascii=False)
                    np.savez_compressed(
                        self.persist_file,
                        embeddings=self.embeddings,
                        metadata=metadata_json
                    )
        except Exception:
            # On read-only serverless environments, fail silently and continue in-memory
            pass

    def _load_from_disk(self):
        """Loads vector index from disk if present."""
        if not self.persist_directory or not os.path.exists(self.persist_file):
            return
        try:
            with self._lock:
                data = np.load(self.persist_file, allow_pickle=False)
                loaded_embs = data["embeddings"].astype(np.float32)
                loaded_meta = json.loads(str(data["metadata"]))
                if len(loaded_embs) == len(loaded_meta):
                    # Check embedding dimension compatibility
                    if loaded_embs.ndim == 2 and loaded_embs.shape[1] == EMBEDDING_DIM:
                        self.embeddings = loaded_embs
                        self.chunks = loaded_meta
                    else:
                        # Old dimensionality mismatch - discard
                        self.reset()
        except Exception:
            self.chunks = []
            self.embeddings = None

    def index_chunks(self, chunks: List[Dict[str, Any]]) -> int:
        """
        Indexes a list of pre-chunked items with embeddings and metadatas into the vector store.
        """
        if not chunks:
            return 0

        texts = [chunk["text"] for chunk in chunks]
        new_embeddings_list = generate_embeddings(texts)
        new_embs = np.array(new_embeddings_list, dtype=np.float32)

        # Ensure unit L2 normalization for cosine similarity via dot product
        norms = np.linalg.norm(new_embs, axis=1, keepdims=True)
        norms[norms == 0.0] = 1.0
        new_embs = new_embs / norms

        with self._lock:
            existing_ids = {c["chunk_id"]: idx for idx, c in enumerate(self.chunks)}
            records_to_append = []
            embs_to_append = []

            for i, chunk in enumerate(chunks):
                cid = chunk.get("id") or chunk.get("chunk_id") or f"chunk_{len(self.chunks) + i}"
                meta = chunk.get("metadata") or {}
                doc_name = meta.get("document_name") or meta.get("source") or "unknown"
                page = int(meta.get("page", 1))
                section = meta.get("section") or "General"

                record = {
                    "content": chunk.get("text", ""),
                    "document_name": doc_name,
                    "page": page,
                    "section": section,
                    "chunk_id": cid,
                    "metadata": meta
                }

                if cid in existing_ids:
                    # Update in place
                    replace_idx = existing_ids[cid]
                    self.chunks[replace_idx] = record
                    self.embeddings[replace_idx] = new_embs[i]
                else:
                    records_to_append.append(record)
                    embs_to_append.append(new_embs[i])

            if records_to_append:
                self.chunks.extend(records_to_append)
                append_arr = np.array(embs_to_append, dtype=np.float32)
                if self.embeddings is None or len(self.embeddings) == 0:
                    self.embeddings = append_arr
                else:
                    self.embeddings = np.vstack([self.embeddings, append_arr])

            self._save_to_disk()

        return len(chunks)

    def index_text_file(
        self,
        file_path: str,
        document_name: Optional[str] = None,
        page: int = 1
    ) -> int:
        """
        Reads, chunks, and indexes a text/markdown file into the vector store.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        doc_name = document_name or os.path.basename(file_path)
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        chunks = chunk_document(
            text=content,
            filename=doc_name,
            page=page
        )
        return self.index_chunks(chunks)

    def query(
        self,
        query_text: str,
        top_k: int = 5,
        score_threshold: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Executes semantic nearest-neighbor search using Cosine Similarity.
        """
        if not query_text or not query_text.strip():
            return []

        with self._lock:
            count = len(self.chunks)
            if count == 0 or self.embeddings is None:
                return []

            query_emb = generate_single_embedding(query_text)
            q_vec = np.array(query_emb, dtype=np.float32)
            q_norm = np.linalg.norm(q_vec)
            if q_norm > 0:
                q_vec /= q_norm

            raw_scores = np.dot(self.embeddings, q_vec)
            if not os.environ.get("GEMINI_API_KEY"):
                # Scale fallback scores to compensate for query-document length disparity
                # Suppress incidental low overlap (< 0.13)
                scores = np.where(
                    raw_scores < 0.13,
                    np.maximum(0.0, raw_scores * 0.5),
                    np.clip(raw_scores * 2.1, 0.0, 1.0)
                )
            else:
                scores = np.clip(raw_scores, 0.0, 1.0)

            # Rank by score descending
            ranked_indices = np.argsort(-scores)

            retrieved_results: List[Dict[str, Any]] = []
            for idx in ranked_indices:
                score = round(float(scores[idx]), 4)
                if score < score_threshold:
                    continue

                chunk = self.chunks[idx]
                retrieved_results.append({
                    "content": chunk.get("content", ""),
                    "document_name": chunk.get("document_name", "unknown"),
                    "page": chunk.get("page", 1),
                    "section": chunk.get("section", "General"),
                    "chunk_id": chunk.get("chunk_id", f"chunk_{idx}"),
                    "relevance_score": score
                })
                if len(retrieved_results) >= top_k:
                    break

            return retrieved_results

    def count(self) -> int:
        """Returns total number of indexed chunks."""
        with self._lock:
            return len(self.chunks)

    def get_indexed_documents(self) -> List[Dict[str, Any]]:
        """Summarizes unique documents indexed in the vector store."""
        with self._lock:
            if not self.chunks:
                return []

            docs: Dict[str, Dict[str, Any]] = {}
            for chunk in self.chunks:
                doc_name = chunk.get("document_name", "unknown")
                if doc_name not in docs:
                    docs[doc_name] = {
                        "document_name": doc_name,
                        "chunks_count": 0,
                        "page": chunk.get("page", 1),
                        "timestamp": chunk.get("metadata", {}).get("timestamp", "N/A")
                    }
                docs[doc_name]["chunks_count"] += 1

            return list(docs.values())

    def reset(self):
        """Clears in-memory collection and removes persistent index."""
        with self._lock:
            self.chunks = []
            self.embeddings = None
            if self.persist_directory and os.path.exists(self.persist_file):
                try:
                    os.remove(self.persist_file)
                except Exception:
                    pass
