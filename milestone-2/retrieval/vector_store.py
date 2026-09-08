"""
Vector Store Manager for Milestone 2
------------------------------------
Interfaces with ChromaDB using HNSW Cosine distance indexing.
Handles document chunk ingestion, persistent storage, and nearest-neighbor
similarity search with structured metadata preservation.
"""

import os
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings

from .chunking import chunk_document
from .embeddings import generate_embeddings, generate_single_embedding

DEFAULT_COLLECTION_NAME = "milestone2_knowledge_base"
DEFAULT_PERSIST_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "data", "vectorstore")
)


class VectorStoreManager:
    """
    Manages vector database lifecycle, document indexing, and semantic search.
    """
    def __init__(
        self,
        collection_name: str = DEFAULT_COLLECTION_NAME,
        persist_directory: str = DEFAULT_PERSIST_DIR
    ):
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        os.makedirs(self.persist_directory, exist_ok=True)

        self.client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )

    def index_chunks(self, chunks: List[Dict[str, Any]]) -> int:
        """
        Indexes a list of pre-chunked items with embeddings and metadatas into ChromaDB.
        """
        if not chunks:
            return 0

        ids = [chunk["id"] for chunk in chunks]
        texts = [chunk["text"] for chunk in chunks]
        metadatas = [chunk["metadata"] for chunk in chunks]

        # Generate MiniLM dense embeddings
        embeddings = generate_embeddings(texts)

        # Upsert into ChromaDB
        self.collection.upsert(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas
        )
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
        Executes semantic nearest-neighbor search.
        
        Returns ranked list of results:
        [
            {
                "content": str,
                "document_name": str,
                "page": int,
                "section": str,
                "chunk_id": str,
                "relevance_score": float (0.0 to 1.0)
            }
        ]
        """
        if not query_text or not query_text.strip():
            return []

        count = self.collection.count()
        if count == 0:
            return []

        k = min(top_k, count)
        query_emb = generate_single_embedding(query_text)

        results = self.collection.query(
            query_embeddings=[query_emb],
            n_results=k,
            include=["documents", "metadatas", "distances"]
        )

        retrieved_results: List[Dict[str, Any]] = []

        if results and "ids" in results and len(results["ids"]) > 0:
            ids = results["ids"][0]
            docs = results["documents"][0]
            metas = results["metadatas"][0]
            dists = results["distances"][0] if "distances" in results and results["distances"] else [0.0] * len(ids)

            for i in range(len(ids)):
                # In ChromaDB cosine space, distance = 1 - cosine_similarity
                # So cosine_similarity = 1 - distance
                dist = dists[i] if i < len(dists) else 1.0
                similarity = round(max(0.0, min(1.0, 1.0 - dist)), 4)

                if similarity < score_threshold:
                    continue

                meta = metas[i] if i < len(metas) and metas[i] else {}
                doc_name = str(meta.get("document_name") or meta.get("source") or "unknown")
                page_num = int(meta.get("page", 1))
                section_name = str(meta.get("section") or "General")
                chunk_id = str(meta.get("chunk_id") or ids[i])

                retrieved_results.append({
                    "content": docs[i],
                    "document_name": doc_name,
                    "page": page_num,
                    "section": section_name,
                    "chunk_id": chunk_id,
                    "relevance_score": similarity
                })

        # Sort by relevance_score descending
        retrieved_results.sort(key=lambda x: x["relevance_score"], reverse=True)
        return retrieved_results

    def count(self) -> int:
        """Returns the total number of indexed chunks."""
        return self.collection.count()

    def get_indexed_documents(self) -> List[Dict[str, Any]]:
        """Summarizes unique documents indexed in the vector store."""
        count = self.collection.count()
        if count == 0:
            return []

        data = self.collection.get(include=["metadatas"])
        docs: Dict[str, Dict[str, Any]] = {}

        for meta in data.get("metadatas", []):
            if not meta:
                continue
            doc_name = str(meta.get("document_name") or meta.get("source") or "unknown")
            if doc_name not in docs:
                docs[doc_name] = {
                    "document_name": doc_name,
                    "chunks_count": 0,
                    "page": meta.get("page", 1),
                    "timestamp": meta.get("timestamp", "N/A")
                }
            docs[doc_name]["chunks_count"] += 1

        return list(docs.values())

    def reset(self):
        """Clears the collection and resets state."""
        try:
            self.client.delete_collection(name=self.collection_name)
        except Exception:
            pass
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
