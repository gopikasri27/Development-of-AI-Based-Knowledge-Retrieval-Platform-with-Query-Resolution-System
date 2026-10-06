# Milestone 4 Testing Documentation & Validation Strategy

## 1. Testing Framework Overview
Milestone 4 implements an automated, reproducible End-to-End Test Suite (`milestone-4/tests/test_e2e_milestone4.py`) built on Python's `unittest` framework.

The test suite systematically evaluates system behavior across:
- **3 Specialized Knowledge Domains**: AI/ML, Cloud Computing, Cybersecurity (+ HR & Policy).
- **5 Intent Classifications**: Factual, Procedural, Comparative, Ambiguous, Out of Scope.
- **System Capabilities**: Multi-turn conversation memory, context switching, voice input simulation, transparency telemetry, anti-hallucination refusal, and query analytics recording.

---

## 2. Test Execution Command
To execute the automated end-to-end test suite:

```bash
python milestone-4/tests/test_e2e_milestone4.py
```

---

## 3. Test Cases Specification & Verification Matrix

| Test ID | Category | Description / Query | Expected Output | Success Criteria |
| :--- | :--- | :--- | :--- | :--- |
| **TC-01** | Factual Query | "What is machine learning and what are its main categories?" | Grounded definition covering Supervised, Unsupervised, Reinforcement Learning. | Confidence ≥ 0.30; non-empty answer; no clarification needed. |
| **TC-02** | Procedural Query | "How does semantic search work step by step in RAG systems?" | Sequential breakdown: text chunking → vector embeddings → HNSW distance search → generation. | Contains citations; confidence label High/Medium; detailed steps. |
| **TC-03** | Comparative Query | "Compare IaaS, PaaS, and SaaS cloud service models." | Structured comparison table/list of responsibility boundaries. | Mentions IaaS, PaaS, SaaS explicitly with context grounding. |
| **TC-04** | Ambiguous Query | "Tell me about cloud deployment." | Trigger clarification prompt or structured option list. | `is_clarification == True` or option list returned to user. |
| **TC-05** | Multi-Turn Memory | Turn 1: "What is CIA triad?"<br>Turn 2: "What does confidentiality mean within it?" | Contextual pronoun resolution referring to CIA triad. | Turn 2 references confidentiality in CIA triad context correctly. |
| **TC-06** | Context Switching | Turn 1: Cloud query<br>Turn 2: "Explain Zero Trust Architecture principles." | Smooth domain transition to Cybersecurity without cross-domain pollution. | Answers Zero Trust principles accurately using Cybersecurity domain doc. |
| **TC-07** | Voice Input | Spoken query with disfluencies: "um could you explain what symmetric encryption is with AES 256" | Normalized query processing and accurate resolution. | Resolves symmetric encryption / AES-256 without error. |
| **TC-08** | Out of Scope | "What will be the weather forecast in Tokyo tomorrow morning?" | Graceful refusal; zero hallucination. | Refusal message; confidence < 0.30; zero fake facts generated. |
| **TC-09** | Transparency | Any technical query | Captured execution trace metrics. | Includes telemetry step timings, classification confidence, distance metrics. |
| **TC-10** | Analytics & Gaps | Low-confidence / unindexed query | Entry logged in SQLite analytics database & gap flagged. | `total_queries` incremented in analytics DB; gap cluster identified. |

---

## 4. Test Result Reporting Structure
Upon execution, `test_e2e_milestone4.py` outputs a structured execution log detailing test case statuses, confidence scores, citation counts, and pipeline execution time. Results are formatted into `milestone-4/tests/test_report.md`.
