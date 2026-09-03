# Milestone 1: Web Speech API Integration

## AI-Based Knowledge Retrieval Platform with Query Resolution System

---

## 1. Overview of Web Speech API

The **W3C Web Speech API** is a modern browser-native JavaScript specification that enables web applications to incorporate voice data into their interfaces. It consists of two distinct functional interfaces:

1. **SpeechRecognition (Speech-to-Text / STT)**: Provides the ability to capture audio streams from the user's microphone, recognize speech in real time, and transcribe spoken words into text strings.
2. **SpeechSynthesis (Text-to-Speech / TTS)**: Provides speech synthesis capabilities, converting programmatic text into synthesized audio output using browser-installed voices.

By using the native Web Speech API, this project achieves multimodal voice interaction **directly in the client browser without needing third-party cloud speech API keys, external binary installations, or server-side audio streaming pipelines**.

---

## 2. End-to-End Voice Interaction Flow

The voice interaction pipeline integrates speech input and audio synthesis with the backend RAG orchestrator:

```
User speaks
   ↓
Speech Recognition (STT: browser-native)
   ↓
Text Query (populated into chat box)
   ↓
Query Processing (Multi-Agent RAG Orchestrator)
   ↓
AI Response (grounded answer + citations)
   ↓
Speech Synthesis (TTS: browser-native)
   ↓
User hears response
```

---

## 3. Speech Recognition (Voice-to-Text Input)

### 3.1 Mechanism & Implementation
Speech Recognition utilizes `window.SpeechRecognition` (or `window.webkitSpeechRecognition` for Chromium-based engines). 

```javascript
// Example Client Initialization
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
const recognition = new SpeechRecognition();

recognition.continuous = false;      // Capture discrete sentence queries
recognition.interimResults = true;   // Provide live feedback as user speaks
recognition.lang = 'en-US';         // Primary language model

// Event handlers
recognition.onstart = () => {
    // Show active pulse animation on UI mic button
    micButton.classList.add('recording');
};

recognition.onresult = (event) => {
    let transcript = '';
    for (let i = event.resultIndex; i < event.results.length; i++) {
        transcript += event.results[i][0].transcript;
    }
    // Update input box in real time
    queryInput.value = transcript;
};

recognition.onend = () => {
    micButton.classList.remove('recording');
    // Automatically submit query if speech was detected
    if (queryInput.value.trim().length > 0) {
        submitQuery(queryInput.value.trim());
    }
};
```

### 3.2 Key Voice Input Features
- **Visual Feedback**: The microphone icon displays an animated pulsing radial wave while the microphone is capturing audio, giving clear visual confirmation.
- **Interim Live Stream**: Users see words appear in the text area in real-time as they speak.
- **Auto-Submission**: Upon detecting a natural speech pause (`onend`), the system automatically dispatches the transcribed query to the backend without requiring a manual click on the Send button.

---

## 4. Speech Synthesis (Text-to-Speech Output)

### 4.1 Mechanism & Implementation
Speech Synthesis utilizes the `window.speechSynthesis` global controller and `SpeechSynthesisUtterance` objects.

```javascript
// Example Speech Synthesis Execution
function speakText(text) {
    if (!window.speechSynthesis) return;

    // Stop any ongoing utterance
    window.speechSynthesis.cancel();

    // Clean text: strip markdown symbols, URLs, and citation brackets
    const cleanText = text
        .replace(/\[Source:[^\]]+\]/g, '')  // Remove citations for clean listening
        .replace(/[*#_`]/g, '')             // Strip markdown markup
        .trim();

    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.lang = 'en-US';
    utterance.rate = 1.0;   // Natural speaking pace
    utterance.pitch = 1.0;  // Standard pitch

    // Choose preferred natural voice if available
    const voices = window.speechSynthesis.getVoices();
    const preferredVoice = voices.find(v => v.lang.startsWith('en') && (v.name.includes('Google') || v.name.includes('Natural')));
    if (preferredVoice) utterance.voice = preferredVoice;

    window.speechSynthesis.speak(utterance);
}
```

### 4.2 Key Voice Output Features
- **Audio Sanitization**: Automatically strips technical citation tags (e.g., `[Source: hr_policy.txt, Chunk: chunk_2]`) and markdown formatting so that the spoken output sounds natural and fluent.
- **User Control Toggle**: A dedicated UI button (`Voice Output: ON / OFF`) in the workspace header allows users to mute or re-enable audio responses at any time.
- **Interruption Management**: Starting a new query or clicking the mute button immediately executes `window.speechSynthesis.cancel()`, preventing audio overlaps.

---

## 5. Browser Support & Compatibility Matrix

| Browser | Speech Recognition (STT) | Speech Synthesis (TTS) | Recommended For Project |
| :--- | :--- | :--- | :--- |
| **Google Chrome** | Full Native Support (`webkitSpeechRecognition`) | Full Native Support (`speechSynthesis`) | Yes (Primary Recommended) |
| **Microsoft Edge** | Full Native Support (`webkitSpeechRecognition`) | Full Native Support (`speechSynthesis`) | Yes (Primary Recommended) |
| **Mozilla Firefox** | Limited / Flag-dependent | Full Native Support (`speechSynthesis`) | Secondary (Text input works) |
| **Apple Safari** | Partial Support | Full Native Support (`speechSynthesis`) | Supported on modern iOS/macOS |

### Graceful Degradation & Fallbacks:
- If a user accesses the platform on an unsupported browser, the microphone button displays a helpful tooltip (`"Speech recognition not supported in this browser; please use Chrome or Edge"`).
- Text typing and standard keyboard interactions remain 100% operational regardless of microphone availability.

---

## 6. Integration with Chat Workspace UI

In the Milestone 1 frontend prototype:
1. **Header Control**: Contains the Voice Output toggle button displaying current status (`ON` / `OFF`).
2. **Input Bar**: Houses the dedicated circular microphone button placed alongside the send button.
3. **Accessibility**: Voice I/O enables hands-free operation for accessibility and enhanced user convenience.
