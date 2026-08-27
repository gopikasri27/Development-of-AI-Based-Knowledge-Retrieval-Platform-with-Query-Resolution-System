# Milestone 1.1: Research Notes & Theoretical Foundations
## AI-Based Knowledge Retrieval Platform with Query Resolution System

---

## 1. What is RAG (Retrieval-Augmented Generation)?

Retrieval-Augmented Generation (RAG) is an architectural pattern in modern generative AI that combines information retrieval systems with large language models (LLMs). Rather than relying solely on the static, parameterized knowledge acquired during pre-training—which is prone to hallucinations, knowledge cutoffs, and lack of domain specificity—RAG dynamically injects relevant context from private or real-time knowledge bases into the model prompt at query time.

```
+-------------------+        +----------------------+        +-----------------------+
|  User Query (Voice| -----> | Vector Search in     | -----> | Augmented Context     |
|  or Text Input)   |        | ChromaDB Knowledge   |        | Injected into LLM     |
+-------------------+        +----------------------+        +-----------------------+
                                                                         |
                                                                         v
                                                             +-----------------------+
                                                             | Grounded Response     |
                                                             | with Source Citations |
                                                             +-----------------------+
```

### End-to-End Pipeline Breakdown
1. **Document Ingestion**: Parsing structured and unstructured documents (PDF, DOCX, TXT, CSV) and cleaning extracted text.
2. **Text Chunking**: Splitting long documents into discrete, semantically cohesive passages with fixed overlap.
3. **Vector Embedding**: Mapping chunks into dense high-dimensional semantic vector spaces using transformer encoders.
4. **Vector Indexing**: Storing embeddings and metadata in an optimized vector database (`ChromaDB`).
5. **Semantic Retrieval**: Generating dense query vectors and calculating cosine similarity against indexed knowledge vectors.
6. **Augmented Synthesis**: Injecting top-matching excerpts into the LLM system prompt along with conversation history.
7. **Grounded Generation**: Outputting factual, cited answers or triggering clarification for ambiguous inquiries.

---

## 2. Multi-Agent Query Resolution Architecture

This platform implements a **5-Agent Collaborative Pipeline** to ensure accuracy, context retention, and hallucination reduction:

```
                  +-----------------------------------+
                  |      User Query (Voice / Text)    |
                  +-----------------------------------+
                                    |
                                    v
                  +-----------------------------------+
                  | 1. Conversation Memory Agent      |  <--- Pulls last 5 turns
                  +-----------------------------------+
                                    |
                                    v
                  +-----------------------------------+
                  | 2. Query Understanding Agent      |  <--- Classifies Intent & Entities
                  +-----------------------------------+
                                    |
                                    v
                  +-----------------------------------+
                  | 3. ChromaDB Retrieval Agent       |  <--- Top-5 Semantic Search
                  +-----------------------------------+
                                    |
                                    v
                  +-----------------------------------+
                  | 4. Clarification Agent            |  <--- Similarity Check (< 0.50?)
                  +-----------------------------------+
                        |                       |
            (Low Confidence / Ambiguous)  (Confidence Confirmed)
                        |                       |
                        v                       v
          +-------------------------+  +-------------------------------+
          | Clarification Prompts   |  | 5. Response Generation Agent  |
          | to User                 |  | (Gemini 1.5 Flash + Citations)|
          +-------------------------+  +-------------------------------+
                        \                       /
                         \                     /
                          v                   v
                  +-----------------------------------+
                  | Memory Agent Records Session Turn |
                  +-----------------------------------+
                                    |
                                    v
                  +-----------------------------------+
                  | Voice Output (SpeechSynthesis)    |
                  +-----------------------------------+
```

### Detailed Agent Roles

1. **Conversation Memory Agent (`backend/agents/memory_agent.py`)**
   - **Role**: Maintains multi-turn conversation memory (last 5 turns) per session in SQLite.
   - **Interaction**: Resolves conversational pronouns ("it", "they", "that policy") by supplying conversational context to subsequent agents.

2. **Query Understanding Agent (`backend/agents/query_agent.py`)**
   - **Role**: Analyzes the lexical and semantic structure of the user query.
   - **Classification**: Categorizes query type into:
     - **Factual**: Direct entity/data lookups (*"What is the annual leave allowance?"*).
     - **Procedural**: Step-by-step instructions (*"How do I install CloudSync Pro?"*).
     - **Comparative**: Side-by-side evaluations (*"Compare Standard vs Pro edition"*).
     - **Unavailable-Info**: Queries requiring fallback or clarification.
   - **Normalization**: Extracts core search keywords and reformulates queries using session memory.

3. **Retrieval Agent (`backend/agents/retrieval_agent.py`)**
   - **Role**: Computes query embeddings and performs Top-$k$ ($k=5$) semantic vector retrieval over ChromaDB.
   - **Metrics**: Computes cosine distances, translates them to similarity percentages ($0.0$ to $1.0$), and calculates average relevance.

4. **Clarification Agent (`backend/agents/clarification_agent.py`)**
   - **Role**: Acts as a guardrail against hallucinations.
   - **Mechanism**: Inspects the highest retrieval similarity score. If the score falls below the confidence threshold ($0.50$) or if the query is inherently ambiguous, it bypasses LLM generation and prompts the user for clarification with suggested actions and indexed document catalogs.

5. **Response Generation Agent (`backend/agents/response_agent.py`)**
   - **Role**: Synthesizes grounded responses by invoking Google Gemini API (`gemini-1.5-flash`) or local structured synthesis engine.
   - **Citation Enforcement**: Attaches structured citation metadata (source file, chunk ID, relevance percentage, text snippet).

---

## 3. Chunking Strategy & Parameter Rationalization

- **Chunk Size**: `500` characters / approx. tokens.
- **Chunk Overlap**: `50` characters / approx. tokens ($10\%$ overlap ratio).
- **Splitter Algorithm**: LangChain's `RecursiveCharacterTextSplitter` with hierarchical separators `["\n\n", "\n", ". ", "? ", "! ", " ", ""]`.

### Why This Strategy Was Chosen:
1. **Semantic Completeness**: 500 characters captures 2-4 complete sentences, sufficient to encapsulate a discrete policy rule, configuration step, or technical specification without fragmentation.
2. **Context Window Efficiency**: Keeps top-5 retrieved chunks concise (~2,500 characters), ensuring fast LLM inference times and minimal token consumption.
3. **Boundary Preservation**: A 50-character overlap prevents critical context (such as conditional clauses like "provided that..." or exception criteria) from being severed at chunk boundaries.

---

## 4. Embedding Model: `sentence-transformers/all-MiniLM-L6-v2`

The platform uses Hugging Face's `sentence-transformers/all-MiniLM-L6-v2` dense embedding model.

### Key Characteristics:
- **Dimensions**: 384-dimensional dense vectors.
- **Max Sequence Length**: 256 tokens.
- **Speed & Footprint**: ~80MB model size; encodes ~14,200 sentences/second on GPU, or instantaneous inference on standard CPU.
- **Metric**: Normalized cosine similarity.

### Selection Rationale:
- **Zero API Cost / Free**: Runs completely locally on CPU without external API rate limits or latency.
- **Exceptional Semantic Density**: Consistently ranks at the top of the MTEB (Massive Text Embedding Benchmark) for retrieval tasks relative to its lightweight memory footprint.
- **Reliability**: Eliminates third-party embedding service downtime during knowledge ingestion.

---

## 5. Web Speech API Integration Overview

The frontend seamlessly integrates the native browser **W3C Web Speech API** for multimodal voice interaction:

```
[User Mic] ---> SpeechRecognition (STT) ---> Text Area ---> Flask Backend (/query)
                                                                    |
                                                                    v
[Speaker]  <--- SpeechSynthesis (TTS)   <--- Formatted Response <---+
```

1. **SpeechRecognition (Voice-to-Text Input)**
   - Utilizes `window.SpeechRecognition` or `window.webkitSpeechRecognition`.
   - Real-time continuous transcription with interim results rendered directly in the chat box.
   - Visual pulsing audio wave animation during active speech capture.
   - Auto-triggers query submission upon pause detection (`onend`).

2. **SpeechSynthesis (Text-to-Speech Output)**
   - Utilizes `window.speechSynthesis` and `SpeechSynthesisUtterance`.
   - Cleans markdown formatting, citations, and URLs before synthesis to produce clear, human-like voice responses.
   - Includes global Voice Output toggles (ON/OFF) and per-message replay buttons.
