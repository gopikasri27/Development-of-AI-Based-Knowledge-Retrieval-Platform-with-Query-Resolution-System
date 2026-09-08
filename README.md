# AI-Based Knowledge Retrieval Platform with Query Resolution System

> ### 📌 Active Milestones: Infosys Internship – Milestone 1 & Milestone 2
> 
> *This repository contains the completed submissions for **Milestone 1** and **Milestone 2** of the Infosys Springboard Internship Project.*
> 
> - **Milestone 1**: System Architecture, RAG Architecture, Web Speech API, Data Specifications, and Frontend UI Prototype.
> - **Milestone 2**: Multi-Agent Query Resolution, Query Understanding Agent, Retrieval Agent, Response Generation Agent, Sequential Orchestration, and Automated Test Suite.

---

## 🎯 Project Overview

The **AI-Based Knowledge Retrieval Platform with Query Resolution System** is an enterprise-grade, full-stack knowledge retrieval solution designed to resolve user inquiries against internal documentation (PDF, DOCX, TXT, CSV). It combines **Retrieval-Augmented Generation (RAG)** with a **Multi-Agent Orchestration Pipeline** and **Multimodal Voice I/O (Web Speech API)** to deliver accurate, cited, and hallucination-free answers.

---

## 📂 Repository Structure

```text
rag/
├── README.md                                   # Root project documentation & submission index
├── .gitignore                                  # Git ignore rules
│
├── milestone-1/                                # Milestone 1 Deliverables
│   ├── architecture/
│   │   ├── System-Architecture.md              # Detailed component & layer breakdown
│   │   └── System-Architecture.png             # High-resolution architectural workflow diagram
│   ├── documentation/
│   │   ├── Data-Specifications.md              # Input, processing, retrieved, and output schemas
│   │   ├── Multi-Agent-Query-Resolution.md     # Multi-agent query resolution design & patterns
│   │   ├── RAG-Architecture.md                 # RAG theory, chunking, embeddings, workflow
│   │   └── Web-Speech-API.md                   # SpeechRecognition & SpeechSynthesis integration
│   └── frontend/
│       ├── index.html                          # Milestone 1 UI prototype with voice controls & dropzone
│       ├── script.js                           # Web Speech API, agent animation, and resolution logic
│       └── style.css                           # Modern dark glassmorphic styling & responsive layout
│
└── milestone-2/                                # Milestone 2 Deliverables
    ├── agents/
    │   ├── query_understanding_agent.py        # M2.1: Intent classification (factual/procedural/comp/ambig)
    │   ├── retrieval_agent.py                  # M2.2: Vector search & metadata ranking
    │   └── response_generation_agent.py        # M2.3: Grounded synthesis, citations & confidence
    ├── orchestration/
    │   └── agent_orchestrator.py               # M2.4: Sequential multi-agent pipeline coordinator
    ├── retrieval/
    │   ├── chunking.py                         # RecursiveCharacterTextSplitter with section metadata
    │   ├── embeddings.py                       # 384-d dense embedding generator (all-MiniLM-L6-v2)
    │   └── vector_store.py                     # ChromaDB HNSW vector store manager
    ├── knowledge_base/
    │   ├── hr_policy.txt                       # Domain 1: Corporate HR Policies
    │   └── product_manual.txt                  # Domain 2: CloudSync Pro Tech Manual
    ├── api/
    │   └── app.py                              # Flask REST API server (POST /api/query)
    ├── tests/
    │   ├── test_query_understanding.py         # Unit tests for M2.1
    │   ├── test_retrieval.py                   # Unit tests for M2.2
    │   ├── test_response_generation.py         # Unit tests for M2.3
    │   └── test_orchestration.py               # End-to-end integration tests for M2.4
    ├── documentation/
    │   └── Milestone-2.md                      # Comprehensive Milestone 2 technical report
    └── README.md                               # Milestone 2 quickstart guide
```

---

## 📑 Milestone 1 Deliverables & Documentation Index

All Milestone 1 deliverables are organized in the `milestone-1/` directory:

| Deliverable | File Path | Focus Areas |
| :--- | :--- | :--- |
| **1. RAG Architecture** | [`milestone-1/documentation/RAG-Architecture.md`](milestone-1/documentation/RAG-Architecture.md) | Ingestion, text preprocessing, chunking (500 chars / 50 overlap), `all-MiniLM-L6-v2` embeddings, ChromaDB HNSW vector indexing, cosine similarity retrieval, context injection, and LLM response generation. |
| **2. Multi-Agent Query Resolution Patterns** | [`milestone-1/documentation/Multi-Agent-Query-Resolution.md`](milestone-1/documentation/Multi-Agent-Query-Resolution.md) | Multi-agent architecture design: Memory Agent, Query Understanding Agent, Retrieval Agent, Clarification Guardrail Agent (< 0.50 cutoff), and Response Agent with inter-agent state contracts. |
| **3. Web Speech API Integration** | [`milestone-1/documentation/Web-Speech-API.md`](milestone-1/documentation/Web-Speech-API.md) | Browser-native `SpeechRecognition` voice-to-text input, `SpeechSynthesis` voice output, audio sanitization, browser compatibility matrix, and UI interaction workflow. |
| **4. System Architecture** | [`milestone-1/architecture/System-Architecture.md`](milestone-1/architecture/System-Architecture.md)<br>[`milestone-1/architecture/System-Architecture.png`](milestone-1/architecture/System-Architecture.png) | End-to-end multi-layer architecture specification and high-resolution graphical diagram covering Client UI, Input Layer, Query Processing, Query Resolution, RAG Pipeline, Vector Store, LLM, and Response Delivery. |
| **5. Data Specifications** | [`milestone-1/documentation/Data-Specifications.md`](milestone-1/documentation/Data-Specifications.md) | JSON schemas and specifications across 4 categories: Input Data (queries, uploads), Processing Data (metadata, chunks, 384-d vectors), Retrieved Data (matches, similarity), and Output Data (citations, telemetry). |
| **6. Frontend UI Prototype** | [`milestone-1/frontend/index.html`](milestone-1/frontend/index.html)<br>[`milestone-1/frontend/style.css`](milestone-1/frontend/style.css)<br>[`milestone-1/frontend/script.js`](milestone-1/frontend/script.js) | Standalone interactive UI prototype with drag-and-drop document upload, live agent execution pipeline bar, voice input/output controls, query suggestion chips, and citation cards. |

---

## 🤖 Milestone 2 – Multi-Agent Query Resolution & Response Generation

Milestone 2 implements the autonomous multi-agent backend engine coordinating query analysis, semantic retrieval, grounded synthesis, and execution telemetry:

```text
User Query
    ↓
Query Understanding Agent (M2.1)
    ↓
Retrieval Agent (M2.2)
    ↓
Response Generation Agent (M2.3)
    ↓
Final Response (Grounded Answer + Citations + Confidence Indicator)
```

### Milestone 2 Components

| Component | Implementation File | Key Capabilities |
| :--- | :--- | :--- |
| **M2.1 Query Understanding Agent** | [`milestone-2/agents/query_understanding_agent.py`](milestone-2/agents/query_understanding_agent.py) | Classifies query intent into `factual`, `procedural`, `comparative`, or `ambiguous` with confidence scoring and routing (`retrieval` vs `clarification`). |
| **M2.2 Retrieval Agent** | [`milestone-2/agents/retrieval_agent.py`](milestone-2/agents/retrieval_agent.py) | Performs vector search on ChromaDB, returns Top-$K$ chunks, ranks by cosine similarity, filters by confidence threshold ($\tau = 0.50$), and preserves document metadata. |
| **M2.3 Response Generation Agent** | [`milestone-2/agents/response_generation_agent.py`](milestone-2/agents/response_generation_agent.py) | Generates grounded answers with exact source citations, dynamic application confidence (`High`/`Medium`/`Low`), and anti-hallucination guardrails. |
| **M2.4 Multi-Agent Orchestration Layer** | [`milestone-2/orchestration/agent_orchestrator.py`](milestone-2/orchestration/agent_orchestrator.py) | Coordinates sequential agent execution, enforces standard data contracts, and handles boundary failures gracefully. |
| **Milestone 2 Technical Report** | [`milestone-2/documentation/Milestone-2.md`](milestone-2/documentation/Milestone-2.md) | Complete architectural specifications, data contracts, and evaluation results. |

### How to Run Milestone 2 Tests
```powershell
python -m unittest discover -s milestone-2/tests -p "test_*.py" -v
```

### How to Run Milestone 2 Backend API
```powershell
python milestone-2/api/app.py
```

---

## 🏛️ System Architecture Workflow

```text
User
 ↓
Web UI
 ↓
Text / Voice Input
 ↓
Query Processing (Query Understanding Agent)
 ↓
Query Resolution (Retrieval Agent & Vector Store)
 ↓
RAG Pipeline (ChromaDB + all-MiniLM-L6-v2)
 ↓
LLM Grounded Synthesis (Response Generation Agent)
 ↓
Response Delivery (Web UI + Speech Output)
```

![System Architecture Diagram](milestone-1/architecture/System-Architecture.png)

---

## 💻 Technologies Used & Proposed

| Component | Technology | Rationale / Purpose |
| :--- | :--- | :--- |
| **Frontend Core** | **HTML5, CSS3, Vanilla JavaScript** | Lightweight, framework-free client ensures fast page loads and simple deployment without node build pipelines. |
| **Voice Interface** | **W3C Web Speech API** | Native in-browser speech recognition and audio synthesis without external cloud API costs or latency. |
| **Backend API** | **Python 3.9+ & Flask** | Modular REST API layer facilitating asynchronous request dispatching and multi-agent coordination. |
| **Vector Store** | **ChromaDB (HNSW Cosine Space)** | Embedded, disk-persistent vector database supporting high-throughput nearest neighbor search. |
| **Embedding Model** | **`all-MiniLM-L6-v2` (Sentence-Transformers)** | 384-dimensional dense vectors; executes fast locally on CPU with zero external API fees. |
| **Text Splitter** | **`RecursiveCharacterTextSplitter`** | Splits documents hierarchically on paragraph and sentence boundaries with 500-char size and 50-char overlap. |
| **Language Model** | **Google Gemini 1.5 Flash** | High-throughput, context-window-efficient model for grounded response synthesis; includes offline local synthesis fallback. |
| **Metadata DB** | **SQLite3** | Lightweight relational storage for document records, chunk counts, and multi-turn session history. |

---

## 🚀 How to Run the Milestone 1 Frontend Prototype

The Milestone 1 prototype runs directly in any modern web browser without requiring a build step or server setup:

1. Open [`milestone-1/frontend/index.html`](milestone-1/frontend/index.html) in your browser (Google Chrome or Microsoft Edge recommended for full Web Speech API voice support).
2. **Test Suggested Queries**: Click any pre-configured query chips (*Annual Leave Policy*, *Installation Steps*, *Enterprise Edition Comparison*).
3. **Test Voice Input**: Click the **Microphone** button to speak your query.
4. **Test Voice Output**: Toggle the **Voice Output** switch to hear synthesized responses read aloud.
5. **Test Document Ingestion UI**: Drag and drop documents (PDF, DOCX, TXT) into the upload dropzone.
6. **Inspect Agent Pipeline**: Observe the multi-agent progress indicator visualizing real-time resolution stages (Memory → Query → Retrieval → Guardrail → Synthesis).

---

## 🔮 Future Milestone Roadmap

- **Milestone 1 (Completed)**: Architectural blueprint, RAG specifications, and interactive voice UI prototype.
- **Milestone 2 (Completed)**: Full multi-agent orchestration, intent understanding, vector retrieval, and grounded answer synthesis.
- **Milestone 3**: Advanced document parsing (scanned PDFs, OCR, tables), hybrid search (dense semantic + BM25 keyword), and full clarification loop.
- **Milestone 4**: Production deployment hardening, containerization, and enterprise monitoring.

