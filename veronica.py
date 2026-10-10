"""
VERONICA - AI Assistant powered by Groq Cloud
Model: openai/gpt-oss-20b
"""

import os
import sys
from dotenv import load_dotenv
from groq import Groq, APIError, AuthenticationError, RateLimitError

# Ensure UTF-8 encoding in Windows consoles
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stdin.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Model configuration
MODEL_NAME = "openai/gpt-oss-20b"

# System instruction defining VERONICA's persona
SYSTEM_PROMPT = {
    "role": "system",
    "content": (
        "You are VERONICA, a helpful, intelligent, and polite AI assistant. "
        "Provide clear, accurate, and concise answers to the user's questions."
    ),
}


def check_api_key() -> str:
    """
    Loads environment variables from .env and verifies GROQ_API_KEY is present.
    Ensures the key is never printed or exposed in logs.
    """
    load_dotenv()
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key or not api_key.strip():
        print("\n[ERROR] GROQ_API_KEY not found or empty.")
        print("Please ensure your .env file contains: GROQ_API_KEY=your_groq_api_key_here")
        sys.exit(1)

    return api_key.strip()


def run_veronica():
    """
    Main loop for the VERONICA assistant.
    """
    # Verify API key is available without exposing it
    api_key = check_api_key()

    # Initialize the Groq client
    try:
        client = Groq(api_key=api_key)
    except Exception as e:
        print(f"[ERROR] Failed to initialize Groq client: {e}")
        sys.exit(1)

    # Conversation history with system prompt
    messages = [SYSTEM_PROMPT]

    # Startup greeting
    print("\n" + "=" * 55)
    print("  VERONICA is online. How can I assist you today?")
    print("  (Type 'exit' to quit)")
    print("=" * 55 + "\n")

    while True:
        try:
            user_input = input("You: ").strip()

            # Skip empty inputs
            if not user_input:
                continue

            # Check for exit command
            if user_input.lower() in ("exit", "quit"):
                print("\nVERONICA: Goodbye! Have a great day.\n")
                break

            # Append user message to history
            messages.append({"role": "user", "content": user_input})

            # Call Groq API
            print("VERONICA is thinking...", end="\r", flush=True)

            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
            )

            assistant_reply = response.choices[0].message.content or ""

            # Clear the 'thinking...' status line and display the response
            print(" " * 30, end="\r")
            print(f"VERONICA: {assistant_reply}\n")

            # Append assistant response to history
            messages.append({"role": "assistant", "content": assistant_reply})

        except KeyboardInterrupt:
            print("\n\nVERONICA: Session interrupted. Shutting down gracefully. Goodbye!\n")
            break
        except EOFError:
            print("\n\nVERONICA: Session closed. Goodbye!\n")
            break
        except AuthenticationError:
            print("\n[API Error] Authentication failed: Invalid GROQ_API_KEY.")
            print("Please check your .env file and ensure the key is valid.\n")
        except RateLimitError:
            print("\n[API Error] Rate limit exceeded. Please wait a moment before trying again.\n")
        except APIError as e:
            err_msg = getattr(e, "message", str(e))
            print(f"\n[API Error] Groq API error: {err_msg}\n")
        except Exception as e:
            print(f"\n[Unexpected Error] An unexpected error occurred: {e}\n")


if __name__ == "__main__":
    run_veronica()
