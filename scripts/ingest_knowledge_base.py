"""
Knowledge Base Ingestion Script
-------------------------------
Ingests all enterprise knowledge domain documents into ChromaDB HNSW vector store:
- AI/ML Knowledge Base (ai_ml_knowledge.txt)
- Cloud Computing Knowledge Base (cloud_computing_knowledge.txt)
- Cybersecurity Knowledge Base (cybersecurity_knowledge.txt)
- HR Policies (hr_policy.txt)
- Product Technical Manual (product_manual.txt)
"""

import os
import sys

# Path setup
script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(script_dir)
src_dir = os.path.join(root_dir, "src")
kb_dir = os.path.join(root_dir, "knowledge_base")
data_dir = os.path.join(root_dir, "data")

for p in [src_dir, root_dir]:
    if p not in sys.path:
        sys.path.insert(0, p)

from retrieval.vector_store import VectorStoreManager


def ingest_all_documents():
    vector_store = VectorStoreManager(
        collection_name="milestone2_knowledge_base",
        persist_directory=os.path.join(data_dir, "vectorstore")
    )

    domain_files = [
        "ai_ml_knowledge.txt",
        "cloud_computing_knowledge.txt",
        "cybersecurity_knowledge.txt",
        "hr_policy.txt",
        "product_manual.txt"
    ]

    total_indexed = 0
    print("=" * 65)
    print("AI Knowledge Retrieval Platform — Enterprise Ingestion Pipeline")
    print("=" * 65)

    for filename in domain_files:
        file_path = os.path.join(kb_dir, filename)
        if os.path.exists(file_path):
            print(f"[*] Ingesting {filename}...")
            chunks_count = vector_store.index_text_file(file_path, document_name=filename)
            total_indexed += chunks_count
            print(f"    -> Indexed {chunks_count} chunks.")
        else:
            print(f"[!] Warning: File {filename} not found at {file_path}")

    print("-" * 65)
    print(f"[OK] Ingestion complete. Newly processed chunks: {total_indexed}")
    print(f"[OK] Total chunks currently in vector store: {vector_store.count()}")
    print(f"[OK] Indexed documents: {vector_store.get_indexed_documents()}")
    print("=" * 65)


if __name__ == "__main__":
    ingest_all_documents()
