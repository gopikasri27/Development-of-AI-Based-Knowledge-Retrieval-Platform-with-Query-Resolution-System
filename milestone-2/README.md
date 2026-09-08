# Milestone 2: Multi-Agent Query Resolution & Response Generation

## AI-Based Knowledge Retrieval Platform with Query Resolution System

> ### 📌 Current Submission: Infosys Internship – Milestone 2
>
> *This folder contains the complete implementation, tests, and documentation for **Milestone 2** of the Infosys Springboard Internship Project.*

---

## 🎯 Overview

Milestone 2 delivers the **Multi-Agent Query Resolution and Response Generation System**. It coordinates three specialized AI agents via a sequential multi-agent orchestrator:

1. **Query Understanding Agent (`agents/query_understanding_agent.py`)**: Categorizes queries into `factual`, `procedural`, `comparative`, or `ambiguous` with confidence scores and routing.
2. **Retrieval Agent (`agents/retrieval_agent.py`)**: Performs dense semantic vector search via ChromaDB and `all-MiniLM-L6-v2`, retrieves Top-$K$ relevant chunks, enforces confidence threshold filtering ($\tau = 0.50$), and preserves document metadata.
3. **Response Generation Agent (`agents/response_generation_agent.py`)**: Synthesizes verified grounded responses using retrieved context, attributes exact source citations, computes application confidence, and applies anti-hallucination guardrails.
4. **Multi-Agent Orchestration Layer (`orchestration/agent_orchestrator.py`)**: Coordinates the sequential execution pipeline, manages boundary error fallbacks, and captures pipeline telemetry.

---

## 📂 Directory Structure

```text
milestone-2/
├── agents/
│   ├── __init__.py
│   ├── query_understanding_agent.py    # M2.1: Intent classification & routing
│   ├── retrieval_agent.py              # M2.2: Vector search & metadata ranking
│   └── response_generation_agent.py    # M2.3: Grounded synthesis & citations
│
├── orchestration/
│   ├── __init__.py
│   └── agent_orchestrator.py           # M2.4: Sequential pipeline coordinator
│
├── retrieval/
│   ├── __init__.py
│   ├── chunking.py                     # Recursive character text chunking
│   ├── embeddings.py                   # 384-d dense embedding generator
│   └── vector_store.py                 # ChromaDB HNSW vector store manager
│
├── knowledge_base/
│   ├── hr_policy.txt                   # Domain 1: Corporate HR Policies
│   └── product_manual.txt              # Domain 2: CloudSync Pro Tech Manual
│
├── api/
│   ├── __init__.py
│   └── app.py                          # Flask REST API server (POST /api/query)
│
├── tests/
│   ├── __init__.py
│   ├── test_query_understanding.py     # Unit tests for M2.1
│   ├── test_retrieval.py               # Unit tests for M2.2
│   ├── test_response_generation.py     # Unit tests for M2.3
│   └── test_orchestration.py           # End-to-end integration tests for M2.4
│
├── documentation/
│   └── Milestone-2.md                  # Comprehensive M2 architecture report
│
└── README.md                           # Milestone 2 quickstart guide
```

---

## 🚀 How to Run and Test

### 1. Run the Test Suite
Execute the 27 unit and integration tests across all components:
```powershell
python -m unittest discover -s milestone-2/tests -p "test_*.py" -v
```

### 2. Start the Milestone 2 REST API
```powershell
python milestone-2/api/app.py
```

### 3. Query the Multi-Agent Endpoint
```powershell
curl -X POST http://localhost:5000/api/query `
  -H "Content-Type: application/json" `
  -d '{"query": "How many days of annual leave do employees receive?"}'
```

---

## 📑 Documentation Links
- Detailed Milestone 2 Architecture & Specifications: [`milestone-2/documentation/Milestone-2.md`](documentation/Milestone-2.md)
- Milestone 1 Foundation & Deliverables: [`milestone-1/`](../milestone-1/)
