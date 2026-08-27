"""
Validation and Retrieval Accuracy Test Script
--------------------------------------------
Milestone 1 Test Suite for AI Knowledge Retrieval Platform:
1. Ingests 2 sample knowledge domains:
   - HR Policy (hr_policy.txt)
   - Product Technical Manual (product_manual.txt)
2. Executes 7 curated test queries:
   - 2 Factual queries
   - 2 Procedural queries
   - 2 Comparative queries
   - 1 Unavailable-info query (out-of-domain)
3. Evaluates Top-1, Top-3, Top-5 retrieval accuracy.
4. Identifies and flags low-relevance queries (score < 0.50).
5. Demonstrates the full multi-agent pipeline output.
"""

import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from utils.extract_text import extract_text
from utils.chunking import chunk_document
from utils.embeddings import index_chunks, reset_collection, query_collection
from utils.db import save_document_record, init_db
from agents.orchestrator import MultiAgentRAGOrchestrator


def setup_knowledge_base():
    """Ingests the two sample documents into ChromaDB."""
    print("=" * 70)
    print("STEP 1: Setting up Knowledge Base (Ingesting Sample Documents)")
    print("=" * 70)
    
    init_db()
    reset_collection()
    
    sample_files = [
        os.path.join(BASE_DIR, "sample_data", "hr_policy.txt"),
        os.path.join(BASE_DIR, "sample_data", "product_manual.txt")
    ]
    
    total_indexed = 0
    for file_path in sample_files:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Missing sample file: {file_path}")
            
        filename = os.path.basename(file_path)
        extracted = extract_text(file_path)
        chunks = chunk_document(
            text=extracted["text"],
            filename=filename,
            chunk_size=500,
            chunk_overlap=50
        )
        count = index_chunks(chunks)
        total_indexed += count
        save_document_record(
            filename=filename,
            file_path=file_path,
            file_type=".txt",
            file_size=extracted["size_bytes"],
            chunks_count=count
        )
        print(f" -> Ingested '{filename}': {len(extracted['text'])} chars split into {count} chunks.")
        
    print(f"Total chunks successfully indexed in ChromaDB: {total_indexed}\n")


def run_evaluation():
    """Runs test queries and evaluates retrieval performance."""
    print("=" * 70)
    print("STEP 2: Executing Retrieval Accuracy & Multi-Agent Tests")
    print("=" * 70)

    # Test query definitions with expected ground truth sources and expected query types
    test_suite = [
        # --- 2 Factual Queries ---
        {
            "id": "FACT-01",
            "type": "factual",
            "query": "How many days of paid annual leave do full-time employees receive per year at GlobalTech?",
            "expected_source": "hr_policy.txt",
            "expected_keywords": ["annual leave", "20 days", "paid annual leave"],
            "is_available": True
        },
        {
            "id": "FACT-02",
            "type": "factual",
            "query": "What are the minimum hardware RAM and CPU core requirements for CloudSync Pro?",
            "expected_source": "product_manual.txt",
            "expected_keywords": ["4 cpu cores", "16 gb ram", "linux"],
            "is_available": True
        },
        # --- 2 Procedural Queries ---
        {
            "id": "PROC-01",
            "type": "procedural",
            "query": "What are the step-by-step instructions to install and configure CloudSync Pro on Linux?",
            "expected_source": "product_manual.txt",
            "expected_keywords": ["install.sh", "cloudsync-admin", "step"],
            "is_available": True
        },
        {
            "id": "PROC-02",
            "type": "procedural",
            "query": "How do I submit a medical certificate if my sick leave exceeds 3 consecutive days?",
            "expected_source": "hr_policy.txt",
            "expected_keywords": ["medical certificate", "hr portal", "3 consecutive"],
            "is_available": True
        },
        # --- 2 Comparative Queries ---
        {
            "id": "COMP-01",
            "type": "comparative",
            "query": "Compare the transaction throughput and encryption security between CloudSync Standard and CloudSync Pro.",
            "expected_source": "product_manual.txt",
            "expected_keywords": ["5,000", "50,000", "aes-128", "aes-256", "standard"],
            "is_available": True
        },
        {
            "id": "COMP-02",
            "type": "comparative",
            "query": "What is the difference between working in the corporate office versus remote days under the hybrid work policy?",
            "expected_source": "hr_policy.txt",
            "expected_keywords": ["3-2", "tuesday", "remote", "office"],
            "is_available": True
        },
        # --- 1 Unavailable-Info Query ---
        {
            "id": "UNAV-01",
            "type": "unavailable-info",
            "query": "What is the company policy for employee stock option vesting schedules for subsidiary offices in Tokyo?",
            "expected_source": None,
            "expected_keywords": [],
            "is_available": False
        }
    ]

    top_1_hits = 0
    top_3_hits = 0
    top_5_hits = 0
    evaluable_count = 0
    orchestrator = MultiAgentRAGOrchestrator()

    for idx, test in enumerate(test_suite, 1):
        print("-" * 70)
        print(f"Test #{idx} [{test['id']}] Category: {test['type'].upper()}")
        print(f"Query: \"{test['query']}\"")
        
        # 1. Direct Vector Search Retrieval Check
        retrieved = query_collection(test["query"], top_k=5)
        top_sim = retrieved[0]["similarity"] if retrieved else 0.0
        
        print(f"ChromaDB Results: {len(retrieved)} chunks retrieved (Top-1 Similarity: {top_sim:.4f})")
        
        # Check for Low-Relevance Flag (< 0.50)
        if top_sim < 0.50:
            print(" [!] FLAG: Low-Relevance Result (Similarity < 0.50) -> Candidate for Clarification Agent")
        else:
            print(f" [*] High Relevance Confirmed (Relevance: {int(top_sim * 100)}%)")

        # Evaluate Top-k accuracy if ground truth expected
        if test["is_available"] and test["expected_source"]:
            evaluable_count += 1
            sources_in_order = [c.get("metadata", {}).get("source") for c in retrieved]
            
            hit_1 = (len(sources_in_order) >= 1 and sources_in_order[0] == test["expected_source"])
            hit_3 = any(src == test["expected_source"] for src in sources_in_order[:3])
            hit_5 = any(src == test["expected_source"] for src in sources_in_order[:5])
            
            if hit_1: top_1_hits += 1
            if hit_3: top_3_hits += 1
            if hit_5: top_5_hits += 1
            
            print(f"Retrieval Accuracy Hits: Top-1: {'YES' if hit_1 else 'NO'} | Top-3: {'YES' if hit_3 else 'NO'} | Top-5: {'YES' if hit_5 else 'NO'}")

        # 2. Run Full Multi-Agent Orchestrator Pipeline
        agent_res = orchestrator.run(test["query"], session_id=f"test_session_{idx}")
        print(f"Classified Query Type: {agent_res['query_type']}")
        print(f"Execution Engine: {agent_res['engine']}")
        print(f"Clarification Triggered: {agent_res['is_clarification']}")
        print(f"Agent Response Preview:\n  {agent_res['response'][:220]}...")
        if agent_res["citations"]:
            print(f"Citations attached: {len(agent_res['citations'])} sources cited.")
        print()

    # Summary Metrics
    print("=" * 70)
    print("RETRIEVAL ACCURACY REPORT SUMMARY")
    print("=" * 70)
    print(f"Total Test Queries Evaluated: {len(test_suite)}")
    print(f"In-Domain Ground Truth Queries: {evaluable_count}")
    print(f"Out-of-Domain / Clarification Queries: 1")
    print(f"Top-1 Accuracy: {top_1_hits}/{evaluable_count} ({top_1_hits / evaluable_count * 100:.1f}%)")
    print(f"Top-3 Accuracy: {top_3_hits}/{evaluable_count} ({top_3_hits / evaluable_count * 100:.1f}%)")
    print(f"Top-5 Accuracy: {top_5_hits}/{evaluable_count} ({top_5_hits / evaluable_count * 100:.1f}%)")
    print("=" * 70)


if __name__ == "__main__":
    setup_knowledge_base()
    run_evaluation()
