# Milestone 1: Data Specifications

## AI-Based Knowledge Retrieval Platform with Query Resolution System

---

## 1. Overview

This document provides formal data specifications and schemas for all entities traversing the **AI-Based Knowledge Retrieval Platform with Query Resolution System**. Data is organized into four distinct lifecycle categories:

1. **Input Data**: Raw signals entered by users (queries, files, audio input).
2. **Processing Data**: Intermediate normalized representations (extracted text, chunks, embeddings, agent telemetry).
3. **Retrieved Data**: Vector search matches, similarity scores, and ranked contexts.
4. **Output Data**: Synthesized answers, structured citations, and UI payload contracts.

---

## 2. Category 1: Input Data Specifications

### 2.1 User Query Schema (`QueryRequest`)
Represents the incoming question submitted via text input or voice transcription.

| Field | Type | Required | Description | Example |
| :--- | :--- | :--- | :--- | :--- |
| `query` | string | Yes | The textual question asked by the user | `"What is the annual leave allowance?"` |
| `session_id` | string (UUID) | No | Unique session key for multi-turn history | `"550e8400-e29b-41d4-a716-446655440000"` |

```json
{
  "query": "How do I install CloudSync Pro on Windows?",
  "session_id": "c7a8b9f1-3d2e-4a6b-9c8d-1e2f3a4b5c6d"
}
```

### 2.2 Uploaded Document Schema (`DocumentUpload`)
Represents files uploaded through the Knowledge Ingestion dropzone.

| Field | Type | Required | Constraints | Example |
| :--- | :--- | :--- | :--- | :--- |
| `file` | binary/multipart | Yes | Max size: 25 MB | `hr_policy.pdf` |
| `file_extension` | string | Inferred | Allowed: `.pdf`, `.docx`, `.txt`, `.csv` | `".pdf"` |

---

## 3. Category 2: Processing Data Specifications

### 3.1 Document Metadata Schema (`DocumentMetadata`)
Stored in SQLite (`rag_metadata.db`) upon ingestion.

| Field | Type | Description |
| :--- | :--- | :--- |
| `id` | integer (PK) | Auto-incrementing primary key |
| `filename` | string | Original filename |
| `file_path` | string | Internal server storage path |
| `file_type` | string | Format extension (`.txt`, `.pdf`, etc.) |
| `file_size` | integer | File size in bytes |
| `chunks_count` | integer | Total chunk count generated |
| `uploaded_at` | string (ISO 8601) | Timestamp of upload |

```json
{
  "id": 1,
  "filename": "hr_policy.txt",
  "file_path": "backend/uploads/hr_policy.txt",
  "file_type": ".txt",
  "file_size": 4210,
  "chunks_count": 9,
  "uploaded_at": "2026-09-03T10:30:00Z"
}
```

### 3.2 Chunk Schema (`Chunk`)
The unit of text stored and indexed in ChromaDB.

| Field | Type | Description |
| :--- | :--- | :--- |
| `id` | string | Deterministic key: `{filename}_chunk_{index}` |
| `text` | string | Chunk text content (maximum 500 characters) |
| `metadata.chunk_id` | string | Unique chunk identifier |
| `metadata.source` | string | Originating filename |
| `metadata.chunk_index` | integer | 0-based sequence number within document |
| `metadata.total_chunks` | integer | Total chunks in parent document |
| `metadata.char_count` | integer | Character count of chunk |
| `metadata.timestamp` | string | Processing timestamp |

```json
{
  "id": "hr_policy.txt_chunk_3",
  "text": "3. Annual Leave Policy\nFull-time employees are entitled to 20 business days of paid annual leave per calendar year. Leave accrues monthly at a rate of 1.67 days per full month worked. Leave requests exceeding 5 consecutive business days must be submitted at least 2 weeks in advance to the direct manager.",
  "metadata": {
    "chunk_id": "hr_policy.txt_chunk_3",
    "source": "hr_policy.txt",
    "chunk_index": 3,
    "total_chunks": 9,
    "char_count": 328,
    "timestamp": "2026-09-03T10:30:01Z"
  }
}
```

### 3.3 Embedding Vector Representation
Text converted into dense floating-point vector arrays.

| Attribute | Specification |
| :--- | :--- |
| **Model** | `sentence-transformers/all-MiniLM-L6-v2` |
| **Dimensions** | `384` |
| **Data Type** | Array of 32-bit floating-point numbers (`float32`) |
| **Normalization** | L2-normalized ($\|v\| = 1.0$) |

```json
{
  "id": "hr_policy.txt_chunk_3",
  "vector": [0.0382, -0.0194, 0.0812, "... (384 float values total) ...", -0.0451],
  "document": "3. Annual Leave Policy\nFull-time employees...",
  "metadata": { "source": "hr_policy.txt", "chunk_index": 3 }
}
```

---

## 4. Category 3: Retrieved Data Specifications

### 4.1 Retrieval Match Schema (`RetrievalMatch`)
Returned by ChromaDB during nearest-neighbor search.

| Field | Type | Description |
| :--- | :--- | :--- |
| `id` | string | Chunk ID |
| `text` | string | Text content of matching chunk |
| `metadata` | object | Source document and index metadata |
| `distance` | float | Cosine distance ($0.0 \le d \le 2.0$) |
| `similarity` | float | Cosine similarity score ($1.0 - \text{distance}$) |

```json
{
  "id": "hr_policy.txt_chunk_3",
  "text": "3. Annual Leave Policy\nFull-time employees are entitled to 20 business days...",
  "metadata": {
    "source": "hr_policy.txt",
    "chunk_index": 3
  },
  "distance": 0.1458,
  "similarity": 0.8542
}
```

---

## 5. Category 4: Output Data Specifications

### 5.1 Agent Pipeline Telemetry Step (`AgentPipelineStep`)
Auditable record of actions taken by each agent during query resolution.

```json
{
  "step": 2,
  "agent": "Query Understanding Agent",
  "action": "Classified query intent and extracted keywords",
  "details": {
    "intent": "factual",
    "keywords": ["annual", "leave", "allowance", "employees"]
  }
}
```

### 5.2 Citation Schema (`Citation`)
Grounded reference linking answers to original documents.

```json
{
  "source_index": 1,
  "source_file": "hr_policy.txt",
  "chunk_id": "hr_policy.txt_chunk_3",
  "similarity_score": 0.8542,
  "excerpt": "Full-time employees are entitled to 20 business days of paid annual leave per calendar year..."
}
```

### 5.3 Final Synthesized API Response Schema (`QueryResponse`)
Complete JSON payload returned to the frontend.

| Field | Type | Description |
| :--- | :--- | :--- |
| `query` | string | Original user query |
| `query_type` | string | Classified intent (`factual`, `procedural`, `comparative`) |
| `response` | string | Synthesized answer or clarification message |
| `is_clarification` | boolean | `true` if similarity fell below confidence threshold ($0.50$) |
| `confidence_score` | float | Highest similarity score ($0.0$ to $1.0$) |
| `engine` | string | Generation model (`Gemini 1.5 Flash` or `Local Synthesis`) |
| `session_id` | string | Persistent conversation session identifier |
| `citations` | array[Citation] | List of grounded source references |
| `agent_pipeline_steps` | array[Step] | Execution audit trail of the 5 agents |

#### Example Final Response Payload:
```json
{
  "query": "How many days of paid annual leave do employees receive?",
  "query_type": "factual",
  "response": "Full-time employees are entitled to 20 business days of paid annual leave per calendar year [Source: hr_policy.txt]. Leave accrues monthly at a rate of 1.67 days per full month worked. For requests exceeding 5 consecutive days, notice must be submitted at least 2 weeks in advance.",
  "is_clarification": false,
  "confidence_score": 0.854,
  "engine": "Gemini (gemini-1.5-flash)",
  "session_id": "c7a8b9f1-3d2e-4a6b-9c8d-1e2f3a4b5c6d",
  "citations": [
    {
      "source_index": 1,
      "source_file": "hr_policy.txt",
      "chunk_id": "hr_policy.txt_chunk_3",
      "similarity_score": 0.854,
      "excerpt": "Full-time employees are entitled to 20 business days of paid annual leave per calendar year..."
    }
  ],
  "agent_pipeline_steps": [
    { "step": 1, "agent": "Memory Agent", "action": "Retrieved 0 prior turns" },
    { "step": 2, "agent": "Query Understanding Agent", "action": "Classified intent: factual" },
    { "step": 3, "agent": "Retrieval Agent", "action": "Retrieved 5 chunks from ChromaDB" },
    { "step": 4, "agent": "Clarification Agent", "action": "Confidence 85.4% >= 50.0% threshold (Passed)" },
    { "step": 5, "agent": "Response Agent", "action": "Generated grounded answer via Gemini 1.5 Flash" }
  ]
}
```
