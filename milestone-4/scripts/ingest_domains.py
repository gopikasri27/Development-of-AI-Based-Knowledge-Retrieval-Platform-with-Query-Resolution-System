"""
Ingest Domain Documents into Vector Store
-----------------------------------------
Ingests the Milestone 4 knowledge domain documents:
- AI/ML Knowledge Base (ai_ml_knowledge.txt)
- Cloud Computing Knowledge Base (cloud_computing_knowledge.txt)
- Cybersecurity Knowledge Base (cybersecurity_knowledge.txt)
"""

import os
import sys

# Add project root and milestone-2 to sys.path
script_dir = os.path.dirname(os.path.abspath(__file__))
m4_dir = os.path.dirname(script_dir)
root_dir = os.path.dirname(m4_dir)
m2_dir = os.path.join(root_dir, "milestone-2")

for p in [m2_dir, root_dir]:
    if p not in sys.path:
        sys.path.insert(0, p)

from retrieval.vector_store import VectorStoreManager

def ingest_all_domains():
    vector_store = VectorStoreManager()
    domains_dir = os.path.join(m4_dir, "knowledge_domains")
    
    domain_files = [
        "ai_ml_knowledge.txt",
        "cloud_computing_knowledge.txt",
        "cybersecurity_knowledge.txt"
    ]
    
    total_indexed = 0
    print("=" * 60)
    print("Milestone 4 Knowledge Domain Ingestion")
    print("=" * 60)
    
    for filename in domain_files:
        file_path = os.path.join(domains_dir, filename)
        if os.path.exists(file_path):
            print(f"[*] Ingesting {filename}...")
            chunks_count = vector_store.index_text_file(file_path, document_name=filename)
            total_indexed += chunks_count
            print(f"    -> Indexed {chunks_count} chunks.")
        else:
            print(f"[!] Warning: File {filename} not found at {file_path}")
            
    print("-" * 60)
    print(f"[OK] Ingestion complete. Total new chunks indexed: {total_indexed}")
    print(f"[OK] Total chunks now in vector store: {vector_store.count()}")
    print(f"[OK] Indexed documents: {vector_store.get_indexed_documents()}")
    print("=" * 60)

if __name__ == "__main__":
    ingest_all_domains()
