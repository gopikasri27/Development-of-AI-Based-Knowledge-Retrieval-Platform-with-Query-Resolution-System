/**
 * Web Speech API Voice Recognition Controller (M3.3)
 * Provides modular speech-to-text recognition with controls, callbacks, structured debug logs, and error handling.
 */

class VoiceInputController {
  constructor(options = {}) {
    this.onStart = options.onStart || (() => {});
    this.onResult = options.onResult || (() => {});
    this.onError = options.onError || (() => {});
    this.onEnd = options.onEnd || (() => {});
    this.lang = options.lang || (navigator.language ? navigator.language : 'en-US');

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
        console.log('[VOICE] Recognition started');
        console.log('[VOICE] Listening...');
        this.isListening = true;
        this.onStart();
      };

      this.recognition.onresult = (event) => {
        let transcript = '';
        let isFinal = false;

        for (let i = 0; i < event.results.length; ++i) {
          transcript += event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            isFinal = true;
          }
        }

        const cleanTranscript = transcript.trim();
        console.log('[VOICE] Speech result received');
        console.log('[VOICE] Transcript:', cleanTranscript);
        this.onResult(cleanTranscript, isFinal);
      };

      this.recognition.onerror = (event) => {
        console.error('[VOICE] Error:', event.error);
        let errorMsg = 'Speech recognition error occurred.';
        if (event.error === 'not-allowed' || event.error === 'service-not-allowed') {
          errorMsg = 'Microphone permission was denied. Please allow microphone access in your browser settings.';
        } else if (event.error === 'no-speech') {
          errorMsg = 'No speech detected. Please speak into your microphone and try again.';
        } else if (event.error === 'audio-capture') {
          errorMsg = 'No microphone was found on your system. Please connect a microphone.';
        } else if (event.error === 'network') {
          errorMsg = 'Network error during speech recognition.';
        } else if (event.error === 'aborted') {
          errorMsg = 'Speech recognition was stopped.';
        }

        this.onError(event.error, errorMsg);
        this.stop();
      };

      this.recognition.onend = () => {
        console.log('[VOICE] Recognition ended');
        this.isListening = false;
        this.onEnd();
      };
    } else {
      this.supported = false;
      console.warn('[VOICE] Error: Web Speech API (SpeechRecognition) is not supported in this browser.');
    }
  }

  start() {
    console.log('[VOICE] Speech recognition starting');
    if (!this.supported) {
      console.error('[VOICE] Error: browser not supported');
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
      console.error('[VOICE] Failed to start speech recognition:', e);
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
