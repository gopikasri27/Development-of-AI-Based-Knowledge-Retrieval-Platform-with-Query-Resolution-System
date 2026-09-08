# Milestone 2: Multi-Agent Query Resolution & Response Generation

## AI-Based Knowledge Retrieval Platform with Query Resolution System

---

## 1. Executive Summary

**Milestone 2** establishes the core intelligence layer of the *AI-Based Knowledge Retrieval Platform with Query Resolution System*. Building directly upon the architectural foundation and vector database design established in Milestone 1, Milestone 2 implements an end-to-end, modular, multi-agent query resolution pipeline.

The architecture decomposes complex query resolution into three specialized agents coordinated by a centralized sequential orchestration layer:
1. **Query Understanding Agent (M2.1)**: Parses incoming queries, determines semantic intent (`factual`, `procedural`, `comparative`, `ambiguous`), computes confidence, and routes execution.
2. **Retrieval Agent (M2.2)**: Performs dense semantic vector search against ChromaDB using `all-MiniLM-L6-v2` embeddings, retrieves Top-$K$ relevant chunks, enforces confidence score thresholds, and preserves full document metadata.
3. **Response Generation Agent (M2.3)**: Synthesizes grounded, natural language answers strictly bound to retrieved context, attributes exact source citations, computes dynamic application confidence, and applies anti-hallucination guardrails.
4. **Multi-Agent Orchestration Layer (M2.4)**: Sequentially coordinates the agents, handles failures at each stage gracefully, and returns unified JSON payloads with step-by-step execution telemetry.

---

## 2. Multi-Agent System Architecture

```text
User Query (Text / Voice Transcription)
                    │
                    ▼
┌────────────────────────────────────────────────────────┐
│ M2.1 — Query Understanding Agent                       │
│ - Intent Classification: factual | procedural |       │
│   comparative | ambiguous                              │
│ - Confidence Score: 0.0 – 1.0                          │
│ - Routing Target: 'retrieval' or 'clarification'       │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│ M2.2 — Retrieval Agent                                 │
│ - Dense Vector Search (ChromaDB + all-MiniLM-L6-v2)    │
│ - Configurable Top-K Retrieval (Default K=5)           │
│ - Cosine Similarity Scoring & Ranking                  │
│ - Low-Confidence Cutoff Threshold Filtering (τ = 0.50) │
│ - Rich Metadata Preservation (doc, page, section, id)  │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│ M2.3 — Response Generation Agent                       │
│ - Grounded Prompt Ingestion & Evidence Binding         │
│ - Anti-Hallucination Guardrail                         │
│ - Source Attribution & Citation Mapping                │
│ - Application Confidence Metric (High / Medium / Low)  │
│ - Dual Engine: Gemini API + Offline Local Synthesis   │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│ M2.4 — Multi-Agent Orchestration Layer                 │
│ - Sequential Pipeline Execution                        │
│ - Step Telemetry & Duration Tracking                   │
│ - Boundary Exception Recovery & Fallbacks              │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
                     Final Unified JSON Response
```

---

## 3. Detailed Component Breakdown

### 3.1 M2.1: Query Understanding Agent

#### Purpose & Responsibilities
The Query Understanding Agent analyzes every incoming query before any database or LLM operation. It prevents inefficient, ambiguous, or out-of-domain searches by categorizing intent and deciding the appropriate downstream routing.

#### Classification Categories & Rules
1. **`factual`**: Direct lookups of specific policies, allowances, dates, limits, definitions, or settings.
   - *Example Queries*: `"How many days of paid annual leave do full-time employees receive?"`, `"What are the system requirements for CloudSync Pro?"`
   - *Routing*: `"retrieval"`
2. **`procedural`**: Step-by-step instructions, deployment guides, troubleshooting sequences, or administrative workflows.
   - *Example Queries*: `"How do I submit a medical certificate for sick leave?"`, `"What are the step-by-step instructions to install CloudSync Pro on Linux?"`
   - *Routing*: `"retrieval"`
3. **`comparative`**: Explicit comparisons between tiers, editions, algorithms, or configurations.
   - *Example Queries*: `"Compare CloudSync Standard vs CloudSync Pro edition throughput and encryption"`, `"Difference between standard and pro tier"`
   - *Routing*: `"retrieval"`
4. **`ambiguous`**: Vague, fragmented, underspecified, or out-of-domain inquiries lacking actionable entities.
   - *Example Queries*: `"help"`, `"tell me something"`, `"policy"`, `"what can you do"`, `"stuff and things"`
   - *Routing*: `"clarification"` (marks query for clarification handling without triggering ungrounded retrieval)

#### Structured Output Schema
```json
{
  "query": "What are the system requirements for CloudSync Pro?",
  "query_type": "factual",
  "classification_confidence": 0.95,
  "routing": "retrieval"
}
```

---

### 3.2 M2.2: Retrieval Agent

#### Purpose & Responsibilities
The Retrieval Agent interfaces with the vector database to fetch relevant knowledge chunks for the user's question, preserving contextual provenance.

#### Retrieval Pipeline Mechanics
1. **Embedding**: Transforms incoming query text into a 384-dimensional dense vector using `sentence-transformers/all-MiniLM-L6-v2`.
2. **Nearest-Neighbor Search**: Executes cosine similarity search over ChromaDB HNSW indexing.
3. **Relevance Ranking**: Computes cosine similarity score:
   $$\text{Similarity Score} = 1.0 - \text{Cosine Distance}$$
   Sorts results in descending order of relevance.
4. **Low-Confidence Filtering**: Filters out chunks whose similarity score falls below the configurable threshold ($\tau = 0.50$).
5. **Metadata Preservation**: Retains document name, page number, section heading, chunk ID, and character count.

#### Structured Output Schema
```json
{
  "query": "What are the system requirements for CloudSync Pro?",
  "results": [
    {
      "content": "[1. System Requirements and Architecture]\nCloudSync Pro is an enterprise distributed data synchronization platform. It requires a 64-bit Linux kernel (Ubuntu 22.04 LTS or RHEL 9), a minimum of 4 CPU cores, 16 GB RAM, and 100 GB NVMe SSD storage.",
      "document_name": "product_manual.txt",
      "page": 1,
      "section": "1. System Requirements and Architecture",
      "chunk_id": "product_manual.txt_chunk_0",
      "relevance_score": 0.8845
    }
  ],
  "result_count": 1
}
```

---

### 3.3 M2.3: Response Generation Agent

#### Purpose & Responsibilities
The Response Generation Agent synthesizes verified, fluent answers strictly backed by the retrieved evidence. It eliminates hallucinations by adhering to grounding constraints.

#### Grounding & Generation Engine
- **LLM Engine**: Google Gemini API (`gemini-1.5-flash`) via `GEMINI_API_KEY`.
- **Local Fallback Engine**: Deterministic, structured offline extractor that formats grounded answers directly from verified chunk content when API keys are unconfigured or offline.
- **Application Confidence Formula**:
  - $\text{Score} \ge 0.75 \rightarrow \textbf{High}$ confidence
  - $0.50 \le \text{Score} < 0.75 \rightarrow \textbf{Medium}$ confidence
  - $\text{Score} < 0.50 \text{ or empty} \rightarrow \textbf{Low}$ confidence
- **Insufficient Context Handling**: If no chunks exceed threshold or query is ambiguous, returns:
  `"Sufficient information was not found in the knowledge base to provide a reliable answer."`

#### Structured Output Schema
```json
{
  "answer": "According to the product manual (1. System Requirements and Architecture), CloudSync Pro requires a 64-bit Linux kernel (Ubuntu 22.04 LTS or RHEL 9), a minimum of 4 CPU cores, 16 GB RAM, and 100 GB NVMe SSD storage with PostgreSQL 15+.",
  "sources": [
    {
      "document_name": "product_manual.txt",
      "page": 1,
      "chunk_id": "product_manual.txt_chunk_0"
    }
  ],
  "confidence": {
    "score": 0.8845,
    "label": "High"
  }
}
```

---

### 3.4 M2.4: Multi-Agent Orchestration Layer

#### Purpose & Responsibilities
The Orchestrator coordinates all three agents sequentially, passes standard JSON contracts between stages, manages timeouts and errors, and produces unified output.

#### Resilience & Error Handling
- **Classification Failure**: Falls back to safe default factual routing without crashing.
- **Retrieval Failure**: Returns safe empty result structure with Low confidence.
- **Generation Failure**: Returns standard safe insufficient information message without exposing internal exceptions.

#### Standard Response Contract
```json
{
  "query": "How many days of paid annual leave do full-time employees get?",
  "query_type": "factual",
  "classification_confidence": 0.95,
  "answer": "According to the HR policy, all full-time employees at GlobalTech are entitled to 20 days of paid Annual Leave per calendar year. Annual leave accrues on the first day of each month at a rate of 1.66 days.",
  "sources": [
    {
      "document_name": "hr_policy.txt",
      "page": 1,
      "chunk_id": "hr_policy.txt_chunk_0"
    }
  ],
  "confidence": {
    "score": 0.885,
    "label": "High"
  },
  "telemetry": {
    "pipeline_steps": [
      {
        "step": 1,
        "agent": "Query Understanding Agent",
        "status": "success",
        "duration_ms": 1.25,
        "details": {
          "query_type": "factual",
          "classification_confidence": 0.95,
          "routing": "retrieval"
        }
      },
      {
        "step": 2,
        "agent": "Retrieval Agent",
        "status": "success",
        "duration_ms": 12.40,
        "details": {
          "chunks_retrieved": 3,
          "top_score": 0.885
        }
      },
      {
        "step": 3,
        "agent": "Response Generation Agent",
        "status": "success",
        "duration_ms": 2.10,
        "details": {
          "confidence_score": 0.885,
          "confidence_label": "High",
          "sources_count": 1
        }
      }
    ],
    "total_duration_ms": 15.75
  }
}
```

---

## 4. Knowledge Domains Tested

Milestone 2 is verified using the two knowledge domains from Milestone 1:

| Domain | Source Document | Key Covered Topics |
| :--- | :--- | :--- |
| **Domain 1: Corporate HR Policies** | [`milestone-2/knowledge_base/hr_policy.txt`](file:///c:/Users/Gopika%20Sri/OneDrive/Desktop/rag/milestone-2/knowledge_base/hr_policy.txt) | Annual leave (20 days), sick leave (10 days, medical cert > 3 days), 3-2 hybrid work model, BlueShield health insurance, wellness allowance ($600), promotion cycles, travel expense per diems. |
| **Domain 2: Technical Product Documentation** | [`milestone-2/knowledge_base/product_manual.txt`](file:///c:/Users/Gopika%20Sri/OneDrive/Desktop/rag/milestone-2/knowledge_base/product_manual.txt) | Linux requirements (Ubuntu/RHEL, 4 cores, 16GB RAM), step-by-step `install.sh` setup, Standard vs Pro edition comparison (5k vs 50k TPS, AES-128 vs AES-256), REST API Bearer token auth, sync error troubleshooting. |

---

## 5. Verification & Test Summary

All 27 automated tests executed via Python's standard `unittest` framework:

```text
test_ambiguous_queries (test_query_understanding.TestQueryUnderstandingAgent) ... ok
test_comparative_query_tech_domain (test_query_understanding.TestQueryUnderstandingAgent) ... ok
test_empty_and_whitespace_query (test_query_understanding.TestQueryUnderstandingAgent) ... ok
test_factual_query_hr_domain (test_query_understanding.TestQueryUnderstandingAgent) ... ok
test_factual_query_tech_domain (test_query_understanding.TestQueryUnderstandingAgent) ... ok
test_procedural_query_hr_domain (test_query_understanding.TestQueryUnderstandingAgent) ... ok
test_procedural_query_tech_domain (test_query_understanding.TestQueryUnderstandingAgent) ... ok
test_grounded_comparative_response (test_response_generation.TestResponseGenerationAgent) ... ok
test_grounded_factual_response (test_response_generation.TestResponseGenerationAgent) ... ok
test_grounded_procedural_response (test_response_generation.TestResponseGenerationAgent) ... ok
test_insufficient_information_empty_results (test_response_generation.TestResponseGenerationAgent) ... ok
test_low_confidence_retrieval_guardrail (test_response_generation.TestResponseGenerationAgent) ... ok
test_metadata_preservation (test_retrieval.TestRetrievalAgent) ... ok
test_relevance_ranking (test_retrieval.TestRetrievalAgent) ... ok
test_semantic_search_comparative (test_retrieval.TestRetrievalAgent) ... ok
test_semantic_search_hr_domain_factual (test_retrieval.TestRetrievalAgent) ... ok
test_semantic_search_tech_domain_procedural (test_retrieval.TestRetrievalAgent) ... ok
test_top_k_parameter (test_retrieval.TestRetrievalAgent) ... ok
test_unavailable_out_of_domain_query (test_retrieval.TestRetrievalAgent) ... ok
test_e2e_ambiguous_query_handling (test_orchestration.TestMultiAgentOrchestration) ... ok
test_e2e_comparative_tech_domain (test_orchestration.TestMultiAgentOrchestration) ... ok
test_e2e_factual_hr_domain (test_orchestration.TestMultiAgentOrchestration) ... ok
test_e2e_procedural_tech_domain (test_orchestration.TestMultiAgentOrchestration) ... ok
test_e2e_unavailable_out_of_domain_query (test_orchestration.TestMultiAgentOrchestration) ... ok
test_orchestration_classification_failure_resilience (test_orchestration.TestMultiAgentOrchestration) ... ok
test_orchestration_generation_failure_resilience (test_orchestration.TestMultiAgentOrchestration) ... ok
test_orchestration_retrieval_failure_resilience (test_orchestration.TestMultiAgentOrchestration) ... ok

----------------------------------------------------------------------
Ran 27 tests in 9.373s

OK
```
