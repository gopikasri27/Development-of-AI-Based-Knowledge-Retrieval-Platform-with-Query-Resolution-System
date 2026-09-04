# AI-Based Knowledge Retrieval Platform with Query Resolution System

> ### 📌 Current Submission: Infosys Internship – Milestone 1
> 
> *This repository contains the submission for **Milestone 1** of the Infosys Springboard Internship Project.*
> 
> **Milestone 1 covers:**
> 1. **RAG Architecture**
> 2. **Multi-Agent Query Resolution Patterns**
> 3. **Web Speech API Integration**
> 4. **System Architecture**
> 5. **Data Specifications**
> 6. **Frontend UI Prototype**

---

## 🎯 Project Overview

The **AI-Based Knowledge Retrieval Platform with Query Resolution System** is an enterprise-grade, full-stack knowledge retrieval solution designed to resolve user inquiries against internal documentation (PDF, DOCX, TXT, CSV). It combines **Retrieval-Augmented Generation (RAG)** with a **Multi-Agent Orchestration Pipeline** and **Multimodal Voice I/O (Web Speech API)** to deliver accurate, cited, and hallucination-free answers.

---

## 📂 Repository Structure

The current `main` branch contains the complete **Milestone 1** deliverables:

```text
rag/
├── README.md                                   # Root project documentation & submission details
├── .gitignore                                  # Git ignore rules
└── milestone-1/                                # Milestone 1 Submission Directory
    ├── architecture/
    │   ├── System-Architecture.md              # Detailed component & layer breakdown
    │   └── System-Architecture.png             # High-resolution architectural workflow diagram
    │
    ├── documentation/
    │   ├── Data-Specifications.md              # Input, processing, retrieved, and output schemas
    │   ├── Multi-Agent-Query-Resolution.md     # 5-Agent query resolution architecture & communication
    │   ├── RAG-Architecture.md                 # RAG theory, chunking, embeddings, workflow
    │   └── Web-Speech-API.md                   # SpeechRecognition & SpeechSynthesis integration
    │
    └── frontend/
        ├── index.html                          # Milestone 1 UI prototype with voice controls & dropzone
        ├── script.js                           # Web Speech API, agent animation, and resolution logic
        └── style.css                           # Modern dark glassmorphic styling & responsive layout
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

## 🏛️ System Architecture Workflow

```text
User
 ↓
Web UI
 ↓
Text / Voice Input
 ↓
Query Processing
 ↓
Query Resolution
 ↓
RAG Pipeline
 ↓
Knowledge Base / Vector Store
 ↓
LLM
 ↓
Response
 ↓
Web UI
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

- **Milestone 2**: Full multi-agent orchestration implementation, dynamic query decomposition into parallel sub-searches, and iterative re-ranking.
- **Milestone 3**: Advanced document parsing (scanned PDFs, OCR, tables), hybrid search (dense semantic + BM25 keyword), and citation highlighting.
- **Milestone 4**: Production deployment hardening, comprehensive unit/integration test suites, and Docker containerization.
