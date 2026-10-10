import sys
from typing import Callable, Optional
from config.logging_config import logger
from voice.speech_to_text import get_stt_engine
from voice.text_to_speech import get_tts_engine

# Ensure UTF-8 stdout on Windows terminals
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Phrases that trigger exit from voice mode back to text mode
VOICE_EXIT_COMMANDS = ("exit", "stop", "goodbye", "quit", "cancel")


def is_voice_exit_phrase(phrase: str) -> bool:
    """Checks if recognized speech contains an exit or stop keyword."""
    clean = phrase.lower().strip().rstrip(".!?,")
    words = clean.split()

    # Conversational phrases with more than 4 words should not be treated as simple exit commands
    if len(words) > 4:
        return False

    for cmd in VOICE_EXIT_COMMANDS:
        if clean == cmd or clean.startswith(f"{cmd} ") or clean.endswith(f" {cmd}") or f"please {cmd}" in clean:
            return True
    return False


def run_voice_mode(
    assistant,
    on_turn_callback: Optional[Callable[[str, str], None]] = None,
):
    """
    Runs the continuous voice interaction loop until the user says an exit word
    or issues a keyboard interrupt.
    """
    stt = get_stt_engine()
    tts = get_tts_engine()

    # Pre-flight check: ensure microphone is functional
    if not stt.is_microphone_available():
        print("\n[Voice Mode Error]: Microphone is unavailable or not detected.")
        print("Please verify your microphone settings or use terminal text mode.\n")
        return

    # Enable TTS for voice mode so answers are spoken
    tts.set_enabled(True)

    print("\n" + "-" * 45)
    print("VERONICA: Voice mode enabled.")
    print("Speak clearly into your microphone.")
    print("Say 'exit', 'stop', or 'goodbye' (or press Ctrl+C) to return to text mode.")
    print("-" * 45 + "\n")

    # Spoken welcome to voice mode
    tts.speak("Voice mode enabled. I am listening.")

    consecutive_timeouts = 0

    while True:
        try:
            print("VERONICA: Listening...", end="\r", flush=True)

            success, speech_text = stt.listen(timeout=6, phrase_time_limit=15)

            # Clear the listening prompt
            print(" " * 35, end="\r")

            if not success:
                # Handle timeout or no speech
                consecutive_timeouts += 1
                if consecutive_timeouts >= 5:
                    print("VERONICA: No speech detected for a while. Returning to text mode.")
                    tts.speak("Returning to text mode.")
                    break
                continue

            consecutive_timeouts = 0
            clean_text = speech_text.strip()
            print(f"You: {clean_text}")

            # Check for exit phrases spoken by user
            if is_voice_exit_phrase(clean_text):
                exit_msg = "Returning to terminal mode."
                print(f"VERONICA: {exit_msg}\n")
                tts.speak(exit_msg)
                break

              # Process input turn via assistant
            def status_callback(msg: str):
                print(f"[{msg}]", end="\r", flush=True)

                # Speak only important agent actions
                if msg.startswith("Using tool"):
                    tool_name = msg.replace("Using tool [", "").replace("]...", "")
                    tts.speak(f"Using {tool_name}.")
                elif msg == "Synthesizing final response...":
                    tts.speak("I found the information. Let me prepare the answer.")

            reply = assistant.process_input(
                clean_text,
                on_status_update=status_callback
            )

            # Clear status line
            print(" " * 45, end="\r")
            clean_reply = reply.replace("\u202f", " ").replace("\xa0", " ")
            print(f"VERONICA: {clean_reply}\n")

            # Spoken response
            tts.speak(clean_reply)

            if on_turn_callback:
                on_turn_callback(clean_text, reply)

        except KeyboardInterrupt:
            print("\n\nVERONICA: Voice mode interrupted. Returning to text mode.\n")
            tts.speak("Returning to text mode.")
            break
        except Exception as e:
            print(f"\n[Voice Mode Error]: {e}\n")
            logger.error(f"Error during voice mode loop: {e}")
            break

    print("VERONICA: Returned to text mode.\n")
