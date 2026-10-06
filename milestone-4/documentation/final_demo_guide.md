# Milestone 4 Demonstration & Walkthrough Guide

## 1. Quick Start / How to Run the Platform

### Step 1: Start the API Server
Open a terminal in the project root directory (`c:\Users\Gopika Sri\OneDrive\Desktop\rag\`) and run:

```bash
python milestone-3/api/app.py
```

The server will start on **`http://localhost:5000`**.

---

### Step 2: Open the Applications in Browser
- **Main Chat & RAG Assistant UI**: `http://localhost:5000/`
- **Query Analytics & Knowledge Gap Dashboard**: `http://localhost:5000/analytics`

---

## 2. Recommended Demonstration Walkthrough Script

### Scenario A: Testing Multi-Domain RAG Resolution
1. **AI/ML Domain Query**:
   - Type: *"What is machine learning and how does supervised learning differ from unsupervised learning?"*
   - Observe: System identifies query as `factual`, retrieves from `ai_ml_knowledge.txt`, displays answer with high confidence score and citations.
2. **Cloud Computing Domain Query**:
   - Type: *"Compare IaaS, PaaS, and SaaS cloud deployment models."*
   - Observe: System returns structured comparative response with citations to `cloud_computing_knowledge.txt`.
3. **Cybersecurity Domain Query**:
   - Type: *"Explain the core principles of Zero Trust Architecture."*
   - Observe: System explains "Never Trust, Always Verify", microsegmentation, and least privilege with citations to `cybersecurity_knowledge.txt`.

---

### Scenario B: Ambiguous Query & Clarification Agent
1. Type: *"Tell me about cloud deployment."*
2. Observe: System detects ambiguous query intent, activates Clarification Agent, and presents interactive clarification options.
3. Select an option (e.g., *"IaaS, PaaS, and SaaS Service Models"*) to receive a tailored response.

---

### Scenario C: Multi-Turn Conversation Memory
1. Turn 1: *"What is the CIA triad in cybersecurity?"*
2. Turn 2: *"What does confidentiality mean within it?"*
3. Observe: System maintains session context, correctly resolving "it" to the CIA triad from previous conversation turn.

---

### Scenario D: Voice Input & Output
1. Click the **Microphone Icon** in the chat input bar.
2. Speak a query (e.g., *"What is symmetric encryption?"*).
3. Observe real-time speech-to-text transcription (optimized for `en-IN` locale) and optional Text-to-Speech audio response playback.

---

### Scenario E: Transparency Panel Inspection
1. Expand the **Transparency Panel** on the right side of the UI.
2. Observe execution pipeline stages, classification confidence scores, similarity distance metrics, and vector chunk details.

---

### Scenario F: Out-of-Scope Refusal & Knowledge Gap Detection
1. Type an unindexed out-of-scope query: *"What will be the weather in Chennai tomorrow?"*
2. Observe: System returns a polite refusal message ("Sufficient information was not found in the knowledge base..."), avoiding hallucination.
3. Navigate to **`http://localhost:5000/analytics`**:
   - View updated **Total Queries** metric card.
   - Inspect **Knowledge Domain Distribution** and **Query Intent Distribution** charts.
   - Observe the newly recorded **Knowledge Gap** entry under *Identified Knowledge Base Gaps*.
