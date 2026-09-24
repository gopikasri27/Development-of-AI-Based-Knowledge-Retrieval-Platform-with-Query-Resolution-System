/**
 * Web Speech API Text-to-Speech Synthesis Controller (M3.3)
 * Provides speech output synthesis with Speak, Pause, Resume, and Stop controls.
 */

class TextToSpeechController {
  constructor(options = {}) {
    this.rate = options.rate || 1.0;
    this.pitch = options.pitch || 1.0;
    this.lang = options.lang || 'en-US';
    this.onStart = options.onStart || (() => {});
    this.onEnd = options.onEnd || (() => {});
    this.onError = options.onError || (() => {});
    this.onPause = options.onPause || (() => {});
    this.onResume = options.onResume || (() => {});

    this.synth = window.speechSynthesis || null;
    this.currentUtterance = null;
    this.supported = !!this.synth;
  }

  speak(text) {
    if (!this.supported) {
      this.onError('unsupported', 'Text-to-Speech is not supported in this browser.');
      return false;
    }

    this.stop(); // Stop any ongoing speech

    const cleanText = this.sanitizeMarkdown(text);
    if (!cleanText) return false;

    this.currentUtterance = new SpeechSynthesisUtterance(cleanText);
    this.currentUtterance.rate = this.rate;
    this.currentUtterance.pitch = this.pitch;
    this.currentUtterance.lang = this.lang;

    this.currentUtterance.onstart = () => this.onStart();
    this.currentUtterance.onend = () => this.onEnd();
    this.currentUtterance.onpause = () => this.onPause();
    this.currentUtterance.onresume = () => this.onResume();
    this.currentUtterance.onerror = (e) => this.onError('synthesis_error', e.error);

    try {
      this.synth.speak(this.currentUtterance);
      return true;
    } catch (e) {
      this.onError('speak_exception', e.message);
      return false;
    }
  }

  pause() {
    if (this.synth && this.synth.speaking && !this.synth.paused) {
      this.synth.pause();
    }
  }

  resume() {
    if (this.synth && this.synth.paused) {
      this.synth.resume();
    }
  }

  stop() {
    if (this.synth) {
      this.synth.cancel();
    }
  }

  isSpeaking() {
    return this.synth ? this.synth.speaking : false;
  }

  isPaused() {
    return this.synth ? this.synth.paused : false;
  }

  sanitizeMarkdown(text) {
    if (!text) return '';
    return text
      .replace(/\[Source:?.*?\]/gi, '')
      .replace(/\[Chunk:?.*?\]/gi, '')
      .replace(/[*#>`_-]/g, '')
      .replace(/https?:\/\/\S+/g, '')
      .replace(/\s+/g, ' ')
      .trim();
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { TextToSpeechController };
}
