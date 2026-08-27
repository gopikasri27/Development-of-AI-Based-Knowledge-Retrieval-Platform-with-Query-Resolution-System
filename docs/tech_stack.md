# Milestone 1.3: Technology Stack & Component Justifications

A detailed breakdown of all libraries, models, databases, and frameworks utilized in the **AutoRAG Multi-Agent Platform**:

| Layer / Component | Technology / Library | Version | Selection Justification |
|---|---|---|---|
| **Backend Web Framework** | `Flask` + `Flask-CORS` | `^3.0.0` | Lightweight, fast Python WSGI framework ideal for hosting clean REST endpoints and serving SPA static assets without framework overhead. |
| **Vector Store** | `ChromaDB` | `^1.5.0` | Local, persistent embedded vector database that runs in-process with zero external server dependencies and native HNSW cosine similarity search. |
| **Dense Embeddings** | `sentence-transformers` (`all-MiniLM-L6-v2`) | `^6.0.0` | High-speed, local 384-dimensional embedding model running on CPU with zero API costs, low latency, and strong semantic retrieval benchmarks. |
| **Text Chunking** | `langchain-text-splitters` | `^1.1.0` | Provides recursive character splitting that prioritizes semantic paragraph and sentence boundaries while preserving overlap margins. |
| **PDF Extraction** | `pypdf` | `^6.16.0` | Pure-Python PDF parsing library capable of extracting page-level text streams without external C-binary dependencies. |
| **DOCX Extraction** | `python-docx` | `^1.2.0` | Robust library for extracting structured paragraphs and tabular rows from Microsoft Word `.docx` files. |
| **CSV & Data Processing** | `pandas` | `^2.2.0` | Industry-standard tabular data manipulation library used to transform CSV rows into descriptive semantic statements. |
| **Generative LLM** | `Google Gemini API` (`gemini-1.5-flash`) | `^0.8.6` | State-of-the-art multimodal LLM offering low-latency, free-tier access, and large context windows for grounded RAG generation. |
| **Metadata & History DB** | `SQLite3` | Built-in | Zero-configuration SQL database for storing document indexing metadata and multi-turn conversational chat logs. |
| **Voice Input (STT)** | `Web Speech API` (`SpeechRecognition`) | Native Browser | Client-side real-time speech-to-text with zero latency, zero backend transcription compute costs, and native browser integration. |
| **Voice Output (TTS)** | `Web Speech API` (`SpeechSynthesis`) | Native Browser | In-browser speech synthesis for natural voice readouts with speed and pitch control without third-party audio API fees. |
| **Frontend UI** | `HTML5`, `Vanilla CSS3`, `Modern ES6+ JS` | Native Standards | Ultra-fast, framework-free single page application featuring glassmorphism aesthetics, responsive layouts, and audio wave animations. |
| **Environment Config** | `python-dotenv` | `^1.0.0` | Secure environment variable management for API keys and configuration across development and production environments. |
