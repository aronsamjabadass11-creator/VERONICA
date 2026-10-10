"""
test_assistant.py - Tests assistant orchestration, commands, and intent.
"""

import unittest
from core.assistant import VeronicaAssistant
from config.settings import settings


class TestAssistant(unittest.TestCase):
    """Tests for assistant orchestration."""

    def setUp(self):
        if not settings.is_api_key_set():
            self.skipTest("GROQ_API_KEY not set")
        self.assistant = VeronicaAssistant()

    def test_remember_intent(self):
        reply = self.assistant.process_input("Remember that I prefer dark mode")
        self.assertIn("dark mode", reply)
        recalled = self.assistant.conversation.recall("dark mode")
        self.assertTrue(len(recalled) > 0)

    def test_status_dict(self):
        status = self.assistant.get_status()
        self.assertEqual(status["ai"], "ONLINE")
        self.assertTrue(status["api_key_set"])
        self.assertIn("calculator", status["tools_registered"])


if __name__ == "__main__":
    unittest.main()
