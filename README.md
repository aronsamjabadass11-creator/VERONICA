# VERONICA — Personal AI Assistant

VERONICA is a modular, extensible personal AI assistant designed to run locally on Windows, powered by **Groq Cloud** using high-speed reasoning with the `openai/gpt-oss-20b` model.

---

## Architecture & Features

- **Primary LLM Provider**: Groq Cloud running `openai/gpt-oss-20b`.
- **Modular Architecture**: Clean separation between AI/LLM logic, conversation management, persistent memory, safe tools, voice systems, and configuration.
- **Controlled Agent Loop**: VERONICA safely plans, invokes tools, and synthesizes answers without allowing arbitrary shell access.
- **Short-term & Persistent Memory**:
  - Automatically manages a rolling conversational context window.
  - Remembers user facts and preferences persistently in `data/memory.json`.
- **Safe Tool System**:
  - `calculator`: Safe mathematical expression evaluation using Python AST (no arbitrary eval).
  - `get_current_datetime`: Instant access to local date, time, and day of week.
  - `list_project_files`: Safely lists files within the project workspace.
  - `read_project_file`: Reads text files inside the project (blocks path traversal and protected files like `.env`).
  - `search_project_files`: Searches text patterns across project files.
- **Voice System (Optional)**:
  - **Text-to-Speech (TTS)**: Local speech synthesis via `pyttsx3`.
  - **Speech-to-Text (STT)**: Microphone speech capture and transcription via `SpeechRecognition`.
  - Terminal text chat works smoothly even if microphone or audio hardware is missing.
- **Safe Logging**: Token-redacting logging writes to `data/veronica.log` without ever exposing API keys or secrets.

---

## Project Structure

```text
VERONICA/
│
├── .venv/                   # Python virtual environment
├── .env                     # Private environment variables (GROQ_API_KEY)
├── .gitignore               # Protects secrets, cache, and logs
├── requirements.txt         # Project dependencies
├── README.md                # Project documentation
│
├── main.py                  # Primary application entry point & interactive CLI
├── veronica.py              # Lightweight standalone script
│
├── config/
│   ├── __init__.py
│   ├── settings.py          # Centralized configuration & environment loader
│   └── logging_config.py    # Secret-redacting logger
│
├── core/
│   ├── __init__.py
│   ├── assistant.py         # Main assistant orchestrator & agent loop
│   ├── conversation.py      # Conversation manager & prompt assembler
│   └── memory.py            # Short-term rolling memory & persistent memory
│
├── llm/
│   ├── __init__.py
│   └── groq_client.py       # Isolated Groq Cloud SDK client & error handler
│
├── tools/
│   ├── __init__.py
│   ├── base.py              # Tool base class & schema generator
│   ├── calculator.py        # Safe math evaluator
│   ├── system_tools.py      # Datetime, file listing, reading, and searching
│   └── registry.py          # Central tool registration & dispatcher
│
├── voice/
│   ├── __init__.py
│   ├── speech_to_text.py    # Microphone speech-to-text
│   └── text_to_speech.py    # Offline text-to-speech engine
│
├── tests/
│   ├── __init__.py
│   ├── test_config.py       # Configuration & environment unit tests
│   ├── test_memory.py       # Short-term & persistent memory tests
│   ├── test_tools.py        # Safe tool & security restriction tests
│   ├── test_groq_client.py  # Groq client & integration tests
│   └── test_assistant.py    # Orchestration & intent tests
│
└── data/
    ├── memory.json          # Persistent user facts & preferences
    └── veronica.log         # Application execution log
```

---

## Quickstart Guide

### 1. Activate the Virtual Environment

In Windows PowerShell:
```powershell
.\.venv\Scripts\Activate.ps1
```

Or in Command Prompt:
```cmd
.\.venv\Scripts\activate.bat
```

### 2. Install Dependencies

```powershell
pip install -r requirements.txt
```

### 3. Configure Your Environment (.env)

Ensure your `.env` file at the root of the project contains your Groq API key:
```env
GROQ_API_KEY=your_groq_api_key_here
```

Optional settings you can configure in `.env`:
```env
VERONICA_MODEL=openai/gpt-oss-20b
VERONICA_MEMORY_ENABLED=true
VERONICA_MAX_HISTORY=20
VERONICA_VOICE_ENABLED=false
VERONICA_TTS_ENABLED=true
VERONICA_TTS_VOICE=en-US-AriaNeural
VERONICA_TTS_SPEED=+0%
VERONICA_TTS_VOLUME=+0%
VERONICA_STT_ENABLED=true
```

> **Security Note**: Never commit `.env` or share your API key. `.env` is ignored in `.gitignore`.

### 4. Start VERONICA

Run the primary application:
```powershell
python main.py
```

Startup banner:
```text
========================================
        VERONICA AI ASSISTANT        
========================================
AI ............ ONLINE
Groq .......... CONNECTED
Memory ........ READY
Voice ......... ON
TTS ........... READY
Voice Model ... en-US-AriaNeural
Microphone .... READY
Speaker ....... READY

VERONICA is online.
Type your message or use commands like /help, /voice test, or /exit.

You:
```

---

## Available Terminal Commands

| Command | Description |
|---|---|
| `/help` | Display the list of available commands |
| `/status` | Show system status (AI, Groq, Memory, Voice, TTS, Model) |
| `/voice` | Toggle neural voice output on or off |
| `/voice test` | Test speech with the neural voice (*"Hello, I am VERONICA..."*) |
| `/voice on` | Enable neural voice output |
| `/voice off` or `/text` | Return to silent terminal text mode |
| `/voice live` | Enter interactive hands-free microphone voice mode |
| `/listen` | Listen once for microphone speech input |
| `/clear` | Clear the terminal and dialogue history |
| `/memory` | View all remembered facts & user preferences |
| `/remember <text>` | Explicitly save a preference or fact |
| `/forget <fact>` | Delete a specific remembered fact |
| `/tools` | List all registered safe tools |
| `/exit` or `exit` | Gracefully shut down VERONICA |

---

## Memory System

VERONICA features a dual-layer memory system:

1. **Short-Term Memory**:
   - Maintains conversational continuity across turns.
   - Automatically maintains a rolling window (default: 20 messages) to prevent context bloat while keeping the system prompt intact.

2. **Persistent Memory**:
   - Stored in `data/memory.json`.
   - Remember facts either conversationally:
     - `Remember that I prefer concise answers.`
     - `Remember that my project is called VERONICA.`
   - Or using the `/remember` command:
     - `/remember I am working on Windows 11`
   - Stored facts are automatically incorporated into VERONICA's context for future turns.
   - Security filters prevent storing passwords, API keys, or private tokens.

---

## Safe Tool System

When you ask questions that require computation or project inspection, VERONICA autonomously selects and runs the appropriate tool:

- **Calculation**: "What is 15 * 8?" or "What is the square root of 144 plus 25?"
- **Date & Time**: "What time is it right now?" or "What day of the week is today?"
- **Project Exploration**:
  - "List the files in the project"
  - "What is inside config/settings.py?"
  - "Search for GROQ_API_KEY in the project"

**Safety Guarantees**:
- No arbitrary code execution or PowerShell command execution.
- Directory traversal outside the project directory is blocked.
- Protected files (such as `.env`) are blocked from being read through tools.

---

## Voice System

- **Text-to-Speech (TTS)**:
  - Powered by `pyttsx3` using Windows native SAPI speech.
  - Can be toggled at runtime using `/voice`.
- **Speech-to-Text (STT)**:
  - Powered by `SpeechRecognition`.
  - Type `/listen` in the terminal to speak your query.
  - If a microphone is not connected, VERONICA gracefully informs you and continues text chat normally.

---

## Running Tests

Run the full automated test suite using Python's built-in `unittest`:

```powershell
python -m unittest discover -s tests
```

---

## Troubleshooting

- **"GROQ_API_KEY not found or empty"**: Ensure `.env` is located in the project root and contains `GROQ_API_KEY=gsk_...`.
- **"Network connection error"**: Check your internet connection; Groq Cloud requires an active internet connection.
- **Voice input not working**: Ensure a microphone is connected and set as the default recording device in Windows Sound Settings.
