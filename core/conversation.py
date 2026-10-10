"""
conversation.py - Conversation Manager for VERONICA.
Coordinates short-term dialogue context, persistent user context, and system instructions.
"""

from typing import List, Dict, Any, Optional
from config.settings import settings
from core.memory import ShortTermMemory, PersistentMemory


class ConversationManager:
    """Manages active conversation context, history, and persistent facts."""

    def __init__(
        self,
        system_prompt: str = settings.SYSTEM_PROMPT,
        max_messages: int = settings.MAX_HISTORY_MESSAGES,
    ):
        self.base_system_prompt = system_prompt
        self.short_term = ShortTermMemory(max_messages=max_messages)
        self.persistent = PersistentMemory()
        self.refresh_system_prompt()

    def refresh_system_prompt(self):
        """Constructs system prompt combining base prompt with remembered facts."""
        context = self.persistent.get_memory_context() if settings.MEMORY_ENABLED else ""
        full_prompt = self.base_system_prompt
        if context:
            full_prompt += f"\n{context}"
        self.short_term.set_system_prompt(full_prompt)

    def add_user_message(self, content: str):
        """Records a user message."""
        self.short_term.add_user_message(content)

    def add_assistant_message(self, content: str):
        """Records an assistant reply."""
        self.short_term.add_assistant_message(content)

    def add_raw_message(self, message: Dict[str, Any]):
        """Records a raw message (e.g. tool message)."""
        self.short_term.add_raw_message(message)

    def get_messages(self) -> List[Dict[str, Any]]:
        """Returns messages prepared for LLM call."""
        self.refresh_system_prompt()
        return self.short_term.get_messages()

    def clear(self):
        """Clears short-term dialogue history."""
        self.short_term.clear()
        self.refresh_system_prompt()

    # Convenience memory methods
    def remember(self, text: str, value: Optional[str] = None) -> str:
        """Stores a fact into persistent memory and updates prompt context."""
        msg = self.persistent.remember(text, value)
        self.refresh_system_prompt()
        return msg

    def recall(self, query: Optional[str] = None) -> Dict[str, Any]:
        """Recalls facts from persistent memory."""
        return self.persistent.recall(query)

    def forget(self, key_or_fact: str) -> bool:
        """Removes a fact from persistent memory."""
        success = self.persistent.forget(key_or_fact)
        if success:
            self.refresh_system_prompt()
        return success
