"""
LLM interface module for VERONICA.
"""

from .groq_client import GroqClient, generate_response

__all__ = ["GroqClient", "generate_response"]
