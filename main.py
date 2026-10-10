"""
main.py - Entry point and terminal interface for VERONICA AI Assistant.

Supports:
- Terminal text chat
- Voice output
- Hands-free voice mode
- Memory
- Safe tools
- Multi-step Agent Mode
"""

import sys
import os

# Ensure UTF-8 output encoding on Windows terminals
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stdin.reconfigure(encoding="utf-8")
    except Exception:
        pass


from config.settings import settings, VOICE_DETAILS
from config.logging_config import logger

from core.assistant import VeronicaAssistant

from voice.text_to_speech import get_tts_engine
from voice.speech_to_text import get_stt_engine
from voice.voice_mode import run_voice_mode


# ============================================================
# STARTUP
# ============================================================

def print_banner(assistant: VeronicaAssistant):
    """Print startup banner and system status."""

    status = assistant.get_status()

    print("\n" + "=" * 40)
    print("        VERONICA AI ASSISTANT")
    print("=" * 40)

    print(f"AI ............ {status['ai']}")
    print(f"Groq .......... {status['groq']}")
    print(f"Memory ........ {status['memory']}")
    print(f"Voice ......... {status['voice']}")
    print(f"TTS ........... {status['tts']}")
    print(f"Voice Model ... {status['voice_model']}")
    print(f"Microphone .... {status['microphone']}")
    print(f"Speaker ....... {status['speaker']}")

    print("\nVERONICA is online.")
    print(
        "Type your message or use commands like "
        "/help, /agent, /voice live, or /exit.\n"
    )


# ============================================================
# STATUS
# ============================================================

def print_status(assistant: VeronicaAssistant):
    """Display detailed subsystem status."""

    status = assistant.get_status()

    print("\n--- System Status ---")

    print(f"AI ............ {status['ai']}")
    print(f"Groq .......... {status['groq']}")
    print(f"Model ......... {status['model']}")

    print(
        f"Memory ........ "
        f"{status['memory']} "
        f"({status['persistent_facts']} facts stored)"
    )

    print(f"Voice ......... {status['voice']}")
    print(f"TTS ........... {status['tts']}")
    print(f"Voice Model ... {status['voice_model']}")

    print(
        f"Speed ......... "
        f"{status.get('speed', '+0%')}"
    )

    print(
        f"Pitch ......... "
        f"{status.get('pitch', '+0Hz')}"
    )

    print(f"Microphone .... {status['microphone']}")
    print(f"Speaker ....... {status['speaker']}")

    print(
        f"Safe Tools .... "
        f"{len(status['tools_registered'])} registered"
    )

    print()


# ============================================================
# VOICE LIST
# ============================================================

def print_voice_list(tts):
    """Display available neural voices."""

    print("\nVERONICA voices:\n")

    for idx, (key, details) in enumerate(
        VOICE_DETAILS.items(),
        start=1
    ):

        is_active = (
            details["id"] == tts.current_voice
        )

        active_tag = (
            "  [ACTIVE]"
            if is_active
            else ""
        )

        print(
            f"  {idx}. "
            f"{details['name']} - "
            f"{details['desc']}"
            f"{active_tag}"
        )

    print(
        "\nUse '/voice set <name>' to change "
        "(e.g. '/voice set aria')\n"
    )


# ============================================================
# HELP
# ============================================================

def print_help():
    """Display available VERONICA commands."""

    print("\n--- Available Commands ---")

    print("  /help")
    print("      Show this help message")

    print("  /status")
    print("      Display full system status")

    print("  /agent <task>")
    print("      Run a multi-step autonomous task")

    print("  /voice list")
    print("      List available neural voices")

    print("  /voice set <name>")
    print("      Change active voice")

    print("  /voice speed <val>")
    print("      Change speaking speed")

    print("  /voice pitch <val>")
    print("      Change voice pitch")

    print("  /voice test")
    print("      Test VERONICA voice")

    print("  /voice on / off")
    print("      Enable or disable voice output")

    print("  /voice live")
    print("      Start hands-free voice mode")

    print("  /listen")
    print("      Listen once through microphone")

    print("  /clear")
    print("      Clear conversation history")

    print("  /memory")
    print("      View remembered facts")

    print("  /remember <fact>")
    print("      Remember a fact")

    print("  /forget <fact>")
    print("      Forget a fact")

    print("  /tools")
    print("      List registered safe tools")

    print("  /exit")
    print("      Shutdown VERONICA")

    print()


# ============================================================
# TOOLS
# ============================================================

def print_tools(assistant: VeronicaAssistant):
    """Display registered tools."""

    print("\n--- Registered Safe Tools ---")

    for name in assistant.tools.list_tools():

        tool = assistant.tools.get_tool(name)

        desc = (
            tool.description
            if tool
            else ""
        )

        print(
            f"  • {name:22} : {desc}"
        )

    print()


# ============================================================
# AGENT MODE
# ============================================================

def run_agent_command(
    goal: str,
    assistant: VeronicaAssistant
):
    """
    Run VERONICA's multi-step agent.

    The agent:
    1. Creates a plan
    2. Executes the plan
    3. Uses registered tools
    4. Reports progress
    """

    if not goal.strip():

        print(
            "\n[Usage]\n"
            "  /agent <task>\n\n"
            "Example:\n"
            "  /agent Search the official "
            "Raspberry Pi 4 specifications "
            "and summarize them.\n"
        )

        return

    print("\n" + "=" * 55)
    print("             VERONICA AGENT")
    print("=" * 55)

    print(f"\nGoal: {goal}\n")

    def agent_status(message: str):

        print(f"[AGENT] {message}")

    try:

        print("Creating plan...\n")

        result = assistant.run_agent(
            goal,
            on_status_update=agent_status
        )

        print("\nAgent finished.")

        print(result)

        print()

    except Exception as e:

        print(
            f"\n[AGENT ERROR]: {e}\n"
        )

        logger.error(
            f"Agent execution error: {e}"
        )


# ============================================================
# COMMAND HANDLER
# ============================================================

def handle_command(
    cmd_text: str,
    assistant: VeronicaAssistant
) -> bool:
    """
    Handles slash commands.

    Returns:
        True  = command handled
        False = normal conversation
    """

    parts = cmd_text.strip().split(
        maxsplit=1
    )

    command = parts[0].lower()

    arg = (
        parts[1].strip()
        if len(parts) > 1
        else ""
    )

    tts = get_tts_engine()
    stt = get_stt_engine()

    # --------------------------------------------------------
    # HELP
    # --------------------------------------------------------

    if command == "/help":

        print_help()

        return True

    # --------------------------------------------------------
    # STATUS
    # --------------------------------------------------------

    elif command == "/status":

        print_status(assistant)

        return True

    # --------------------------------------------------------
    # AGENT
    # --------------------------------------------------------

    elif command == "/agent":

        run_agent_command(
            arg,
            assistant
        )

        return True

    # --------------------------------------------------------
    # CLEAR
    # --------------------------------------------------------

    elif command == "/clear":

        assistant.conversation.clear()

        os.system(
            "cls"
            if os.name == "nt"
            else "clear"
        )

        print_banner(assistant)

        print(
            "[Conversation history cleared]\n"
        )

        return True

    # --------------------------------------------------------
    # MEMORY
    # --------------------------------------------------------

    elif command == "/memory":

        facts = (
            assistant.conversation.recall()
        )

        print(
            "\n--- Remembered Facts "
            "& Preferences ---"
        )

        if not facts:

            print(
                "  (No facts stored.)"
            )

        else:

            for k, v in facts.items():

                print(
                    f"  • {k}: {v}"
                )

        print()

        return True

    # --------------------------------------------------------
    # REMEMBER
    # --------------------------------------------------------

    elif command == "/remember":

        if not arg:

            print(
                "[Usage: /remember "
                "<fact or preference>]"
            )

        else:

            msg = (
                assistant.conversation
                .remember(arg)
            )

            print(
                f"[Memory]: {msg}\n"
            )

        return True

    # --------------------------------------------------------
    # FORGET
    # --------------------------------------------------------

    elif command == "/forget":

        if not arg:

            print(
                "[Usage: /forget "
                "<fact or key>]"
            )

        else:

            success = (
                assistant.conversation
                .forget(arg)
            )

            if success:

                print(
                    f"[Memory]: Successfully "
                    f"forgot '{arg}'.\n"
                )

            else:

                print(
                    f"[Memory]: No matching "
                    f"fact found for '{arg}'.\n"
                )

        return True

    # --------------------------------------------------------
    # VOICE
    # --------------------------------------------------------

    elif command == "/voice":

        subparts = arg.split(
            maxsplit=1
        )

        subcmd = (
            subparts[0].lower()
            if subparts
            else ""
        )

        subarg = (
            subparts[1].strip()
            if len(subparts) > 1
            else ""
        )

        # Voice list
        if subcmd == "list":

            print_voice_list(tts)

            return True

        # Voice set
        elif subcmd == "set":

            if not subarg:

                print(
                    "[Usage: /voice set "
                    "<aria | jenny | neerja | ava>]"
                )

                print_voice_list(tts)

            else:

                success, msg = (
                    tts.set_voice(
                        subarg
                    )
                )

                if success:

                    print(
                        f"VERONICA: Voice "
                        f"set to {msg}.\n"
                    )

                    tts.speak(
                        "Voice changed."
                    )

                else:

                    print(
                        f"[Voice Error]: "
                        f"{msg}\n"
                    )

            return True

        # Voice speed
        elif subcmd == "speed":

            if not subarg:

                print(
                    f"[Current speaking speed: "
                    f"{tts.current_speed}]"
                )

            else:

                success, msg = (
                    tts.set_speed(
                        subarg
                    )
                )

                if success:

                    print(
                        f"VERONICA: Speaking "
                        f"speed set to {msg}.\n"
                    )

                else:

                    print(
                        f"[Speed Error]: "
                        f"{msg}\n"
                    )

            return True

        # Voice pitch
        elif subcmd == "pitch":

            if not subarg:

                print(
                    f"[Current voice pitch: "
                    f"{tts.current_pitch}]"
                )

            else:

                success, msg = (
                    tts.set_pitch(
                        subarg
                    )
                )

                if success:

                    print(
                        f"VERONICA: Voice "
                        f"pitch set to {msg}.\n"
                    )

                else:

                    print(
                        f"[Pitch Error]: "
                        f"{msg}\n"
                    )

            return True

        # Voice test
        elif subcmd == "test":

            print(
                "[Testing voice system...]"
            )

            tts.test_voice()

            print()

            return True

        # Live voice mode
        elif subcmd in (
            "live",
            "mode",
            "listen"
        ):

            tts.set_enabled(True)

            run_voice_mode(
                assistant
            )

            return True

        # Voice on
        elif subcmd in (
            "on",
            "enable",
            "start"
        ):

            tts.set_enabled(True)

            print(
                f"VERONICA: Voice output "
                f"enabled ({tts.current_voice}).\n"
            )

            return True

        # Voice off
        elif subcmd in (
            "off",
            "disable",
            "stop"
        ):

            tts.set_enabled(False)

            print(
                "VERONICA: Voice output "
                "disabled.\n"
            )

            return True

        # Toggle
        else:

            new_state = tts.toggle()

            state_str = (
                "ENABLED"
                if new_state
                else "DISABLED"
            )

            print(
                f"VERONICA: Voice output "
                f"is now {state_str}.\n"
            )

            return True

    # --------------------------------------------------------
    # TEXT MODE
    # --------------------------------------------------------

    elif command in (
        "/text",
        "/textmode"
    ):

        tts.set_enabled(False)

        print(
            "VERONICA: Returned to "
            "silent text mode.\n"
        )

        return True

    # --------------------------------------------------------
    # LISTEN
    # --------------------------------------------------------

    elif command == "/listen":

        if not stt.is_microphone_available():

            print(
                "[Voice Input]: Microphone "
                "is unavailable.\n"
            )

            return True

        print(
            "[Listening for speech...]"
        )

        success, speech_text = (
            stt.listen(timeout=6)
        )

        if success:

            print(
                f"You (voice): {speech_text}"
            )

            run_turn(
                speech_text,
                assistant
            )

        else:

            print(
                f"[Voice Notice]: "
                f"{speech_text}\n"
            )

        return True

    # --------------------------------------------------------
    # TOOLS
    # --------------------------------------------------------

    elif command == "/tools":

        print_tools(assistant)

        return True

    # --------------------------------------------------------
    # EXIT
    # --------------------------------------------------------

    elif command in (
        "/exit",
        "/quit"
    ):

        print(
            "\nVERONICA: Goodbye! "
            "Shutting down systems.\n"
        )

        sys.exit(0)

    return False


# ============================================================
# NORMAL TURN
# ============================================================

def run_turn(
    user_text: str,
    assistant: VeronicaAssistant
):
    """Process a normal VERONICA conversation turn."""

    def status_callback(message: str):

        print(
            f"[{message}]",
            end="\r",
            flush=True
        )

    reply = assistant.process_input(
        user_text,
        on_status_update=status_callback
    )

    print(
        " " * 60,
        end="\r"
    )

    clean_reply = (
        reply
        .replace("\u202f", " ")
        .replace("\xa0", " ")
    )

    print(
        f"VERONICA: {clean_reply}\n"
    )


# ============================================================
# MAIN
# ============================================================

def main():
    """Main VERONICA CLI interaction loop."""

    # --------------------------------------------------------
    # Check API key
    # --------------------------------------------------------

    if not settings.is_api_key_set():

        print(
            "\n[CRITICAL ERROR] "
            "GROQ_API_KEY is missing."
        )

        print(
            "Please check your .env file."
        )

        sys.exit(1)

    # --------------------------------------------------------
    # Initialize assistant
    # --------------------------------------------------------

    try:

        assistant = VeronicaAssistant()

    except Exception as e:

        print(
            f"[CRITICAL ERROR] "
            f"Failed to initialize VERONICA: {e}"
        )

        logger.critical(
            f"Initialization failure: {e}"
        )

        sys.exit(1)

    # --------------------------------------------------------
    # Startup
    # --------------------------------------------------------

    print_banner(assistant)

    # --------------------------------------------------------
    # Optional automatic voice mode
    # --------------------------------------------------------

    if settings.VOICE_ENABLED:

        run_voice_mode(
            assistant
        )

    # --------------------------------------------------------
    # Main terminal loop
    # --------------------------------------------------------

    while True:

        try:

            user_input = input(
                "You: "
            ).strip()

            if not user_input:

                continue

            # Simple exit
            if user_input.lower() in (
                "exit",
                "quit"
            ):

                print(
                    "\nVERONICA: Goodbye! "
                    "Systems standing down.\n"
                )

                break

            # Slash command
            if user_input.startswith("/"):

                handled = handle_command(
                    user_input,
                    assistant
                )

                if handled:

                    continue

            # Normal conversation
            run_turn(
                user_input,
                assistant
            )

        except KeyboardInterrupt:

            print(
                "\n\nVERONICA: Interrupted. "
                "Shutting down gracefully. "
                "Goodbye!\n"
            )

            break

        except EOFError:

            print(
                "\n\nVERONICA: Session ended. "
                "Goodbye!\n"
            )

            break

        except Exception as e:

            print(
                f"\n[Unexpected Error]: {e}\n"
            )

            logger.error(
                f"Top-level loop error: {e}"
            )


# ============================================================
# PROGRAM ENTRY
# ============================================================

if __name__ == "__main__":
    main()