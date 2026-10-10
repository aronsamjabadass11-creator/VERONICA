"""
Voice module for VERONICA.
Provides Neural Text-To-Speech (TTS), Speech-To-Text (STT), and interactive Voice Mode.
"""

from .text_to_speech import (
    TextToSpeech,
    get_tts_engine,
    BaseTTSProvider,
    EdgeTTSProvider,
    Pyttsx3TTSProvider,
)
from .speech_to_text import (
    SpeechToText,
    get_stt_engine,
    BaseSTTProvider,
    GoogleSTTProvider,
)
from .voice_mode import run_voice_mode, is_voice_exit_phrase

__all__ = [
    "TextToSpeech",
    "get_tts_engine",
    "BaseTTSProvider",
    "EdgeTTSProvider",
    "Pyttsx3TTSProvider",
    "SpeechToText",
    "get_stt_engine",
    "BaseSTTProvider",
    "GoogleSTTProvider",
    "run_voice_mode",
    "is_voice_exit_phrase",
]
