# AI-Based Knowledge Retrieval Platform with Query Resolution System
## Multi-Agent RAG with Voice Input & Output (Milestone 1)

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/backend-Flask-green.svg)](https://flask.palletsprojects.com/)
[![ChromaDB](https://img.shields.io/badge/vectorstore-ChromaDB-purple.svg)](https://www.trychroma.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

An enterprise-grade, full-stack **Multi-Agent Retrieval-Augmented Generation (RAG)** platform designed for intelligent document search, question resolution, and multimodal interaction (voice-to-text input and text-to-speech output).

---

## 📑 Project Documentation Index

Detailed engineering documentation and evaluation reports are available in the [`docs/`](file:///c:/Users/Gopika%20Sri/OneDrive/Desktop/rag/docs) directory:

- 📖 **[Research Notes & RAG Foundations](file:///c:/Users/Gopika%20Sri/OneDrive/Desktop/rag/docs/research_notes.md)** (`docs/research_notes.md`) — RAG theory, 5-agent query resolution pattern, chunking strategy rationale, embedding selection, and Web Speech API mechanics.
- 📐 **[System Architecture & Data Specifications](file:///c:/Users/Gopika%20Sri/OneDrive/Desktop/rag/docs/architecture.md)** (`docs/architecture.md`) — Complete Mermaid architecture diagram, data flow walkthrough, and code schemas.
- 🛠️ **[Technology Stack](file:///c:/Users/Gopika%20Sri/OneDrive/Desktop/rag/docs/tech_stack.md)** (`docs/tech_stack.md`) — Comprehensive technology breakdown and justification table.
- 📊 **[Retrieval Evaluation & Performance Report](file:///c:/Users/Gopika%20Sri/OneDrive/Desktop/rag/docs/retrieval_evaluation.md)** (`docs/retrieval_evaluation.md`) — Validation results, Top-1/3/5 accuracy metrics (100%), out-of-domain detection, and Milestone 2 roadmap.

---

## 🏛️ Architecture Overview

The system employs a sequential **5-Agent Collaborative Query Resolution Pipeline**:

```
+-----------------------------------------------------------------------------------+
|                            User Interface & Voice I/O                             |
|       (Web Speech Recognition Input  •  Web Speech Synthesis Voice Output)        |
+-----------------------------------------------------------------------------------+
                                         │  POST /query
                                         ▼
+───────────────────────────────────────────────────────────────────────────────────+
|                           Multi-Agent Orchestrator                                |
|                                                                                   |
|  1. Memory Agent ──► 2. Query Agent ──► 3. Retrieval Agent ──► 4. Clarification   |
|     (Session Hist)      (Classify Intent)   (ChromaDB Top-5)      (Score < 0.50?) |
|                                                                         │         |
|                                                     ┌───────────────────┴──────┐  |
|                                                     ▼                          ▼  |
|                                            (Clarification Prompts)  5. Response   |
|                                                                        (Gemini)   |
+───────────────────────────────────────────────────────────────────────────────────+
                                         │  Grounded Response + Sources
                                         ▼
+───────────────────────────────────────────────────────────────────────────────────+
|                        Persistent Storage & Vector Engine                         |
|     ChromaDB (HNSW Cosine Vector Store)  •  SQLite (Document Metadata & Logs)     |
+───────────────────────────────────────────────────────────────────────────────────+
```

For complete architecture details and schemas, see **[docs/architecture.md](file:///c:/Users/Gopika%20Sri/OneDrive/Desktop/rag/docs/architecture.md)**.

---

## 📁 Folder Structure

```
rag/
├── backend/
│   ├── app.py                      # Flask REST API & static asset server
│   ├── requirements.txt            # Python dependencies
│   ├── test_retrieval.py           # Evaluation test suite (Top-1/3/5 accuracy)
│   ├── .env.example                # Environment variable configuration template
│   ├── rag_metadata.db             # SQLite document and session persistence database
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── query_agent.py          # Query Understanding Agent (Intent/Type classifier)
│   │   ├── retrieval_agent.py      # ChromaDB Semantic Retrieval Agent
│   │   ├── clarification_agent.py  # Confidence & Ambiguity Guardrail Agent
│   │   ├── response_agent.py       # Gemini API / Local Synthesis Response Agent
│   │   ├── memory_agent.py         # Multi-turn Session Memory Agent
│   │   └── orchestrator.py         # Sequential Pipeline Coordinator
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── extract_text.py         # PDF, DOCX, TXT, CSV text extraction & cleaning
│   │   ├── chunking.py             # RecursiveCharacterTextSplitter with overlap
│   │   ├── embeddings.py           # Sentence-Transformers & ChromaDB interface
│   │   └── db.py                   # SQLite helper functions
│   ├── sample_data/
│   │   ├── hr_policy.txt           # Sample Domain 1: GlobalTech HR Policies
│   │   └── product_manual.txt      # Sample Domain 2: CloudSync Pro Technical Manual
│   ├── uploads/                    # Ingested user documents
│   └── vectorstore/                # ChromaDB local persistent vector storage
├── frontend/
│   ├── index.html                  # Single-page UI with dropzone, chat, & pipeline bar
│   ├── style.css                   # Modern dark glassmorphic styling & mic animations
│   └── script.js                   # Client logic, Web Speech API, & citation cards
├── docs/
│   ├── research_notes.md           # Milestone 1.1: Theoretical & architectural research
│   ├── architecture.md             # Milestone 1.2: Architecture diagrams & schemas
│   ├── tech_stack.md               # Milestone 1.3: Technology stack table
│   └── retrieval_evaluation.md     # Milestone 1.4: Evaluation metrics & results
└── README.md
```

---

## ⚡ Setup & Installation

### 1. Prerequisites
- Python 3.9, 3.10, 3.11, or 3.12 installed
- Google Chrome or Microsoft Edge (for native Web Speech API voice support)

### 2. Clone and Install Dependencies
Navigate to the project root and install the required dependencies:

```bash
pip install -r backend/requirements.txt
```

### 3. Configure Environment Variables
Copy `backend/.env.example` to `backend/.env`:

```bash
cp backend/.env.example backend/.env
```

Edit `backend/.env` to configure your settings:
```env
# Google Gemini API Key (Optional: system uses local synthesis if omitted)
GEMINI_API_KEY=your_gemini_api_key_here

# Model Selection
GEMINI_MODEL=gemini-1.5-flash
EMBEDDING_MODEL=all-MiniLM-L6-v2

# Server Port
PORT=5000
FLASK_ENV=development
```

---

## 🧪 How to Test & Evaluate

### Option A: Run the Automated Retrieval Evaluation Suite
Run the test suite to evaluate Top-1, Top-3, and Top-5 accuracy across factual, procedural, comparative, and unavailable-information queries:

```bash
python backend/test_retrieval.py
```

**Evaluation Results Highlights:**
- **Top-1 Retrieval Accuracy**: `100.0%` (6/6)
- **Top-3 Retrieval Accuracy**: `100.0%` (6/6)
- **Top-5 Retrieval Accuracy**: `100.0%` (6/6)
- **Low-Confidence Query Flagged**: `39.5%` similarity (< 0.50 threshold) triggered the Clarification Agent.

---

### Option B: Run the Interactive Web Application

1. **Start the Flask Backend**:
   ```bash
   python backend/app.py
   ```
2. **Access the Web Interface**:
   Open **`http://localhost:5000`** in your browser.
3. **Ingest Documents**:
   - Drag & drop `.pdf`, `.docx`, `.txt`, or `.csv` files into the left sidebar.
   - The platform will extract text, chunk it (500 tokens, 50 overlap), generate dense embeddings, and index into ChromaDB.
4. **Interact via Text or Voice**:
   - Type queries in the input box, or click the **Microphone** button to speak your question aloud.
   - Click sample query chips to test factual, procedural, and comparative queries.
   - Inspect grounded source citation cards with match percentages.
   - Toggle **Voice Output** in the top bar to hear generated answers read aloud.

---

## 📡 REST API Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/upload` | Ingest and index a document (`multipart/form-data`) |
| `POST` | `/query` | Execute multi-agent RAG workflow on user question |
| `GET` | `/health` | Health status, total chunks, and document count |
| `GET` | `/documents` | List all indexed documents in the knowledge base |
| `GET` | `/history/<session_id>` | Fetch conversation history for a session |
| `POST` | `/reset` | Clear all indexed vectors from ChromaDB |
