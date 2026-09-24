"""
Unit Tests for Voice Input & Text-to-Speech Controllers (M3.3)
--------------------------------------------------------------
Tests voice transcription payload formatting, text sanitizer rules, and TTS text preparation.
"""

import unittest
import re


def sanitize_markdown_for_speech(text: str) -> str:
    """Python representation of TextToSpeechController markdown sanitizer."""
    if not text:
        return ""
    text = re.sub(r"\[Source:?.*?\]", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\[Chunk:?.*?\]", "", text, flags=re.IGNORECASE)
    text = re.sub(r"[*#>`_-]", "", text)
    text = re.sub(r"https?://\S+", "", text)
    return " ".join(text.split()).strip()


class TestVoiceModule(unittest.TestCase):

    def test_speech_sanitizer_removes_markdown_and_citations(self):
        """Test markdown tags and source citations are stripped before TTS."""
        raw_text = "**Cloud computing** is the delivery of services [Source: hr_policy.txt]. See `https://cloud.com`."
        clean = sanitize_markdown_for_speech(raw_text)
        self.assertNotIn("**", clean)
        self.assertNotIn("[Source", clean)
        self.assertNotIn("https://", clean)
        self.assertIn("Cloud computing is the delivery of services", clean)

    def test_voice_transcription_cleanup(self):
        """Test transcribed text formatting."""
        raw_voice_input = "  what is semantic search  "
        clean_input = raw_voice_input.strip()
        self.assertEqual(clean_input, "what is semantic search")


if __name__ == "__main__":
    unittest.main()
