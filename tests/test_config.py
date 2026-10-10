"""
test_config.py - Tests configuration loading and settings.
"""

import unittest
from config.settings import settings


class TestConfig(unittest.TestCase):
    """Unit tests for settings and environment loading."""

    def test_app_name_and_model(self):
        self.assertEqual(settings.APP_NAME, "VERONICA")
        self.assertEqual(settings.MODEL_NAME, "openai/gpt-oss-20b")

    def test_api_key_loaded(self):
        # GROQ_API_KEY must be configured, but we do not expose its value
        self.assertTrue(settings.is_api_key_set(), "GROQ_API_KEY should be loaded and non-empty")
        self.assertIsInstance(settings.GROQ_API_KEY, str)

    def test_paths_exist(self):
        self.assertTrue(settings.PROJECT_ROOT.exists())
        self.assertTrue(settings.DATA_DIR.exists())


if __name__ == "__main__":
    unittest.main()
