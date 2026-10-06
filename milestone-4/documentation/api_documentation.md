# Milestone 4 API Reference & Specification

## Overview
The platform exposes RESTful endpoints via Flask on port 5000. All request payloads and response bodies use JSON formatting.

---

## 1. Core Query & Resolution Endpoints

### `POST /api/query` (or `/query`)
Main endpoint for executing multi-agent query processing pipeline.

**Request Header:** `Content-Type: application/json`

**Request Payload:**
```json
{
  "query": "What is Zero Trust Architecture?",
  "session_id": "session_12345",
  "clarification_response": null
}
```

**Response Payload (Standard Answer):**
```json
{
  "query": "What is Zero Trust Architecture?",
  "answer": "Zero Trust Architecture is a cybersecurity model built on the principle 'Never Trust, Always Verify'...",
  "is_clarification": false,
  "query_type": "factual",
  "classification_confidence": 0.95,
  "confidence": {
    "score": 0.88,
    "label": "High"
  },
  "citations": [
    {
      "source": "cybersecurity_knowledge.txt",
      "chunk_id": "cybersecurity_knowledge.txt_chunk_12",
      "similarity": 0.88
    }
  ],
  "transparency": {
    "steps": [
      { "name": "Query Understanding", "status": "completed", "duration_ms": 12 },
      { "name": "Context Retrieval", "status": "completed", "duration_ms": 45 },
      { "name": "Response Generation", "status": "completed", "duration_ms": 230 }
    ]
  },
  "telemetry": {
    "pipeline_execution_time_ms": 287
  }
}
```

**Response Payload (Clarification Required):**
```json
{
  "query": "Tell me about cloud deployment.",
  "is_clarification": true,
  "clarification": {
    "question": "Which cloud deployment model or topic would you like information on?",
    "options": [
      "Public Cloud vs Private Cloud",
      "IaaS, PaaS, and SaaS Service Models",
      "Cloud Storage & Security Options"
    ]
  }
}
```

---

### `POST /api/clarify`
Submits user's choice to resolve an active clarification prompt.

**Request Payload:**
```json
{
  "session_id": "session_12345",
  "clarification_response": "IaaS, PaaS, and SaaS Service Models"
}
```

---

## 2. Conversation Memory Endpoints

### `GET /api/memory/<session_id>`
Retrieves session turn history and extracted context summary.

**Response:**
```json
{
  "session_id": "session_12345",
  "turns_count": 4,
  "history": [...],
  "summary": {
    "entities": ["Zero Trust", "Firewall"],
    "topics": ["Cybersecurity"]
  }
}
```

### `DELETE /api/memory/<session_id>`
Clears history for specified session ID.

---

## 3. Vector Knowledge Base Ingestion Endpoints

### `POST /api/upload`
Uploads PDF, DOCX, TXT, or CSV document and indexes chunks into ChromaDB.

**Request:** `multipart/form-data` with `file` parameter.

---

## 4. Query Analytics Endpoints (Milestone 4)

### `GET /api/analytics/stats`
Returns aggregated analytics summary.

**Query Parameters:**
- `domain` (optional): Filter by domain (e.g. `AI/ML`, `Cloud Computing`, `Cybersecurity`)
- `query_type` (optional): Filter by intent (`factual`, `procedural`, `comparative`, `ambiguous`)
- `status` (optional): Filter by status (`answered`, `knowledge_gap`, `clarification_needed`)
- `confidence_level` (optional): `High`, `Medium`, `Low`

**Response:**
```json
{
  "total_queries": 42,
  "answered_queries": 38,
  "knowledge_gap_count": 4,
  "resolution_rate": 0.904,
  "average_confidence": 0.76,
  "by_domain": {
    "AI/ML": 15,
    "Cloud Computing": 12,
    "Cybersecurity": 10,
    "HR & Policy": 5
  },
  "by_type": {
    "factual": 22,
    "procedural": 10,
    "comparative": 6,
    "ambiguous": 4
  },
  "by_confidence": {
    "High": 30,
    "Medium": 8,
    "Low": 4
  }
}
```

---

### `GET /api/analytics/gaps`
Returns detected knowledge gaps where queries had low confidence or missing context.

**Query Parameters:**
- `min_frequency` (int, default=1): Minimum occurrence count.

**Response:**
```json
{
  "knowledge_gaps": [
    {
      "topic": "Quantum Encryption Latency",
      "domain": "Cybersecurity",
      "frequency": 3,
      "sample_queries": [
        "What is quantum cryptographic teleportation latency?",
        "How to benchmark quantum key distribution latency?"
      ]
    }
  ],
  "total_gaps": 1
}
```

---

### `GET /api/analytics/queries`
Returns paginated list of recent query execution logs.

**Query Parameters:**
- `limit` (int, default=50)
- `offset` (int, default=0)
- `domain`, `query_type`, `status`, `confidence_level`

---

### `GET /api/analytics/topics`
Returns top frequently asked topics.

**Response:**
```json
{
  "frequent_topics": [
    { "topic": "zero trust architecture", "count": 8 },
    { "topic": "semantic search rag", "count": 6 }
  ]
}
```

---

### `GET /analytics`
Serves the interactive web-based Query Analytics Dashboard UI.
