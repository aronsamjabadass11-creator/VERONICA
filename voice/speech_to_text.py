"""
speech_to_text.py - Modular Speech-To-Text engine for VERONICA.
Captures microphone audio and transcribes speech using SpeechRecognition and sounddevice.
Designed for high resilience with graceful fallbacks and error handling.
"""

import time
from abc import ABC, abstractmethod
from typing import Optional, Tuple, List
from config.settings import settings
from config.logging_config import logger


class BaseSTTProvider(ABC):
    """Abstract base class for modular speech recognition providers."""

    @abstractmethod
    def transcribe(self, audio_data) -> Tuple[bool, str]:
        """Transcribes AudioData into text. Returns (success, text_or_error)."""
        pass


class GoogleSTTProvider(BaseSTTProvider):
    """Google Web Speech API transcription provider via SpeechRecognition."""

    def __init__(self):
        self._recognizer = None
        self._init_recognizer()

    def _init_recognizer(self):
        try:
            import speech_recognition as sr
            self._recognizer = sr.Recognizer()
        except ImportError:
            self._recognizer = None

    def transcribe(self, audio_data) -> Tuple[bool, str]:
        if self._recognizer is None:
            return False, "SpeechRecognition package not available."

        try:
            import speech_recognition as sr
            text = self._recognizer.recognize_google(audio_data)
            return True, text.strip()
        except sr.UnknownValueError:
            return False, "Could not understand audio. Please speak clearly."
        except sr.RequestError as e:
            logger.error(f"Speech recognition service error: {e}")
            return False, f"Speech recognition service error: {e}"
        except Exception as e:
            logger.error(f"Unexpected error in STT transcription: {e}")
            return False, f"Transcription error: {e}"


class SpeechToText:
    """Manages microphone audio capture and coordinates STT transcription."""

    def __init__(self, provider: Optional[BaseSTTProvider] = None):
        self.enabled = settings.STT_ENABLED
        self.provider = provider or GoogleSTTProvider()

    def is_microphone_available(self) -> bool:
        """Checks if a functional microphone input device is connected."""
        try:
            import sounddevice as sd
            in_devices = [d for d in sd.query_devices() if d.get("max_input_channels", 0) > 0]
            return len(in_devices) > 0
        except Exception as e:
            logger.warning(f"Error querying microphone devices: {e}")
            return False

    def list_microphones(self) -> List[str]:
        """Returns names of available input microphone devices."""
        try:
            import sounddevice as sd
            return [
                d["name"] for d in sd.query_devices()
                if d.get("max_input_channels", 0) > 0
            ]
        except Exception:
            return []

    def _record_audio(
        self,
        timeout: int = settings.STT_TIMEOUT,
        phrase_time_limit: int = settings.STT_PHRASE_LIMIT,
    ) -> Tuple[bool, Optional[bytes], int]:
        """
        Records speech from microphone using sounddevice RawInputStream.
        Performs energy-based voice activity and silence detection.
        Returns (success: bool, raw_pcm_bytes, sample_rate).
        """
        try:
            import sounddevice as sd
            try:
                import audioop
            except ImportError:
                import audioop_lts as audioop
        except ImportError as ie:
            return False, None, 0

        sample_rate = 16000
        chunk_duration = 0.05  # 50ms chunks
        chunk_samples = int(sample_rate * chunk_duration)
        chunk_bytes_len = chunk_samples * 2  # 16-bit PCM

        try:
            stream = sd.RawInputStream(
                samplerate=sample_rate,
                channels=1,
                dtype="int16",
                blocksize=chunk_samples,
            )
            stream.start()
        except Exception as e:
            logger.error(f"Failed to open microphone audio stream: {e}")
            return False, None, 0

        # Calibrate ambient noise for ~0.3 seconds
        ambient_energies = []
        for _ in range(6):
            chunk, _ = stream.read(chunk_samples)
            rms = audioop.rms(chunk, 2)
            ambient_energies.append(rms)

        ambient_base = sum(ambient_energies) / max(1, len(ambient_energies))
        energy_threshold = max(350, int(ambient_base * 1.6))
        silence_threshold = max(250, int(ambient_base * 1.2))

        recorded_chunks: List[bytes] = []
        started_speaking = False
        silence_start_time: Optional[float] = None
        start_wait_time = time.time()
        speaking_start_time: Optional[float] = None

        try:
            while True:
                chunk, overflow = stream.read(chunk_samples)
                rms = audioop.rms(chunk, 2)
                now = time.time()

                if not started_speaking:
                    # Waiting for user to begin speaking
                    if rms > energy_threshold:
                        started_speaking = True
                        speaking_start_time = now
                        recorded_chunks.append(bytes(chunk))
                    elif (now - start_wait_time) > timeout:
                        # Timeout before speaking
                        return False, None, sample_rate
                else:
                    # User is actively speaking or paused
                    recorded_chunks.append(bytes(chunk))

                    # Check overall phrase time limit
                    if speaking_start_time and (now - speaking_start_time) > phrase_time_limit:
                        break

                    # Check silence detection
                    if rms < silence_threshold:
                        if silence_start_time is None:
                            silence_start_time = now
                        elif (now - silence_start_time) >= 1.1:  # 1.1 seconds of silence ends speech
                            break
                    else:
                        silence_start_time = None

        finally:
            try:
                stream.stop()
                stream.close()
            except Exception:
                pass

        if not recorded_chunks:
            return False, None, sample_rate

        all_pcm = b"".join(recorded_chunks)
        return True, all_pcm, sample_rate

    def listen(
        self,
        timeout: int = settings.STT_TIMEOUT,
        phrase_time_limit: int = settings.STT_PHRASE_LIMIT,
    ) -> Tuple[bool, str]:
        """
        Listens to the microphone, records speech, and converts it to text.
        Returns (success: bool, text_or_error_message: str).
        """
        if not self.is_microphone_available():
            return False, "Microphone is not detected or audio input is unavailable."

        try:
            import speech_recognition as sr
        except ImportError:
            return False, "SpeechRecognition package is not installed."

        success, pcm_data, sample_rate = self._record_audio(
            timeout=timeout,
            phrase_time_limit=phrase_time_limit,
        )

        if not success or not pcm_data:
            return False, "No speech detected (timeout)."

        try:
            # Wrap PCM bytes into SpeechRecognition AudioData
            audio = sr.AudioData(pcm_data, sample_rate, 2)
            return self.provider.transcribe(audio)
        except Exception as e:
            logger.error(f"Error processing audio data: {e}")
            return False, f"Speech processing error: {e}"

    def get_status(self) -> str:
        """Returns readable status of the microphone / STT subsystem."""
        if not self.is_microphone_available():
            return "ERROR (Microphone unavailable)"
        return "READY"


# Global singleton instance
_stt_instance: Optional[SpeechToText] = None


def get_stt_engine() -> SpeechToText:
    """Returns the singleton SpeechToText instance."""
    global _stt_instance
    if _stt_instance is None:
        _stt_instance = SpeechToText()
    return _stt_instance
