/**
 * Web Speech API Voice Recognition Controller (M3.3)
 * Provides modular speech-to-text recognition with explicit getUserMedia permission acquisition,
 * structured console debug logs, and robust error handling.
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
          errorMsg = 'Microphone permission was denied. Please click the lock/camera icon in your address bar and allow microphone access.';
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

  async start() {
    console.log('[VOICE] Speech recognition starting');
    if (!this.supported) {
      console.error('[VOICE] Error: browser not supported');
      this.onError('unsupported', 'Voice recognition is not supported in your browser. Please use Chrome or Edge.');
      return false;
    }

    if (this.isListening) {
      this.stop();
      return true;
    }

    // Step 1: Pre-flight explicit microphone permission request via getUserMedia
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
      try {
        console.log('[VOICE] Requesting microphone stream permission via getUserMedia...');
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        console.log('[VOICE] Microphone permission granted by browser');
        // Stop temporary stream tracks so microphone device is released for SpeechRecognition engine
        stream.getTracks().forEach((track) => track.stop());
      } catch (err) {
        console.error('[VOICE] Microphone permission error via getUserMedia:', err);
        if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
          this.onError('not-allowed', 'Microphone permission was denied. Please click the lock/camera icon in the address bar and allow microphone access.');
          return false;
        } else if (err.name === 'NotFoundError' || err.name === 'DevicesNotFoundError') {
          this.onError('audio-capture', 'No microphone hardware found on your system.');
          return false;
        }
      }
    }

    // Step 2: Start Web Speech API SpeechRecognition
    try {
      this.recognition.start();
      return true;
    } catch (e) {
      if (e.name === 'InvalidStateError') {
        console.warn('[VOICE] SpeechRecognition is already active or in starting state');
      } else {
        console.error('[VOICE] Failed to start speech recognition:', e);
        this.onError('start_failed', e.message);
      }
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
