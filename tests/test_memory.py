"""
test_memory.py - Tests short-term and persistent memory components.
"""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from core.memory import ShortTermMemory, PersistentMemory


class TestMemory(unittest.TestCase):
    """Unit tests for memory management."""

    def test_short_term_trimming(self):
        mem = ShortTermMemory(max_messages=4)
        mem.set_system_prompt("System prompt")
        mem.add_user_message("msg 1")
        mem.add_assistant_message("msg 2")
        mem.add_user_message("msg 3")
        mem.add_assistant_message("msg 4")

        messages = mem.get_messages()
        # Should retain system prompt + most recent 3 messages = 4 total
        self.assertEqual(len(messages), 4)
        self.assertEqual(messages[0]["role"], "system")
        self.assertEqual(messages[-1]["content"], "msg 4")

    def test_persistent_memory_operations(self):
        with TemporaryDirectory() as tmp_dir:
            test_file = Path(tmp_dir) / "test_memory.json"
            pm = PersistentMemory(filepath=test_file)

            # Remember fact
            msg = pm.remember("favorite_language", "Python")
            self.assertIn("Python", msg)

            # Recall fact
            facts = pm.recall("language")
            self.assertIn("favorite_language", facts)
            self.assertEqual(facts["favorite_language"], "Python")

            # Forget fact
            success = pm.forget("favorite_language")
            self.assertTrue(success)
            self.assertNotIn("favorite_language", pm.recall())

    def test_persistent_memory_security_blocking(self):
        with TemporaryDirectory() as tmp_dir:
            test_file = Path(tmp_dir) / "test_memory.json"
            pm = PersistentMemory(filepath=test_file)

            notice = pm.remember("api_key", "secret123")
            self.assertIn("Security Notice", notice)
            self.assertNotIn("api_key", pm.recall())


if __name__ == "__main__":
    unittest.main()
