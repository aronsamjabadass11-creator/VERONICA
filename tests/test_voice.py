"""
test_voice.py - Unit tests for VERONICA's voice subsystems and Neural Edge TTS.
Tests EdgeTTSProvider, voice selection (Aria, Jenny, Neerja, Ava), speed, pitch, and error handling.
Does not require physical microphone or speaker hardware to pass.
"""

import unittest
from voice.text_to_speech import (
    TextToSpeech,
    BaseTTSProvider,
    EdgeTTSProvider,
    Pyttsx3TTSProvider,
)
from voice.speech_to_text import SpeechToText, BaseSTTProvider, GoogleSTTProvider
from voice.voice_mode import is_voice_exit_phrase
from config.settings import settings, AVAILABLE_VOICES, VOICE_DETAILS


class MockTTSProvider(BaseTTSProvider):
    """Mock TTS provider for hardware-independent unit testing."""

    def __init__(self):
        self.spoken_texts = []
        self._available = True
        self.voice = settings.TTS_VOICE
        self.rate = settings.TTS_SPEED
        self.pitch = settings.TTS_PITCH

    def initialize(self) -> bool:
        return True

    def is_available(self) -> bool:
        return self._available

    def set_voice(self, voice_id: str):
        self.voice = voice_id

    def set_speed(self, rate_str: str):
        self.rate = rate_str

    def set_pitch(self, pitch_str: str):
        self.pitch = pitch_str

    def speak(self, text: str) -> bool:
        self.spoken_texts.append(text)
        return True


class MockSTTProvider(BaseSTTProvider):
    """Mock STT provider for hardware-independent unit testing."""

    def __init__(self, response_text="Hello VERONICA"):
        self.response_text = response_text

    def transcribe(self, audio_data):
        return True, self.response_text


class TestVoiceSystem(unittest.TestCase):
    """Unit tests for Voice subsystems."""

    def setUp(self):
        self.orig_voice = settings.TTS_VOICE
        self.orig_speed = settings.TTS_SPEED
        self.orig_pitch = settings.TTS_PITCH

    def tearDown(self):
        settings.TTS_VOICE = self.orig_voice
        settings.TTS_SPEED = self.orig_speed
        settings.TTS_PITCH = self.orig_pitch

    def test_voice_settings_defaults(self):
        """Verifies default neural voice settings and available voices."""
        self.assertIn("AriaNeural", self.orig_voice)
        self.assertIn("aria", AVAILABLE_VOICES)
        self.assertIn("jenny", AVAILABLE_VOICES)
        self.assertIn("neerja", AVAILABLE_VOICES)
        self.assertIn("ava", AVAILABLE_VOICES)

    def test_exit_phrase_detection(self):
        """Tests that exit words in speech are reliably recognized."""
        self.assertTrue(is_voice_exit_phrase("exit"))
        self.assertTrue(is_voice_exit_phrase("stop"))
        self.assertTrue(is_voice_exit_phrase("goodbye"))
        self.assertTrue(is_voice_exit_phrase("please stop"))
        self.assertTrue(is_voice_exit_phrase("goodbye veronica"))
        self.assertTrue(is_voice_exit_phrase("exit now"))
        self.assertTrue(is_voice_exit_phrase("quit"))

        # Non-exit phrases
        self.assertFalse(is_voice_exit_phrase("Hello VERONICA"))
        self.assertFalse(is_voice_exit_phrase("What is 10 plus 5?"))
        self.assertFalse(is_voice_exit_phrase("Do not stop listening to me"))

    def test_tts_initialization(self):
        """Tests TTS initialization with mock provider."""
        mock_provider = MockTTSProvider()
        tts = TextToSpeech(provider=mock_provider)
        self.assertTrue(tts.is_available())

        # Test speaking
        success = tts.speak("Test speech output")
        self.assertTrue(success)
        self.assertIn("Test speech output", mock_provider.spoken_texts)

    def test_tts_test_voice_phrase(self):
        """Verifies test_voice speaks exact required phrase."""
        mock_provider = MockTTSProvider()
        tts = TextToSpeech(provider=mock_provider)

        result = tts.test_voice()
        self.assertTrue(result)
        expected = "Hello, I am VERONICA. My voice system is working perfectly."
        self.assertTrue(any(expected in t for t in mock_provider.spoken_texts))

    def test_tts_voice_switching(self):
        """Tests switching between Aria, Jenny, Neerja, and Ava."""
        mock_provider = MockTTSProvider()
        tts = TextToSpeech(provider=mock_provider)

        # Switch to Jenny
        success, msg = tts.set_voice("jenny")
        self.assertTrue(success)
        self.assertEqual(tts.current_voice, "en-US-JennyNeural")

        # Switch to Neerja
        success, msg = tts.set_voice("neerja")
        self.assertTrue(success)
        self.assertEqual(tts.current_voice, "en-IN-NeerjaNeural")

        # Switch to Ava
        success, msg = tts.set_voice("ava")
        self.assertTrue(success)
        self.assertEqual(tts.current_voice, "en-US-AvaNeural")

        # Switch back to Aria
        success, msg = tts.set_voice("aria")
        self.assertTrue(success)
        self.assertEqual(tts.current_voice, "en-US-AriaNeural")

        # Invalid voice
        success, err = tts.set_voice("invalid_voice")
        self.assertFalse(success)

    def test_tts_speed_and_pitch_controls(self):
        """Tests adjusting speed and pitch."""
        mock_provider = MockTTSProvider()
        tts = TextToSpeech(provider=mock_provider)

        # Speed adjustment
        success, speed = tts.set_speed("+10%")
        self.assertTrue(success)
        self.assertEqual(tts.current_speed, "+10%")

        # Numeric speed auto-formatting
        success, speed = tts.set_speed("-5")
        self.assertTrue(success)
        self.assertEqual(tts.current_speed, "-5%")

        # Pitch adjustment
        success, pitch = tts.set_pitch("+5Hz")
        self.assertTrue(success)
        self.assertEqual(tts.current_pitch, "+5Hz")

        # Numeric pitch auto-formatting
        success, pitch = tts.set_pitch("2")
        self.assertTrue(success)
        self.assertEqual(tts.current_pitch, "+2Hz")

    def test_get_available_voices_list(self):
        """Verifies voice details list structure."""
        tts = TextToSpeech(provider=MockTTSProvider())
        voices = tts.get_available_voices_list()
        self.assertEqual(len(voices), 4)
        names = [v["name"] for v in voices]
        self.assertIn("Aria", names)
        self.assertIn("Jenny", names)
        self.assertIn("Neerja", names)
        self.assertIn("Ava", names)

    def test_tts_toggle_and_enable(self):
        """Tests toggling TTS on and off."""
        mock_provider = MockTTSProvider()
        tts = TextToSpeech(provider=mock_provider)

        tts.set_enabled(False)
        self.assertFalse(tts.enabled)
        # Speaking should do nothing when disabled
        tts.speak("Should not speak")
        self.assertEqual(len(mock_provider.spoken_texts), 0)

        # Toggle on
        tts.toggle()
        self.assertTrue(tts.enabled)

    def test_edge_tts_provider_initialization(self):
        """Verifies EdgeTTSProvider initializes and recognizes edge-tts package."""
        provider = EdgeTTSProvider()
        self.assertTrue(provider.is_available())
        self.assertIn("Neural", provider.voice)

    def test_stt_initialization(self):
        """Tests STT initialization and mock transcription."""
        mock_provider = MockSTTProvider("Mock transcription")
        stt = SpeechToText(provider=mock_provider)
        self.assertIsNotNone(stt)
        self.assertIsInstance(stt.get_status(), str)

    def test_stt_transcription_with_mock(self):
        """Verifies transcription logic using mock provider."""
        mock_provider = MockSTTProvider("Testing microphone")
        success, text = mock_provider.transcribe(None)
        self.assertTrue(success)
        self.assertEqual(text, "Testing microphone")

    def test_pyttsx3_provider_status(self):
        """Checks Pyttsx3 provider without crashing."""
        provider = Pyttsx3TTSProvider()
        self.assertIsInstance(provider.is_available(), bool)

    def test_google_stt_provider_status(self):
        """Checks GoogleSTTProvider instantiation."""
        provider = GoogleSTTProvider()
        self.assertIsNotNone(provider)


if __name__ == "__main__":
    unittest.main()
