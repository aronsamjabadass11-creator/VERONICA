"""
text_to_speech.py - Neural Text-To-Speech engine for VERONICA powered by edge-tts.
Uses Microsoft Edge Neural voices (default: en-US-AriaNeural) for a warm, natural female assistant personality.
Provides runtime controls for voice switching, speed, pitch, automatic playback, and error handling.
"""

import os
import sys
import uuid
import ctypes
import asyncio
from abc import ABC, abstractmethod
from typing import Optional, Tuple, List, Dict
from config.settings import settings, AVAILABLE_VOICES, VOICE_DETAILS
from config.logging_config import logger


class BaseTTSProvider(ABC):
    """Abstract base class for TTS providers."""

    @abstractmethod
    def speak(self, text: str) -> bool:
        """Converts text to speech and plays through default audio output."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Returns True if the provider is initialized and ready."""
        pass


def _play_audio_windows(filepath: str) -> bool:
    """
    Plays an audio file on Windows using the native winmm mciSendString API.
    Does not require external audio dependencies or media players.
    Blocks until playback is complete.
    """
    abs_path = os.path.abspath(filepath)
    if not os.path.exists(abs_path):
        return False

    if sys.platform != "win32":
        return False

    winmm = ctypes.windll.winmm
    alias = f"veronica_{uuid.uuid4().hex[:8]}"

    try:
        # Close any lingering alias
        winmm.mciSendStringW(f"close {alias}", None, 0, None)

        # Open media file
        open_cmd = f'open "{abs_path}" type mpegvideo alias {alias}'
        res_open = winmm.mciSendStringW(open_cmd, None, 0, None)
        if res_open != 0:
            logger.warning(f"winmm open failed with code: {res_open}")
            return False

        # Play synchronously ('wait' flag blocks until playback finishes)
        play_cmd = f"play {alias} wait"
        res_play = winmm.mciSendStringW(play_cmd, None, 0, None)

        # Close media alias
        winmm.mciSendStringW(f"close {alias}", None, 0, None)
        return res_play == 0

    except Exception as e:
        logger.error(f"Error during winmm audio playback: {e}")
        try:
            winmm.mciSendStringW(f"close {alias}", None, 0, None)
        except Exception:
            pass
        return False


class EdgeTTSProvider(BaseTTSProvider):
    """
    Neural TTS Provider using Microsoft Edge Neural TTS (edge-tts).
    Produces natural, studio-quality speech with female neural models.
    Supports dynamic adjustments to voice, speaking speed, and pitch.
    """

    def __init__(
        self,
        voice: Optional[str] = None,
        rate: Optional[str] = None,
        pitch: Optional[str] = None,
        volume: Optional[str] = None,
    ):
        self.voice = voice or settings.TTS_VOICE
        self.rate = rate or settings.TTS_SPEED
        self.pitch = pitch or settings.TTS_PITCH
        self.volume = volume or settings.TTS_VOLUME
        self.temp_dir = settings.DATA_DIR / "temp_audio"
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self._check_installed()

    def _check_installed(self) -> bool:
        try:
            import edge_tts
            return True
        except ImportError:
            logger.warning("edge-tts package is not installed.")
            return False

    def is_available(self) -> bool:
        return self._check_installed()

    def set_voice(self, voice_id: str):
        """Updates the active voice model."""
        self.voice = voice_id

    def set_speed(self, rate_str: str):
        """Updates the speaking speed (e.g. '+5%', '-10%')."""
        self.rate = rate_str

    def set_pitch(self, pitch_str: str):
        """Updates the voice pitch (e.g. '+5Hz', '-2Hz')."""
        self.pitch = pitch_str

    async def _synthesize(self, text: str, output_path: str):
        """Asynchronously synthesizes speech to an MP3 file."""
        import edge_tts
        communicate = edge_tts.Communicate(
            text=text,
            voice=self.voice,
            rate=self.rate,
            pitch=self.pitch,
            volume=self.volume,
        )
        await communicate.save(output_path)

    def speak(self, text: str) -> bool:
        """
        Synthesizes text with edge-tts, plays via Windows winmm, and deletes temp file.
        """
        if not text or not text.strip():
            return False

        temp_file = self.temp_dir / f"veronica_{uuid.uuid4().hex}.mp3"
        temp_path = str(temp_file.resolve())

        try:
            # Clean text formatting for neural pronunciation
            speech_text = (
                text.replace("*", "")
                .replace("#", "")
                .replace("`", "")
                .replace("_", "")
                .replace("\u202f", " ")
                .replace("\xa0", " ")
                .strip()
            )

            # Synthesize audio file via edge-tts
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                        pool.submit(asyncio.run, self._synthesize(speech_text, temp_path)).result(timeout=15)
                else:
                    loop.run_until_complete(self._synthesize(speech_text, temp_path))
            except RuntimeError:
                asyncio.run(self._synthesize(speech_text, temp_path))

            # Automatically play audio
            played = _play_audio_windows(temp_path)
            return played

        except Exception as e:
            logger.error(f"EdgeTTS synthesis/playback error: {e}")
            return False

        finally:
            # Clean up temporary audio file safely
            try:
                if temp_file.exists():
                    temp_file.unlink(missing_ok=True)
            except Exception as e:
                logger.debug(f"Could not remove temp audio file {temp_file}: {e}")


class Pyttsx3TTSProvider(BaseTTSProvider):
    """Fallback local offline TTS provider using pyttsx3."""

    def __init__(self):
        self.engine = None
        self._init_engine()

    def _init_engine(self):
        try:
            import pyttsx3
            self.engine = pyttsx3.init()
            self.engine.setProperty("rate", settings.VOICE_RATE)
        except Exception:
            self.engine = None

    def is_available(self) -> bool:
        return self.engine is not None

    def speak(self, text: str) -> bool:
        if not self.is_available():
            return False
        try:
            clean_text = text.replace("*", "").replace("#", "").replace("`", "")
            self.engine.say(clean_text)
            self.engine.runAndWait()
            return True
        except Exception as e:
            logger.warning(f"pyttsx3 fallback error: {e}")
            return False


class TextToSpeech:
    """
    High-level TTS manager for VERONICA.
    Controls female neural voices (Aria, Jenny, Neerja, Ava), speaking speed, and pitch.
    Prioritizes Edge Neural TTS with graceful pyttsx3 offline fallback.
    """

    def __init__(self, provider: Optional[BaseTTSProvider] = None):
        self.enabled = settings.TTS_ENABLED
        self.primary_provider = provider or EdgeTTSProvider()
        self.fallback_provider = Pyttsx3TTSProvider()

    @property
    def current_voice(self) -> str:
        """Returns the current voice identifier."""
        if hasattr(self.primary_provider, "voice"):
            return self.primary_provider.voice
        return settings.TTS_VOICE

    @property
    def current_speed(self) -> str:
        """Returns the current speaking speed."""
        if hasattr(self.primary_provider, "rate"):
            return self.primary_provider.rate
        return settings.TTS_SPEED

    @property
    def current_pitch(self) -> str:
        """Returns the current voice pitch."""
        if hasattr(self.primary_provider, "pitch"):
            return self.primary_provider.pitch
        return settings.TTS_PITCH

    def is_available(self) -> bool:
        """Returns True if any TTS provider is available."""
        return self.primary_provider.is_available() or self.fallback_provider.is_available()

    def is_speaker_available(self) -> bool:
        """Checks if speaker output hardware is ready."""
        try:
            import sounddevice as sd
            out_devices = [d for d in sd.query_devices() if d.get("max_output_channels", 0) > 0]
            return len(out_devices) > 0 and self.is_available()
        except Exception:
            return self.is_available()

    def set_voice(self, voice_name_or_key: str) -> Tuple[bool, str]:
        """
        Sets the active voice using either shorthand key ('aria', 'jenny', etc.)
        or exact model name ('en-US-AriaNeural').
        """
        target = voice_name_or_key.strip().lower()

        # Check in shorthand keys
        if target in AVAILABLE_VOICES:
            full_id = AVAILABLE_VOICES[target]
            detail = VOICE_DETAILS.get(target, {})
            name = detail.get("name", target.title())
        else:
            # Check if an exact full voice ID was provided
            matched = False
            for k, v in AVAILABLE_VOICES.items():
                if v.lower() == target:
                    full_id = v
                    name = VOICE_DETAILS[k]["name"]
                    matched = True
                    break
            if not matched:
                valid_options = ", ".join(AVAILABLE_VOICES.keys())
                return False, f"Unknown voice '{voice_name_or_key}'. Available voices: {valid_options}"

        if hasattr(self.primary_provider, "set_voice"):
            self.primary_provider.set_voice(full_id)
        settings.TTS_VOICE = full_id
        logger.info(f"VERONICA voice updated to '{name}' ({full_id})")
        return True, f"{name} ({full_id})"

    def set_speed(self, speed_input: str) -> Tuple[bool, str]:
        """
        Sets the speaking speed.
        Accepts values like '+10%', '-5%', '+0%', '10', '-10'.
        """
        clean = speed_input.strip()
        if not clean:
            return False, "Speed value cannot be empty."

        # Auto-format numeric inputs
        if clean.replace("+", "").replace("-", "").isdigit():
            sign = "+" if not clean.startswith("-") else ""
            clean = f"{sign}{clean}%"
        elif not clean.endswith("%"):
            clean = f"{clean}%"

        if hasattr(self.primary_provider, "set_speed"):
            self.primary_provider.set_speed(clean)
        settings.TTS_SPEED = clean
        logger.info(f"VERONICA speaking speed updated to {clean}")
        return True, clean

    def set_pitch(self, pitch_input: str) -> Tuple[bool, str]:
        """
        Sets the voice pitch.
        Accepts values like '+5Hz', '-2Hz', '+0Hz', '5', '-5'.
        """
        clean = pitch_input.strip()
        if not clean:
            return False, "Pitch value cannot be empty."

        # Auto-format numeric inputs
        if clean.replace("+", "").replace("-", "").isdigit():
            sign = "+" if not clean.startswith("-") else ""
            clean = f"{sign}{clean}Hz"
        elif not (clean.endswith("Hz") or clean.endswith("%")):
            clean = f"{clean}Hz"

        if hasattr(self.primary_provider, "set_pitch"):
            self.primary_provider.set_pitch(clean)
        settings.TTS_PITCH = clean
        logger.info(f"VERONICA voice pitch updated to {clean}")
        return True, clean

    def get_available_voices_list(self) -> List[Dict[str, str]]:
        """Returns details of all configured female neural voices."""
        items = []
        for key, details in VOICE_DETAILS.items():
            items.append({
                "key": key,
                "name": details["name"],
                "desc": details["desc"],
                "id": details["id"],
                "is_active": (details["id"] == self.current_voice),
            })
        return items

    def speak(self, text: str) -> bool:
        """
        Speaks text using the neural voice. If Edge-TTS fails or is offline,
        gracefully attempts fallback without interrupting terminal execution.
        """
        if not self.enabled or not text.strip():
            return False

        # Try Edge Neural TTS
        if self.primary_provider.is_available():
            success = self.primary_provider.speak(text)
            if success:
                return True
            logger.info("Primary EdgeTTS failed. Attempting offline fallback.")

        # Try offline pyttsx3 fallback
        if self.fallback_provider.is_available():
            return self.fallback_provider.speak(text)

        logger.warning("No TTS providers succeeded in speaking text.")
        return False

    def test_voice(self) -> bool:
        """
        Plays the required verification voice prompt:
        'Hello, I am VERONICA. My voice system is working perfectly.'
        """
        test_phrase = "Hello, I am VERONICA. My voice system is working perfectly."
        print(f'VERONICA: "{test_phrase}"')
        was_enabled = self.enabled
        self.enabled = True
        try:
            return self.speak(test_phrase)
        finally:
            self.enabled = was_enabled

    def toggle(self) -> bool:
        """Toggles TTS enabled state."""
        self.enabled = not self.enabled
        return self.enabled

    def set_enabled(self, state: bool):
        """Sets TTS enabled state."""
        self.enabled = state

    def get_status(self) -> str:
        """Returns status string for TTS."""
        if not self.is_available():
            return "ERROR (TTS unavailable)"
        return "READY"


# Global singleton instance
_tts_instance: Optional[TextToSpeech] = None


def get_tts_engine() -> TextToSpeech:
    """Returns the singleton TextToSpeech instance."""
    global _tts_instance
    if _tts_instance is None:
        _tts_instance = TextToSpeech()
    return _tts_instance
