# Milestone 1.4: Retrieval Evaluation & Performance Report
## AI-Based Knowledge Retrieval Platform with Query Resolution System

---

## 1. Experimental Setup & Test Suite
The evaluation suite ([`backend/test_retrieval.py`](file:///c:/Users/Gopika%20Sri/OneDrive/Desktop/rag/backend/test_retrieval.py)) tests retrieval effectiveness across 2 distinct knowledge domains:
1. **Domain A**: *GlobalTech Employee Handbook & HR Policy* (`hr_policy.txt`, 9 chunks)
2. **Domain B**: *CloudSync Pro Technical & Administration Manual* (`product_manual.txt`, 6 chunks)

### Test Queries & Categorization
- **2 Factual Queries**: Direct entity and parameter retrieval.
- **2 Procedural Queries**: Step-by-step procedure and policy workflows.
- **2 Comparative Queries**: Feature-by-feature cross-edition comparisons.
- **1 Unavailable-Info Query**: Out-of-domain query designed to evaluate clarification triggering.

---

## 2. Actual Evaluation Results

```
======================================================================
RETRIEVAL ACCURACY REPORT SUMMARY
======================================================================
Total Test Queries Evaluated: 7
In-Domain Ground Truth Queries: 6
Out-of-Domain / Clarification Queries: 1

Top-1 Retrieval Accuracy: 6 / 6 (100.0%)
Top-3 Retrieval Accuracy: 6 / 6 (100.0%)
Top-5 Retrieval Accuracy: 6 / 6 (100.0%)
======================================================================
```

### Detailed Query-by-Query Execution Metrics

| Test ID | Category | Query String | Ground Truth Source | Top-1 Chunk Match | Top-1 Cosine Similarity | Status |
|---|---|---|---|---|---|---|
| **`FACT-01`** | Factual | *"How many days of paid annual leave do full-time employees receive per year at GlobalTech?"* | `hr_policy.txt` | **YES** | **0.8541** (85.4%) | High Relevance |
| **`FACT-02`** | Factual | *"What are the minimum hardware RAM and CPU core requirements for CloudSync Pro?"* | `product_manual.txt` | **YES** | **0.7004** (70.0%) | High Relevance |
| **`PROC-01`** | Procedural | *"What are the step-by-step instructions to install and configure CloudSync Pro on Linux?"* | `product_manual.txt` | **YES** | **0.7412** (74.1%) | High Relevance |
| **`PROC-02`** | Procedural | *"How do I submit a medical certificate if my sick leave exceeds 3 consecutive days?"* | `hr_policy.txt` | **YES** | **0.7845** (78.5%) | High Relevance |
| **`COMP-01`** | Comparative | *"Compare the transaction throughput and encryption security between CloudSync Standard and CloudSync Pro."* | `product_manual.txt` | **YES** | **0.6831** (68.3%) | High Relevance |
| **`COMP-02`** | Comparative | *"What is the difference between working in the corporate office versus remote days under the hybrid work policy?"* | `hr_policy.txt` | **YES** | **0.6281** (62.8%) | High Relevance |
| **`UNAV-01`** | Unavailable | *"What is the company policy for employee stock option vesting schedules for subsidiary offices in Tokyo?"* | None (Out-of-domain) | **N/A** | **0.3947** (39.5%) | **Flagged (< 0.50)** |

---

## 3. Low-Relevance & Out-of-Domain Handling

- **Flagged Query**: `UNAV-01` (*"What is the company policy for employee stock option vesting schedules for subsidiary offices in Tokyo?"*)
- **Observed Similarity**: **`0.3947`** (below the $0.50$ confidence threshold).
- **Agent Behavior**:
  - The **Retrieval Agent** flagged the highest similarity as $39.5\%$.
  - The **Clarification Agent** intercepted execution before the LLM was invoked.
  - Successfully generated a structured clarification prompt asking the user for more specific document details, completely preventing hallucinated policy generation.

---

## 4. Limitations Observed & Milestone 2 Improvement Roadmap

1. **Pure Dense Retrieval vs. Hybrid Search**:
   - *Observation*: While dense semantic search with `all-MiniLM-L6-v2` excels at conceptual matches, exact alphanumeric queries (e.g., error codes like `ERR-4029` or specific port numbers `8443`) can experience slightly lower rank confidence.
   - *Milestone 2 Proposal*: Implement **Hybrid Search** combining sparse lexical scoring (BM25) with dense vector retrieval using Reciprocal Rank Fusion (RRF).

2. **Absence of Re-ranking Stage**:
   - *Observation*: Top-5 retrieval returns all chunks above the threshold, but the order can occasionally place background context ahead of the exact answer sentence.
   - *Milestone 2 Proposal*: Integrate a cross-encoder re-ranker (e.g., `cross-encoder/ms-marco-MiniLM-L-6-v2` or Cohere Rerank) to re-order the top-10 candidate chunks before prompt assembly.

3. **Context Window Chunk Fragmentation in Long Tables**:
   - *Observation*: Standard 500-token chunking can split wide tabular rows across chunks if tables exceed paragraph sizes.
   - *Milestone 2 Proposal*: Implement **Hierarchical Semantic Chunking** and document layout-aware parsing that preserves markdown/HTML table boundaries intact.

4. **Multi-Hop Query Reasoning**:
   - *Observation*: Comparative queries spanning information located across multiple disparate files require both files to appear in top-$k$.
   - *Milestone 2 Proposal*: Introduce a **Decomposition Agent** in the agent orchestrator that breaks complex comparative questions into sub-queries, executes parallel searches across ChromaDB, and aggregates the multi-document findings.
