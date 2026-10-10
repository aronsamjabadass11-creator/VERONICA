"""
groq_client.py - Dedicated client interface for Groq Cloud.
Isolates all Groq SDK interactions, model configurations, and error handling.
"""

from typing import List, Dict, Any, Optional
from groq import (
    Groq,
    APIError,
    AuthenticationError,
    RateLimitError,
    APIConnectionError,
    NotFoundError,
)
from config.settings import settings
from config.logging_config import logger


class GroqClient:
    """Wrapper around the Groq SDK client with robust error handling."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = settings.GROQ_API_KEY if api_key is None else api_key.strip()
        self.model = model or settings.MODEL_NAME

        if not self.api_key:
            logger.error("Groq initialization failed: GROQ_API_KEY is not configured.")
            raise ValueError(
                "GROQ_API_KEY is not set. Please add GROQ_API_KEY to your .env file."
            )

        try:
            self.client = Groq(api_key=self.api_key)
            logger.info(f"GroqClient initialized successfully with model: {self.model}")
        except Exception as e:
            logger.error(f"Failed to instantiate Groq SDK: {e}")
            raise

    def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: str = "auto",
    ) -> Any:
        """
        Sends a chat completion request to Groq Cloud.
        Returns the raw ChatCompletionMessage object or raises an exception.
        """
        kwargs: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
        }

        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = tool_choice

        try:
            logger.info(f"Sending request to Groq with {len(messages)} messages (tools: {bool(tools)})")
            response = self.client.chat.completions.create(**kwargs)
            choice = response.choices[0]
            logger.info(f"Received Groq response (finish_reason: {choice.finish_reason})")
            return choice.message

        except AuthenticationError as e:
            logger.error(f"Authentication failed: {e}")
            raise RuntimeError(
                "Authentication failed with Groq Cloud. Please verify your GROQ_API_KEY in .env."
            ) from e

        except RateLimitError as e:
            logger.warning(f"Rate limit hit: {e}")
            raise RuntimeError(
                "Groq Cloud rate limit exceeded. Please wait a moment and try again."
            ) from e

        except APIConnectionError as e:
            logger.error(f"Network connection error to Groq Cloud: {e}")
            raise RuntimeError(
                "Unable to connect to Groq Cloud. Please check your internet connection."
            ) from e

        except NotFoundError as e:
            logger.error(f"Model not found error: {e}")
            raise RuntimeError(
                f"The configured model '{self.model}' was not found on Groq Cloud."
            ) from e

        except APIError as e:
            err_msg = getattr(e, "message", str(e))
            logger.error(f"Groq API error: {err_msg}")
            raise RuntimeError(f"Groq API error: {err_msg}") from e

        except Exception as e:
            logger.error(f"Unexpected error communicating with Groq: {e}")
            raise RuntimeError(f"An unexpected error occurred while contacting Groq: {e}") from e

    def generate_response(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """
        Convenience method that sends messages and returns the assistant's text response.
        Handles errors gracefully and returns user-friendly messages if an error occurs.
        """
        try:
            msg = self.chat_completion(messages=messages, tools=tools)
            return msg.content or ""
        except RuntimeError as err:
            return f"[VERONICA System Notice: {err}]"


# Global default client instance (lazy loaded)
_default_client: Optional[GroqClient] = None


def get_default_client() -> GroqClient:
    """Returns the singleton GroqClient instance."""
    global _default_client
    if _default_client is None:
        _default_client = GroqClient()
    return _default_client


def generate_response(messages: List[Dict[str, Any]]) -> str:
    """
    Module-level function to generate a response from Groq.
    Sends messages to Groq Cloud and returns the assistant response string.
    """
    client = get_default_client()
    return client.generate_response(messages)
