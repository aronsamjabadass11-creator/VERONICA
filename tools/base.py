"""
base.py - Base classes for VERONICA's tool system.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseTool(ABC):
    """Abstract base class for all safe tools."""

    name: str = ""
    description: str = ""
    parameters: Dict[str, Any] = {}

    @abstractmethod
    def execute(self, **kwargs) -> str:
        """Executes the tool with provided arguments and returns a string result."""
        pass

    def to_groq_schema(self) -> Dict[str, Any]:
        """Formats the tool definition into the Groq / OpenAI function schema."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }
