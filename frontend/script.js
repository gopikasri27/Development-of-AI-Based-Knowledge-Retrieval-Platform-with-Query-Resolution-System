/**
 * Frontend Logic for AI Knowledge Retrieval Platform
 * - Document Upload & Indexing
 * - Multi-Agent RAG Interaction (POST /query)
 * - Web Speech API (SpeechRecognition for Voice Input & SpeechSynthesis for Voice Output)
 * - Pipeline telemetry & Citation rendering
 */

document.addEventListener("DOMContentLoaded", () => {
  // --- DOM Elements ---
  const dropzone = document.getElementById("dropzone");
  const fileInput = document.getElementById("fileInput");
  const uploadProgress = document.getElementById("uploadProgress");
  const progressBar = document.getElementById("progressBar");
  const uploadStatusText = document.getElementById("uploadStatusText");
  const documentsList = document.getElementById("documentsList");
  const docCount = document.getElementById("docCount");
  const refreshDocsBtn = document.getElementById("refreshDocsBtn");

  const queryInput = document.getElementById("queryInput");
  const sendBtn = document.getElementById("sendBtn");
  const micBtn = document.getElementById("micBtn");
  const messagesContainer = document.getElementById("messagesContainer");
  const welcomeCard = document.getElementById("welcomeCard");
  const clearChatBtn = document.getElementById("clearChatBtn");
  const ttsToggleBtn = document.getElementById("ttsToggleBtn");
  const ttsStatusText = document.getElementById("ttsStatusText");
  const pipelineContainer = document.getElementById("pipelineContainer");

  // System Stats Elements
  const vectorStoreStatus = document.getElementById("vectorStoreStatus");
  const llmEngineStatus = document.getElementById("llmEngineStatus");

  // --- App State ---
  let sessionId = "session_" + Math.random().toString(36).substring(2, 9);
  let isTtsEnabled = true;
  let isListening = false;
  let recognition = null;

  // --- Initialize Web Speech API (Voice-to-Text) ---
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (SpeechRecognition) {
    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = "en-US";

    recognition.onstart = () => {
      isListening = true;
      micBtn.classList.add("listening");
      queryInput.placeholder = "Listening... speak now...";
    };

    recognition.onresult = (event) => {
      let transcript = "";
      for (let i = event.resultIndex; i < event.results.length; ++i) {
        transcript += event.results[i][0].transcript;
      }
      queryInput.value = transcript;
    };

    recognition.onerror = (event) => {
      console.warn("Speech recognition error:", event.error);
      stopListening();
    };

    recognition.onend = () => {
      stopListening();
      if (queryInput.value.trim().length > 0) {
        // Automatically submit query after voice input
        handleSendMessage();
      }
    };
  } else {
    micBtn.title = "Speech recognition is not supported in this browser.";
    micBtn.style.opacity = "0.5";
  }

  function startListening() {
    if (!recognition) {
      alert("Voice input is not supported in your current browser. Please try Google Chrome or Microsoft Edge.");
      return;
    }
    try {
      queryInput.value = "";
      recognition.start();
    } catch (e) {
      console.error("Speech recognition start failed:", e);
    }
  }

  function stopListening() {
    isListening = false;
    micBtn.classList.remove("listening");
    queryInput.placeholder = "Ask a question or click the mic for voice input...";
    if (recognition) {
      try {
        recognition.stop();
      } catch (e) {}
    }
  }

  // --- Voice Output (Text-to-Speech) ---
  function speakText(text) {
    if (!("speechSynthesis" in window) || !isTtsEnabled) return;
    
    // Cancel any ongoing speech
    window.speechSynthesis.cancel();
    
    // Strip markdown tags & formatting for clean speech
    const cleanSpeech = text
      .replace(/\[Source:?.*?\]/gi, "")
      .replace(/[*#>`_-]/g, "")
      .replace(/https?:\/\/\S+/g, "")
      .trim();

    if (!cleanSpeech) return;

    const utterance = new SpeechSynthesisUtterance(cleanSpeech);
    utterance.rate = 1.0;
    utterance.pitch = 1.0;
    utterance.lang = "en-US";
    window.speechSynthesis.speak(utterance);
  }

  // --- Health Check & Documents Fetching ---
  async function fetchHealthAndDocuments() {
    try {
      const res = await fetch("/health");
      const data = await res.json();
      if (data.status === "healthy") {
        vectorStoreStatus.textContent = `${data.vector_store} (${data.total_chunks_indexed} chunks)`;
        llmEngineStatus.textContent = data.gemini_api_configured ? "Gemini 1.5 Flash" : "Local Synthesis";
      }
    } catch (e) {
      console.error("Health check error:", e);
    }

    try {
      const res = await fetch("/documents");
      const data = await res.json();
      renderDocumentsList(data.documents || []);
    } catch (e) {
      console.error("Documents fetch error:", e);
    }
  }

  function renderDocumentsList(docs) {
    docCount.textContent = docs.length;
    if (docs.length === 0) {
      documentsList.innerHTML = '<li class="empty-docs-msg">No documents indexed yet.</li>';
      return;
    }

    documentsList.innerHTML = docs
      .map(
        (d) => `
        <li class="doc-item">
          <div class="doc-info">
            <span class="doc-name" title="${d.filename}">${d.filename}</span>
            <span class="doc-meta">${(d.file_size / 1024).toFixed(1)} KB • ${d.chunks_count} chunks</span>
          </div>
          <span class="doc-badge">${d.file_type || ".txt"}</span>
        </li>
      `
      )
      .join("");
  }

  // --- Document Upload ---
  dropzone.addEventListener("click", () => fileInput.click());
  fileInput.addEventListener("change", (e) => {
    if (e.target.files.length > 0) {
      uploadFile(e.target.files[0]);
    }
  });

  dropzone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropzone.classList.add("dragover");
  });

  dropzone.addEventListener("dragleave", () => {
    dropzone.classList.remove("dragover");
  });

  dropzone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropzone.classList.remove("dragover");
    if (e.dataTransfer.files.length > 0) {
      uploadFile(e.dataTransfer.files[0]);
    }
  });

  async function uploadFile(file) {
    uploadProgress.classList.remove("hidden");
    progressBar.style.width = "40%";
    uploadStatusText.textContent = `Uploading and parsing '${file.name}'...`;

    const formData = new FormData();
    formData.append("file", file);

    try {
      progressBar.style.width = "75%";
      uploadStatusText.textContent = "Chunking and generating vector embeddings...";

      const res = await fetch("/upload", {
        method: "POST",
        body: formData,
      });

      const data = await res.json();
      if (res.ok) {
        progressBar.style.width = "100%";
        uploadStatusText.textContent = `Indexed ${data.chunks_indexed} chunks successfully!`;
        setTimeout(() => {
          uploadProgress.classList.add("hidden");
          progressBar.style.width = "0%";
        }, 2500);
        fetchHealthAndDocuments();
      } else {
        alert(data.error || "Failed to upload document");
        uploadProgress.classList.add("hidden");
      }
    } catch (e) {
      console.error("Upload error:", e);
      alert("Error uploading document to server");
      uploadProgress.classList.add("hidden");
    }
  }

  // --- Multi-Agent Step Pipeline Animations ---
  function updatePipelineSteps(activeStep) {
    pipelineContainer.classList.remove("hidden");
    const steps = ["step-memory", "step-query", "step-retrieval", "step-clarification", "step-response"];
    
    steps.forEach((stepId, idx) => {
      const el = document.getElementById(stepId);
      if (!el) return;
      el.classList.remove("active", "completed");
      if (idx < activeStep) {
        el.classList.add("completed");
      } else if (idx === activeStep) {
        el.classList.add("active");
      }
    });
  }

  function finalizePipelineSteps() {
    const steps = ["step-memory", "step-query", "step-retrieval", "step-clarification", "step-response"];
    steps.forEach((stepId) => {
      const el = document.getElementById(stepId);
      if (el) el.classList.add("completed");
    });
  }

  // --- Chat Message Rendering ---
  function appendUserMessage(text) {
    if (welcomeCard) welcomeCard.style.display = "none";

    const msgRow = document.createElement("div");
    msgRow.className = "message-row user";
    msgRow.innerHTML = `
      <div class="avatar">You</div>
      <div class="bubble">
        <div class="message-content">${escapeHtml(text)}</div>
      </div>
    `;
    messagesContainer.appendChild(msgRow);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }

  function appendLoadingMessage() {
    const msgRow = document.createElement("div");
    msgRow.className = "message-row assistant";
    msgRow.id = "loadingMessage";
    msgRow.innerHTML = `
      <div class="avatar">AI</div>
      <div class="bubble">
        <div class="message-content" style="color: var(--text-muted);">
          <span>Orchestrating agents and retrieving context</span>...
        </div>
      </div>
    `;
    messagesContainer.appendChild(msgRow);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }

  function removeLoadingMessage() {
    const el = document.getElementById("loadingMessage");
    if (el) el.remove();
  }

  function appendAssistantMessage(data) {
    removeLoadingMessage();

    const msgRow = document.createElement("div");
    msgRow.className = "message-row assistant";

    // Format query type badge
    let tagClass = "factual";
    if (data.is_clarification) tagClass = "clarification";
    else if (data.query_type === "procedural") tagClass = "procedural";
    else if (data.query_type === "comparative") tagClass = "comparative";

    const tagText = data.is_clarification ? "Clarification Requested" : `${data.query_type || "Factual"} Query`;

    // Citations HTML
    let citationsHtml = "";
    if (data.citations && data.citations.length > 0) {
      const citationCards = data.citations
        .map(
          (c) => `
        <div class="citation-card">
          <div class="citation-top">
            <span class="citation-doc" title="${c.source_file}">📄 ${c.source_file}</span>
            <span class="citation-score">${Math.round(c.similarity_score * 100)}% match</span>
          </div>
          <p class="citation-snippet">"${escapeHtml(c.excerpt)}"</p>
        </div>
      `
        )
        .join("");

      citationsHtml = `
        <div class="citations-box">
          <div class="citations-header">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
              <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
            </svg>
            <span>Verified Sources (${data.citations.length})</span>
          </div>
          <div class="citation-cards-grid">
            ${citationCards}
          </div>
        </div>
      `;
    }

    msgRow.innerHTML = `
      <div class="avatar">AI</div>
      <div class="bubble">
        <span class="query-type-tag ${tagClass}">${tagText}</span>
        <div class="message-content">${formatMarkdown(data.response)}</div>
        ${citationsHtml}
        <button class="speak-response-btn" data-text="${escapeHtml(data.response)}">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/>
            <path d="M15.54 8.46a5 5 0 0 1 0 7.07"/>
          </svg>
          <span>Speak aloud</span>
        </button>
      </div>
    `;

    messagesContainer.appendChild(msgRow);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;

    // Attach speak button listener
    const speakBtn = msgRow.querySelector(".speak-response-btn");
    if (speakBtn) {
      speakBtn.addEventListener("click", () => {
        speakText(data.response);
      });
    }

    // Auto speak if enabled
    if (isTtsEnabled) {
      speakText(data.response);
    }
  }

  // --- Send Message Flow ---
  async function handleSendMessage() {
    const query = queryInput.value.trim();
    if (!query) return;

    queryInput.value = "";
    queryInput.style.height = "auto";
    sendBtn.disabled = true;

    appendUserMessage(query);
    appendLoadingMessage();

    // Animate multi-agent sequence
    updatePipelineSteps(0);
    setTimeout(() => updatePipelineSteps(1), 300);
    setTimeout(() => updatePipelineSteps(2), 600);
    setTimeout(() => updatePipelineSteps(3), 900);

    try {
      const res = await fetch("/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: query, session_id: sessionId }),
      });

      const data = await res.json();
      finalizePipelineSteps();

      if (res.ok) {
        appendAssistantMessage(data);
      } else {
        removeLoadingMessage();
        alert(data.error || "Query execution failed");
      }
    } catch (e) {
      removeLoadingMessage();
      console.error("Query error:", e);
      alert("Could not reach backend API server");
    } finally {
      sendBtn.disabled = false;
    }
  }

  // --- Event Listeners ---
  sendBtn.addEventListener("click", handleSendMessage);

  queryInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  });

  micBtn.addEventListener("click", () => {
    if (isListening) {
      stopListening();
    } else {
      startListening();
    }
  });

  ttsToggleBtn.addEventListener("click", () => {
    isTtsEnabled = !isTtsEnabled;
    if (isTtsEnabled) {
      ttsStatusText.textContent = "ON";
      ttsToggleBtn.classList.remove("secondary");
    } else {
      ttsStatusText.textContent = "OFF";
      ttsToggleBtn.classList.add("secondary");
      window.speechSynthesis.cancel();
    }
  });

  clearChatBtn.addEventListener("click", () => {
    sessionId = "session_" + Math.random().toString(36).substring(2, 9);
    messagesContainer.innerHTML = "";
    if (welcomeCard) {
      messagesContainer.appendChild(welcomeCard);
      welcomeCard.style.display = "block";
    }
    pipelineContainer.classList.add("hidden");
    window.speechSynthesis.cancel();
  });

  refreshDocsBtn.addEventListener("click", fetchHealthAndDocuments);

  // Sample Query Chips
  document.querySelectorAll(".chip").forEach((chip) => {
    chip.addEventListener("click", () => {
      const sampleText = chip.getAttribute("data-query");
      queryInput.value = sampleText;
      handleSendMessage();
    });
  });

  // --- Helpers ---
  function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text || "";
    return div.innerHTML;
  }

  function formatMarkdown(text) {
    if (!text) return "";
    let html = escapeHtml(text);
    // Bold
    html = html.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
    // Italic
    html = html.replace(/\*(.*?)\*/g, "<em>$1</em>");
    // Blockquote
    html = html.replace(/^&gt; (.*$)/gm, "<blockquote>$1</blockquote>");
    // Code block
    html = html.replace(/`(.*?)`/g, "<code>$1</code>");
    return html;
  }

  // Initial Data Load
  fetchHealthAndDocuments();
});
