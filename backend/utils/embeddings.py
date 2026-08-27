"""
Embeddings and Vector Store Utility Module
------------------------------------------
Generates dense vector embeddings via sentence-transformers (all-MiniLM-L6-v2)
and indexes / queries vectors against local persistent ChromaDB with cosine metric.
"""

import os
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from dotenv import load_dotenv

load_dotenv()

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

# Global model singleton for efficient in-memory reuse
_EMBEDDING_MODEL = None
_CHROMA_CLIENT = None
_COLLECTION = None

DEFAULT_COLLECTION_NAME = "rag_knowledge_base"
DEFAULT_MODEL_NAME = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VECTOR_STORE_DIR = os.getenv("CHROMA_PERSIST_DIR", os.path.join(BASE_DIR, "vectorstore"))


def get_embedding_model(model_name: str = DEFAULT_MODEL_NAME):
    """Loads and caches the SentenceTransformer embedding model."""
    global _EMBEDDING_MODEL
    if _EMBEDDING_MODEL is None:
        if SentenceTransformer is None:
            raise ImportError("sentence-transformers is not installed. Please install it.")
        print(f"Loading SentenceTransformer embedding model: {model_name}...")
        _EMBEDDING_MODEL = SentenceTransformer(model_name)
    return _EMBEDDING_MODEL


def get_chroma_client(persist_directory: str = VECTOR_STORE_DIR):
    """Initializes and caches the persistent ChromaDB client."""
    global _CHROMA_CLIENT
    if _CHROMA_CLIENT is None:
        os.makedirs(persist_directory, exist_ok=True)
        _CHROMA_CLIENT = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False, is_persistent=True)
        )
    return _CHROMA_CLIENT


def get_or_create_collection(
    collection_name: str = DEFAULT_COLLECTION_NAME,
    persist_directory: str = VECTOR_STORE_DIR
):
    """Retrieves or creates a ChromaDB collection with cosine distance."""
    global _COLLECTION
    client = get_chroma_client(persist_directory)
    _COLLECTION = client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}
    )
    return _COLLECTION


def generate_embeddings(texts: List[str], model_name: str = DEFAULT_MODEL_NAME) -> List[List[float]]:
    """Generates dense vector embeddings for a list of text strings."""
    if not texts:
        return []
    model = get_embedding_model(model_name)
    embeddings = model.encode(texts, show_progress_bar=False, normalize_embeddings=True)
    return embeddings.tolist()


def generate_single_embedding(text: str, model_name: str = DEFAULT_MODEL_NAME) -> List[float]:
    """Generates embedding for a single text string."""
    embs = generate_embeddings([text], model_name)
    return embs[0] if embs else []


def index_chunks(
    chunks: List[Dict[str, Any]],
    collection_name: str = DEFAULT_COLLECTION_NAME,
    persist_directory: str = VECTOR_STORE_DIR
) -> int:
    """
    Indexes chunk objects into ChromaDB.
    
    Each chunk dict format:
    {
        "id": str,
        "text": str,
        "metadata": dict
    }
    
    Returns the number of successfully indexed chunks.
    """
    if not chunks:
        return 0
        
    collection = get_or_create_collection(collection_name, persist_directory)
    
    ids = [chunk["id"] for chunk in chunks]
    documents = [chunk["text"] for chunk in chunks]
    metadatas = [chunk["metadata"] for chunk in chunks]
    
    # Generate embeddings
    embeddings = generate_embeddings(documents)
    
    # Upsert into ChromaDB
    collection.upsert(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas
    )
    
    return len(chunks)


def query_collection(
    query_text: str,
    top_k: int = 5,
    collection_name: str = DEFAULT_COLLECTION_NAME,
    persist_directory: str = VECTOR_STORE_DIR,
    filter_metadata: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Performs semantic vector search in ChromaDB.
    
    Returns list of dicts with:
    - id
    - text
    - metadata
    - distance (cosine distance: 0 = identical, 2 = opposite)
    - similarity (cosine similarity: 1 - distance, range [0, 1])
    """
    collection = get_or_create_collection(collection_name, persist_directory)
    
    count = collection.count()
    if count == 0:
        return []
        
    k = min(top_k, count)
    query_emb = generate_single_embedding(query_text)
    
    kwargs: Dict[str, Any] = {
        "query_embeddings": [query_emb],
        "n_results": k,
        "include": ["documents", "metadatas", "distances"]
    }
    if filter_metadata:
        kwargs["where"] = filter_metadata
        
    results = collection.query(**kwargs)
    
    retrieved_items = []
    if results and "ids" in results and len(results["ids"]) > 0:
        ids = results["ids"][0]
        docs = results["documents"][0]
        metas = results["metadatas"][0]
        dists = results["distances"][0] if "distances" in results and results["distances"] else [0.0] * len(ids)
        
        for i in range(len(ids)):
            # With hnsw:space = cosine, Chroma distance is (1 - cosine_sim)
            # Hence cosine_sim = 1 - distance (clamped between 0.0 and 1.0)
            dist = dists[i] if i < len(dists) else 1.0
            similarity = max(0.0, min(1.0, 1.0 - dist))
            
            retrieved_items.append({
                "id": ids[i],
                "text": docs[i],
                "metadata": metas[i] if i < len(metas) else {},
                "distance": round(dist, 4),
                "similarity": round(similarity, 4)
            })
            
    return retrieved_items


def get_all_indexed_documents(
    collection_name: str = DEFAULT_COLLECTION_NAME,
    persist_directory: str = VECTOR_STORE_DIR
) -> List[Dict[str, Any]]:
    """Retrieves unique indexed source files and their chunk counts."""
    collection = get_or_create_collection(collection_name, persist_directory)
    count = collection.count()
    if count == 0:
        return []
        
    all_data = collection.get(include=["metadatas"])
    doc_summary: Dict[str, Dict[str, Any]] = {}
    
    for meta in all_data.get("metadatas", []):
        if not meta:
            continue
        src = str(meta.get("source", "unknown"))
        if src not in doc_summary:
            doc_summary[src] = {
                "source": src,
                "chunks": 0,
                "timestamp": meta.get("timestamp", "N/A")
            }
        doc_summary[src]["chunks"] += 1
        
    return list(doc_summary.values())


def reset_collection(
    collection_name: str = DEFAULT_COLLECTION_NAME,
    persist_directory: str = VECTOR_STORE_DIR
):
    """Deletes and recreates the collection."""
    global _COLLECTION
    client = get_chroma_client(persist_directory)
    try:
        client.delete_collection(name=collection_name)
    except Exception:
        pass
    _COLLECTION = client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}
    )
    return _COLLECTION
