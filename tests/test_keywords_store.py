import os
import shutil
import tempfile
import unittest

from src.keywords_store import (
    DISABLED_PREFIX,
    KeywordRecord,
    load_active_keywords,
    load_keyword_records,
    normalize_keyword_records,
    save_keyword_records,
    serialize_keyword_records,
)


class TestKeywordsStore(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.keywords_path = os.path.join(self.test_dir, "keywords.txt")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_load_keyword_records_ignores_comments_and_parses_disabled(self):
        with open(self.keywords_path, "w", encoding="utf-8") as f:
            f.write(
                "# harvest comment\n"
                "Payment services trillion $\n"
                f"{DISABLED_PREFIX} Mobile payments trillion $\n"
            )

        records = load_keyword_records(self.keywords_path)
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0].text, "Payment services trillion $")
        self.assertTrue(records[0].enabled)
        self.assertEqual(records[1].text, "Mobile payments trillion $")
        self.assertFalse(records[1].enabled)

    def test_load_active_keywords_skips_disabled(self):
        with open(self.keywords_path, "w", encoding="utf-8") as f:
            f.write(
                "Active keyword\n"
                f"{DISABLED_PREFIX} Disabled keyword\n"
            )

        active = load_active_keywords(self.keywords_path)
        self.assertEqual(active, ["Active keyword"])

    def test_normalize_rejects_duplicates_case_insensitive(self):
        records = [
            KeywordRecord(text="Payment services trillion $", enabled=True),
            KeywordRecord(text="payment services trillion $", enabled=True),
        ]
        with self.assertRaises(ValueError):
            normalize_keyword_records(records)

    def test_save_round_trip(self):
        records = [
            KeywordRecord(text="Payment services trillion $", enabled=True),
            KeywordRecord(text="Mobile payments trillion $", enabled=False),
        ]
        save_keyword_records(records, self.keywords_path)

        with open(self.keywords_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("Payment services trillion $", content)
        self.assertIn(f"{DISABLED_PREFIX} Mobile payments trillion $", content)

        reloaded = load_keyword_records(self.keywords_path)
        self.assertEqual(len(reloaded), 2)
        self.assertTrue(reloaded[0].enabled)
        self.assertFalse(reloaded[1].enabled)

    def test_serialize_keyword_records(self):
        serialized = serialize_keyword_records([
            KeywordRecord(text="Alpha", enabled=True),
            KeywordRecord(text="Beta", enabled=False),
        ])
        self.assertEqual(
            serialized,
            f"Alpha\n{DISABLED_PREFIX} Beta\n",
        )


if __name__ == "__main__":
    unittest.main()