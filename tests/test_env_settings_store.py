import os
import shutil
import tempfile
import unittest

from src.env_settings_store import (
    parse_env_assignments,
    read_env_settings,
    save_env_settings,
)


class TestEnvSettingsStore(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.env_path = os.path.join(self.test_dir, ".env")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_read_defaults_when_env_missing(self):
        data = read_env_settings(self.env_path)
        self.assertFalse(data["env_exists"])
        self.assertFalse(data["gemini_api_key_configured"])
        self.assertEqual(data["values"]["AI_PROVIDER"], "gemini")
        self.assertEqual(data["values"]["GEMINI_API_KEY"], "")

    def test_save_and_return_api_key(self):
        saved = save_env_settings(
            {
                "GEMINI_API_KEY": "secret-key-value",
                "AI_MODEL": "gemma-4-31b-it",
                "SEARCH_PROVIDER": "bing",
                "HEADLESS": "false",
                "BACKUP_ENABLED": "false",
                "MAX_POSTS_PER_RUN": 5,
            },
            env_path=self.env_path,
        )

        self.assertTrue(saved["gemini_api_key_configured"])
        self.assertEqual(saved["values"]["GEMINI_API_KEY"], "secret-key-value")
        self.assertEqual(saved["values"]["AI_MODEL"], "gemma-4-31b-it")

        parsed = parse_env_assignments(self.env_path)
        self.assertEqual(parsed["GEMINI_API_KEY"], "secret-key-value")
        self.assertEqual(parsed["BACKUP_ENABLED"], "false")

    def test_preserve_api_key_when_blank(self):
        save_env_settings({"GEMINI_API_KEY": "keep-me"}, env_path=self.env_path)

        saved = save_env_settings(
            {"AI_MODEL": "gemini-1.5-flash", "GEMINI_API_KEY": ""},
            env_path=self.env_path,
        )

        parsed = parse_env_assignments(self.env_path)
        self.assertEqual(parsed["GEMINI_API_KEY"], "keep-me")
        self.assertEqual(saved["values"]["AI_MODEL"], "gemini-1.5-flash")

    def test_reject_invalid_search_provider(self):
        with self.assertRaises(ValueError):
            save_env_settings({"SEARCH_PROVIDER": "google"}, env_path=self.env_path)

    def test_preserve_extra_env_keys(self):
        with open(self.env_path, "w", encoding="utf-8") as f:
            f.write("CUSTOM_FLAG=1\nGEMINI_API_KEY=abc\n")

        save_env_settings({"AI_PROVIDER": "gemini"}, env_path=self.env_path)
        parsed = parse_env_assignments(self.env_path)
        self.assertEqual(parsed["CUSTOM_FLAG"], "1")
        self.assertEqual(parsed["AI_PROVIDER"], "gemini")


if __name__ == "__main__":
    unittest.main()