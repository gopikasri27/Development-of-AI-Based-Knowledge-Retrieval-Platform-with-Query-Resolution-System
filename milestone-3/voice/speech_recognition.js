/**
 * Web Speech API Voice Recognition Controller (M3.3)
 * Provides modular speech-to-text recognition with controls, callbacks, and error handling.
 */

class VoiceInputController {
  constructor(options = {}) {
    this.onStart = options.onStart || (() => {});
    this.onResult = options.onResult || (() => {});
    this.onError = options.onError || (() => {});
    this.onEnd = options.onEnd || (() => {});
    this.lang = options.lang || 'en-US';

    this.recognition = null;
    this.isListening = false;
    this.supported = false;

    this.init();
  }

  init() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      this.supported = true;
      this.recognition = new SpeechRecognition();
      this.recognition.continuous = false;
      this.recognition.interimResults = true;
      this.recognition.lang = this.lang;

      this.recognition.onstart = () => {
        this.isListening = true;
        this.onStart();
      };

      this.recognition.onresult = (event) => {
        let transcript = '';
        let isFinal = false;

        for (let i = event.resultIndex; i < event.results.length; ++i) {
          transcript += event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            isFinal = true;
          }
        }
        this.onResult(transcript.trim(), isFinal);
      };

      this.recognition.onerror = (event) => {
        console.warn('Speech recognition error:', event.error);
        let errorMsg = 'Speech recognition error occurred.';
        if (event.error === 'not-allowed' || event.error === 'service-not-allowed') {
          errorMsg = 'Microphone permission was denied. Please allow microphone access in your browser settings.';
        } else if (event.error === 'no-speech') {
          errorMsg = 'No speech detected. Please try speaking again.';
        } else if (event.error === 'network') {
          errorMsg = 'Network error during speech recognition.';
        }
        this.onError(event.error, errorMsg);
        this.stop();
      };

      this.recognition.onend = () => {
        this.isListening = false;
        this.onEnd();
      };
    } else {
      this.supported = false;
      console.warn('Web Speech API (SpeechRecognition) is not supported in this browser.');
    }
  }

  start() {
    if (!this.supported) {
      this.onError('unsupported', 'Voice recognition is not supported in your browser. Please use Chrome or Edge.');
      return false;
    }
    if (this.isListening) {
      this.stop();
    }
    try {
      this.recognition.start();
      return true;
    } catch (e) {
      console.error('Failed to start speech recognition:', e);
      this.onError('start_failed', e.message);
      return false;
    }
  }

  stop() {
    if (this.recognition && this.isListening) {
      try {
        this.recognition.stop();
      } catch (e) {}
      this.isListening = false;
    }
  }

  restart() {
    this.stop();
    setTimeout(() => this.start(), 200);
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { VoiceInputController };
}
