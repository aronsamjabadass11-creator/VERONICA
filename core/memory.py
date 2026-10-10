"""
memory.py - Short-term and persistent memory management for VERONICA.
Maintains recent conversation turns and stores user-requested facts/preferences.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from config.settings import settings
from config.logging_config import logger


class ShortTermMemory:
    """Manages short-term conversational context with a rolling message window."""

    def __init__(self, max_messages: int = settings.MAX_HISTORY_MESSAGES):
        self.max_messages = max_messages
        self.messages: List[Dict[str, Any]] = []

    def set_system_prompt(self, prompt: str):
        """Sets or updates the initial system prompt."""
        if self.messages and self.messages[0].get("role") == "system":
            self.messages[0]["content"] = prompt
        else:
            self.messages.insert(0, {"role": "system", "content": prompt})

    def add_user_message(self, content: str):
        """Appends a user message to conversation history."""
        self.messages.append({"role": "user", "content": content})
        self._trim_history()

    def add_assistant_message(self, content: str):
        """Appends an assistant message to conversation history."""
        self.messages.append({"role": "assistant", "content": content})
        self._trim_history()

    def add_raw_message(self, message: Dict[str, Any]):
        """Adds a message dictionary (e.g., tool call or tool response)."""
        self.messages.append(message)
        self._trim_history()

    def _trim_history(self):
        """Ensures history does not exceed max_messages while preserving system prompt."""
        if len(self.messages) <= self.max_messages:
            return

        has_system = len(self.messages) > 0 and self.messages[0].get("role") == "system"
        if has_system:
            # Keep system prompt at index 0 and keep the most recent (max_messages - 1)
            keep_count = max(1, self.max_messages - 1)
            self.messages = [self.messages[0]] + self.messages[-keep_count:]
        else:
            self.messages = self.messages[-self.max_messages:]

    def get_messages(self) -> List[Dict[str, Any]]:
        """Returns the current message list for sending to LLM."""
        return list(self.messages)

    def clear(self):
        """Clears conversation messages, preserving system prompt if present."""
        system_msg = None
        if self.messages and self.messages[0].get("role") == "system":
            system_msg = self.messages[0]
        self.messages = [system_msg] if system_msg else []
        logger.info("Short-term conversation history cleared.")


class PersistentMemory:
    """Manages long-term key-fact memory saved in data/memory.json."""

    def __init__(self, filepath: Path = settings.MEMORY_FILE):
        self.filepath = filepath
        self._data: Dict[str, Any] = {"facts": {}, "last_updated": None}
        self.load()

    def load(self):
        """Loads memory facts from JSON file."""
        if not self.filepath.exists():
            self._save()
            return

        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                content = json.load(f)
                if isinstance(content, dict) and "facts" in content:
                    self._data = content
                else:
                    self._data = {"facts": content if isinstance(content, dict) else {}, "last_updated": None}
            logger.info(f"Loaded {len(self._data.get('facts', {}))} persistent facts from {self.filepath.name}")
        except Exception as e:
            logger.error(f"Error loading persistent memory: {e}")
            self._data = {"facts": {}, "last_updated": None}

    def _save(self):
        """Persists memory data to disk."""
        try:
            self.filepath.parent.mkdir(parents=True, exist_ok=True)
            self._data["last_updated"] = datetime.now().isoformat()
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2, ensure_ascii=False)
            logger.info("Persistent memory updated successfully.")
        except Exception as e:
            logger.error(f"Failed to save persistent memory: {e}")

    def remember(self, key_or_fact: str, value: Optional[str] = None) -> str:
        """
        Stores a fact or key-value pair.
        Never stores passwords, tokens, or API keys.
        """
        clean_text = key_or_fact.strip()
        lower_check = (clean_text + " " + (value or "")).lower()

        # Security check: Never store sensitive credentials
        sensitive_keywords = ["api_key", "password", "secret", "private_key", "token"]
        if any(kw in lower_check for kw in sensitive_keywords):
            logger.warning("Attempted to remember sensitive information blocked.")
            return "Security Notice: VERONICA cannot store sensitive keys, secrets, or passwords in memory."

        if value is not None:
            self._data["facts"][clean_text] = value.strip()
            msg = f"Remembered: '{clean_text}' = '{value.strip()}'"
        else:
            # Single fact string
            key = f"fact_{len(self._data['facts']) + 1}"
            self._data["facts"][key] = clean_text
            msg = f"Remembered fact: '{clean_text}'"

        self._save()
        return msg

    def recall(self, query: Optional[str] = None) -> Dict[str, Any]:
        """
        Recalls stored facts.
        If a query is provided, filters for matching keys or values.
        """
        facts = self._data.get("facts", {})
        if not query:
            return dict(facts)

        query_lower = query.lower().strip()
        return {
            k: v for k, v in facts.items()
            if query_lower in k.lower() or (isinstance(v, str) and query_lower in v.lower())
        }
    def forget(self, key_or_fact: str) -> bool:
        """Removes a specific fact or key from memory."""
        facts = self._data.get("facts", {})
        target = key_or_fact.strip().lower()

        matched_key = None

        for k, v in facts.items():
            if target == k.lower():
                matched_key = k
                break

            if isinstance(v, str):
                value_lower = v.lower()

                if target == value_lower or target in value_lower:
                    matched_key = k
                    break

        if matched_key:
            del facts[matched_key]
            self._save()
            return True

        return False
    def clear(self):
        """Clears all stored facts."""
        self._data = {"facts": {}, "last_updated": datetime.now().isoformat()}
        self._save()

    def get_memory_context(self) -> str:
        """Formats recalled facts for inclusion in the AI system prompt."""
        facts = self._data.get("facts", {})
        if not facts:
            return ""

        lines = ["\n[Remembered User Context & Preferences]"]
        for k, v in facts.items():
            lines.append(f"- {k}: {v}" if not k.startswith("fact_") else f"- {v}")
        return "\n".join(lines)
