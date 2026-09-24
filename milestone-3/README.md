# Milestone 3: AI-Based Knowledge Retrieval Platform with Query Resolution System

Milestone 3 extends the multi-agent RAG system with four core components:
1. **Clarification Agent (M3.1)**: Ambiguity detection & follow-up question generation.
2. **Conversation Memory Agent (M3.2)**: Multi-turn session context & pronoun resolution ("its", "them", "it").
3. **Voice Input and Text-to-Speech (M3.3)**: Web Speech API voice-to-text and text-to-speech with controls (speak, pause, resume, stop).
4. **Response Transparency Panel (M3.4)**: Expandable evidence display with actual chunk metadata, page/section numbers, and relevance scores.

---

## Directory Structure
```
milestone-3/
├── agents/
│   ├── clarification_agent.py
│   └── conversation_memory_agent.py
├── memory/
│   └── conversation_memory.py
├── voice/
│   ├── speech_recognition.js
│   └── text_to_speech.js
├── transparency/
│   └── transparency_panel.js
├── orchestration/
│   └── milestone3_orchestrator.py
├── api/
│   └── app.py
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── script.js
├── tests/
│   ├── test_clarification.py
│   ├── test_memory.py
│   ├── test_transparency.py
│   ├── test_voice.py
│   └── test_orchestration.py
├── documentation/
│   └── Milestone-3.md
└── README.md
```

---

## How to Run Milestone 3

### 1. Install Dependencies
Make sure you have Python 3.9+ and the project requirements installed:
```bash
pip install -r requirements.txt
```

### 2. Set Optional Gemini API Key
```bash
# Windows PowerShell
$env:GEMINI_API_KEY="your_api_key_here"

# Linux / macOS
export GEMINI_API_KEY="your_api_key_here"
```
*(Note: If no API key is set, the system seamlessly runs in local synthesis mode.)*

### 3. Start the API Server
```bash
python milestone-3/api/app.py
```
The API server will start at `http://localhost:5000`.

### 4. Open the Web Application
Open your web browser and navigate to:
```
http://localhost:5000
```
Or open `milestone-3/frontend/index.html` directly in Google Chrome or Microsoft Edge.

---

## Running Automated Tests

Run the full automated test suite covering all 4 components and end-to-end scenarios:
```bash
python -m unittest discover milestone-3/tests
```

Or run individual test files:
```bash
python milestone-3/tests/test_clarification.py
python milestone-3/tests/test_memory.py
python milestone-3/tests/test_transparency.py
python milestone-3/tests/test_voice.py
python milestone-3/tests/test_orchestration.py
```
