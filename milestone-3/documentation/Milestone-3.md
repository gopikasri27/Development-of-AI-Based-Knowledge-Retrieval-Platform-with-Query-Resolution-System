# Milestone 3 Documentation: AI-Based Knowledge Retrieval Platform with Query Resolution System

## 1. Milestone 3 Objective
Milestone 3 extends the existing Milestone 1 and Milestone 2 multi-agent query resolution system with four specialized modules:
1. **Clarification Agent (M3.1)**: Detects ambiguous, incomplete, or multi-part queries and asks targeted follow-up questions to refine queries prior to retrieval and synthesis.
2. **Conversation Memory Agent (M3.2)**: Tracks session context across multiple turns, resolves ambiguous pronouns ("its", "them", "it"), and selectively provides memory context without overloading LLM context windows.
3. **Voice Input and Text-to-Speech Module (M3.3)**: Provides browser-native speech recognition (`SpeechRecognition`) for voice queries and speech synthesis (`SpeechSynthesis`) for reading answers aloud with Play, Pause, Resume, and Stop controls.
4. **Response Transparency Panel (M3.4)**: Displays evidence-backed answer details (confidence indicator, actual document names, page/section numbers, chunk IDs, similarity scores, and excerpts) in an expandable/collapsible UI element.

Milestone 3 reuses and integrates cleanly with the existing Milestone 2 pipeline (`QueryUnderstandingAgent`, `RetrievalAgent`, `ResponseGenerationAgent`, ChromaDB vector store) without modifying or breaking previous implementations.

---

## 2. Clarification Agent (M3.1)
- **Functionality**: Evaluates incoming queries for ambiguity, incomplete specifications, missing subjects, or multiple interpretations.
- **Rules & Heuristics**:
  - Detects single-word underspecified inputs (e.g. `"leave"`, `"policy"`).
  - Detects broad multi-domain terms (e.g. `"Tell me about cloud."` -> `"Could you clarify whether you mean cloud computing, cloud storage, or cloud security?"`).
  - Evaluates context-dependent queries missing session memory.
  - Processes multi-part queries: if all parts are clear (e.g., `"Compare AWS and Azure and tell me which one is cheaper and how to deploy it."`), resolves directly without unnecessary clarification; if missing required targets, prompts for clarification.
- **Query Refinement**: Combines original query + user clarification response into a refined query (e.g. `"Tell me about cloud."` + `"Cloud computing."` -> `"Tell me about cloud computing."`).

---

## 3. Conversation Memory Agent (M3.2)
- **Session Context Store**: `ConversationMemory` tracks interaction turns by `session_id`, including queries, refined queries, answers, clarification states, referenced sources, and topics.
- **Pronoun Resolution**: Detects pronouns (`"its"`, `"them"`, `"it"`, `"this"`, `"that"`) and substitutes explicit subjects extracted from previous turns (e.g. Turn 1: `"What is IaaS?"` -> Turn 2: `"What are its benefits?"` resolves to `"What are the benefits of IaaS?"`).
- **Selective Context Window**: Selects only relevant memory context (recent entities, topics, and previous turn summary) for downstream agents instead of dumping raw history into LLM prompts.
- **Context Missing Handling**: If user asks a context-dependent question without prior history, memory agent signals missing context, allowing the Clarification Agent to prompt the user gracefully.

---

## 4. Voice Input (M3.3)
- **Implementation**: Native browser Web Speech API (`window.SpeechRecognition` / `window.webkitSpeechRecognition`).
- **Flow**: Microphone -> Voice Recognition -> Transcribed text displayed in UI textarea -> Query resolution pipeline.
- **Controls & Status**:
  - Mic button with active recording pulse animation (`.mic-btn.listening`).
  - Real-time interim transcription feedback.
- **Error Handling**: Handles unsupported browser, permission denied (`not-allowed`), network errors, empty speech, and incomplete recognition.

---

## 5. Text-to-Speech (M3.3)
- **Implementation**: Native browser Web Speech API (`window.speechSynthesis` and `SpeechSynthesisUtterance`).
- **Controls**: Read Aloud button with full player controls:
  - **Speak**: Starts reading answer aloud.
  - **Pause**: Pauses active speech synthesis.
  - **Resume**: Resumes paused speech synthesis.
  - **Stop**: Cancels active speech synthesis.
- **Text Sanitization**: Strips markdown symbols, code blocks, URLs, and source brackets (`[Source: ...]`) prior to speaking for clean auditory presentation.

---

## 6. Response Transparency Panel (M3.4)
- **UI Structure**: Renders evidence supporting the generated answer in a separate expandable/collapsible section below the main response text.
- **Metadata Fields**:
  - **Confidence Indicator**: Badge showing High, Medium, or Low confidence along with exact score (e.g. `High (0.89)`).
  - **Source Documents**: Actual filename (e.g. `hr_policy.txt`, `product_manual.txt`).
  - **Page / Section**: Section name and page number.
  - **Chunk ID**: Exact vector store chunk identifier (e.g. `chunk_23`).
  - **Relevance / Similarity Score**: Exact similarity score returned by Retrieval Agent.
  - **Retrieved Evidence Quote**: Exact excerpt block from indexed chunk.
- **Low Confidence / No Result Handling**: Displays `"Insufficient supporting evidence was found in the knowledge base."` without inventing metadata or hard-coding fake sources.

---

## 7. Updated Architecture
```
                         +-----------------------------------+
                         |  Text / Web Speech Voice Input    |
                         +-----------------------------------+
                                           |
                                           v
                         +-----------------------------------+
                         | Conversation Memory Agent (M3.2)  |
                         |  - Resolves pronouns & fetch context|
                         +-----------------------------------+
                                           |
                                           v
                         +-----------------------------------+
                         | Query Understanding Agent (M2.1)  |
                         |  - Intent classification           |
                         +-----------------------------------+
                                           |
                                           v
                         +-----------------------------------+
                         |   Clarification Agent (M3.1)      |
                         |  - Ambiguity check & follow-up    |
                         +-----------------------------------+
                                 /                   \
                 [Clarification Required]       [Query Clear]
                               /                       \
                              v                         v
                   +---------------------+   +---------------------+
                   | Return Targeted     |   | Retrieval Agent     |
                   | Clarification Prompt|   | (M2.2 - Vector Store|
                   +---------------------+   +---------------------+
                              |                         |
                   [User Clarification Response]        v
                              |              +---------------------+
                              +------------> | Response Generation |
                                             | Agent (M2.3 LLM)    |
                                             +---------------------+
                                                        |
                                                        v
                                             +---------------------+
                                             | Transparency Panel  |
                                             | (M3.4 Metadata)     |
                                             +---------------------+
                                                        |
                                                        v
                                             +---------------------+
                                             | Text-to-Speech Output|
                                             | (M3.3 Web Speech API|
                                             +---------------------+
                                                        |
                                                        v
                                             +---------------------+
                                             | Conversation Memory |
                                             | Update Turn         |
                                             +---------------------+
```

---

## 8. Data Flow
1. User enters text or speaks via Web Speech API.
2. Request sent to `POST /api/query` with `query` and `session_id`.
3. `ConversationMemoryAgent` inspects `session_id` history, resolves pronouns ("its" -> "IaaS"), and extracts relevant memory.
4. `QueryUnderstandingAgent` classifies intent (`factual`, `procedural`, `comparative`, `ambiguous`).
5. `ClarificationAgent` checks if query requires clarification. If yes, returns `is_clarification: true` and targeted follow-up question.
6. When user responds to clarification, `ClarificationAgent.refine_query()` generates refined query (e.g. `"Tell me about cloud computing."`).
7. `RetrievalAgent` executes vector search against ChromaDB vector store and filters low-confidence chunks.
8. `ResponseGenerationAgent` synthesizes grounded answer and computes confidence score.
9. `TransparencyPanel` formats actual document metadata, page/section, chunk ID, relevance score, and excerpt.
10. `Text-to-Speech` allows reading answer aloud with controls (speak, pause, resume, stop).
11. `ConversationMemory` stores turn details for future multi-turn follow-up queries.

---

## 9. Error Handling
- **Missing Microphone / Permission**: Displays graceful notification to enable microphone in browser settings.
- **Speech Recognition Error**: Recovers cleanly, stops listening animation, and allows keyboard input.
- **Offline / LLM API Fallback**: System seamlessly switches to local rule-based classification and synthesis when `GEMINI_API_KEY` is not set.
- **Low Confidence / No Result**: Displays transparent notice: `"Insufficient supporting evidence was found in the knowledge base."` without inventing metadata.

---

## 10. Testing
Comprehensive test suite located in `milestone-3/tests/`:
- `test_clarification.py`: Tests ambiguous, incomplete, context-dependent, multi-part, clear query, and query refinement logic.
- `test_memory.py`: Tests pronoun resolution, follow-up query, topic tracking, context switching, missing memory, and memory selection.
- `test_transparency.py`: Tests source mapping, chunk display, similarity scores, confidence indicators, and low-confidence/no-result outputs.
- `test_voice.py`: Tests speech transcription formatting and text-to-speech sanitizer rules.
- `test_orchestration.py`: End-to-end integration tests for all 5 mandatory scenarios.

Run tests using:
```bash
python -m unittest discover milestone-3/tests
```

---

## 11. Example Conversations

### Scenario 1: Normal Factual Query
- **User**: `"What is cloud computing?"`
- **Assistant**: Provides grounded answer from `hr_policy.txt`.
- **Transparency**: High Confidence (0.89), Source: `hr_policy.txt`, Chunk: `chunk_23`, Relevance: `0.89`.

### Scenario 2: Ambiguous Query & Clarification
- **User**: `"Tell me about cloud."`
- **Assistant**: `"Could you clarify whether you mean cloud computing, cloud storage, or cloud security?"`
- **User**: `"Cloud computing."`
- **Refined Query**: `"Tell me about cloud computing."`
- **Assistant**: Provides detailed grounded answer for cloud computing with full transparency panel.

### Scenario 3: Multi-Turn Follow-Up Query
- **User**: `"What is IaaS?"`
- **Assistant**: `"IaaS stands for Infrastructure as a Service..."`
- **User**: `"What are its benefits?"`
- **Memory Agent**: Resolves `"its"` -> `"IaaS"` (`"What are the benefits of IaaS?"`).
- **Assistant**: Provides grounded benefits of IaaS without requiring the user to repeat the topic.

### Scenario 4: Voice Query
- **User (speaks)**: `"What are the step-by-step instructions to install CloudSync Pro?"`
- **System**: Transcribes speech -> Query Resolution -> Displays answer -> TTS reads answer aloud.

### Scenario 5: Out of Domain / Low Evidence
- **User**: `"What is today's weather in Coimbatore?"`
- **Assistant**: `"Sufficient information was not found in the knowledge base to provide a reliable answer."`
- **Transparency**: Low Confidence (0.12), Insufficient evidence notice.

---

## 12. Integration with Milestone 2
- Reuses M2's `QueryUnderstandingAgent`, `RetrievalAgent`, and `ResponseGenerationAgent` directly.
- Reuses M2's `VectorStoreManager` and ChromaDB vector store.
- Wraps M2 agents inside `Milestone3Orchestrator` without modifying or deleting M1/M2 code.

---

## 13. Limitations
- Browser Web Speech API requires browser support (supported natively in Chrome and Edge).
- Conversation memory is stored per-session in memory and resets when the session is cleared.
