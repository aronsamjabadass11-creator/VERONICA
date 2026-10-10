"""
Core module for VERONICA.
"""

from .assistant import VeronicaAssistant
from .conversation import ConversationManager
from .memory import ShortTermMemory, PersistentMemory

__all__ = [
    "VeronicaAssistant",
    "ConversationManager",
    "ShortTermMemory",
    "PersistentMemory",
]
