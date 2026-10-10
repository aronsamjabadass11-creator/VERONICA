"""
settings.py - Centralized configuration for VERONICA.
Loads environment variables from .env and defines runtime constants.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Base paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Load environment variables from .env located at project root
ENV_FILE = PROJECT_ROOT / ".env"
load_dotenv(dotenv_path=ENV_FILE)


# Available Female Neural Voices for VERONICA
AVAILABLE_VOICES: dict = {
    "aria": "en-US-AriaNeural",
    "jenny": "en-US-JennyNeural",
    "neerja": "en-IN-NeerjaNeural",
    "ava": "en-US-AvaNeural",
}

VOICE_DETAILS: dict = {
    "aria": {"name": "Aria", "desc": "US Female Assistant", "id": "en-US-AriaNeural"},
    "jenny": {"name": "Jenny", "desc": "Soft Female", "id": "en-US-JennyNeural"},
    "neerja": {"name": "Neerja", "desc": "Indian Female", "id": "en-IN-NeerjaNeural"},
    "ava": {"name": "Ava", "desc": "Modern Female", "id": "en-US-AvaNeural"},
}


class Settings:
    """Application configuration settings."""

    # Base paths
    PROJECT_ROOT: Path = PROJECT_ROOT
    DATA_DIR: Path = DATA_DIR

    # Project Information
    APP_NAME: str = "VERONICA"
    VERSION: str = "1.0.0"

    # API Keys & Provider
    # Note: Never hardcode or print this key!
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "").strip()

    # LLM Configuration
    # Primary model currently available on Groq Cloud
    DEFAULT_MODEL: str = "openai/gpt-oss-20b"
    MODEL_NAME: str = os.getenv("VERONICA_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL

    # Memory Configuration
    MEMORY_ENABLED: bool = os.getenv("VERONICA_MEMORY_ENABLED", "true").lower() in ("true", "1", "yes")
    MAX_HISTORY_MESSAGES: int = int(os.getenv("VERONICA_MAX_HISTORY", "20"))
    MEMORY_FILE: Path = DATA_DIR / "memory.json"

    # Voice & Neural TTS Configuration
    VOICE_ENABLED: bool = os.getenv("VERONICA_VOICE_ENABLED", "false").lower() in ("true", "1", "yes")
    TTS_ENABLED: bool = os.getenv("VERONICA_TTS_ENABLED", "true").lower() in ("true", "1", "yes")
    TTS_VOICE: str = os.getenv("VERONICA_TTS_VOICE", "en-US-AriaNeural").strip() or "en-US-AriaNeural"
    TTS_SPEED: str = os.getenv("VERONICA_TTS_SPEED", "+0%").strip() or "+0%"
    TTS_PITCH: str = os.getenv("VERONICA_TTS_PITCH", "+0Hz").strip() or "+0Hz"
    TTS_VOLUME: str = os.getenv("VERONICA_TTS_VOLUME", "+0%").strip() or "+0%"
    VOICE_RATE: int = int(os.getenv("VERONICA_VOICE_RATE", "180"))
    VOICE_ID: str = os.getenv("VERONICA_VOICE", "en-US-AriaNeural")
    STT_ENABLED: bool = os.getenv("VERONICA_STT_ENABLED", "true").lower() in ("true", "1", "yes")
    STT_TIMEOUT: int = int(os.getenv("VERONICA_STT_TIMEOUT", "5"))
    STT_PHRASE_LIMIT: int = int(os.getenv("VERONICA_STT_PHRASE_LIMIT", "15"))

    # Logging Configuration
    LOG_FILE: Path = DATA_DIR / "veronica.log"

    # System Prompt for VERONICA
    SYSTEM_PROMPT: str = (
        "You are VERONICA, a helpful personal AI assistant. "
        "You communicate clearly and naturally. "
        "You should understand the user's intent before responding. "
        "You should not claim to have performed an action unless it was actually performed. "
        "For actions involving files, commands, or external systems, use available tools rather than pretending."
    )

    @classmethod
    def is_api_key_set(cls) -> bool:
        """Check if GROQ_API_KEY is configured without exposing it."""
        return bool(cls.GROQ_API_KEY)


settings = Settings()
