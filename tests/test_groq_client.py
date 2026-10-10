"""
test_groq_client.py - Unit and integration tests for GroqClient.
"""

import unittest
from config.settings import settings
from llm.groq_client import GroqClient


class TestGroqClient(unittest.TestCase):
    """Tests for GroqClient initialization and operations."""

    def test_missing_api_key_raises_error(self):
        with self.assertRaises(ValueError):
            GroqClient(api_key="")

    def test_client_initialization_with_key(self):
        if not settings.is_api_key_set():
            self.skipTest("GROQ_API_KEY not configured in .env")

        client = GroqClient()
        self.assertEqual(client.model, settings.MODEL_NAME)
        self.assertIsNotNone(client.client)

    def test_live_groq_response(self):
        """Live API test against Groq Cloud using openai/gpt-oss-20b."""
        if not settings.is_api_key_set():
            self.skipTest("GROQ_API_KEY not configured in .env")

        client = GroqClient()
        reply = client.generate_response([
            {"role": "user", "content": "Respond with the word SUCCESS only."}
        ])
        self.assertIn("SUCCESS", reply.upper())


if __name__ == "__main__":
    unittest.main()
