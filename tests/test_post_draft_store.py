import os
import shutil
import tempfile
import unittest

from src.assisted_posting import parse_post_markdown
from src.post_draft_store import (
    merge_generated_post_content,
    read_post_draft,
    resolve_post_dir,
    save_post_draft,
    split_post_sections,
    validate_relative_post_path,
)


SAMPLE_POST = """# Post 001 — Linkedin

## News

Title: Merchant Payments Title
Source: N/A
URL:

## Image

../Ảnh Trillion $ news/temp.png

## Generated Post

Hello LinkedIn draft
Line two
"""


class TestPostDraftStore(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.post_dir = os.path.join(self.test_dir, "posts")
        os.makedirs(self.post_dir, exist_ok=True)
        self.post_path = os.path.join(self.post_dir, "2026-06-09_001_payment_linkedin.md")
        with open(self.post_path, "w", encoding="utf-8") as f:
            f.write(SAMPLE_POST)

        class MockConfig:
            post_dir = self.post_dir
            excel_file = os.path.join(self.test_dir, "workbook.xlsx")

        self.config = MockConfig()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_split_and_merge_generated_post(self):
        preamble, body, news, image = split_post_sections(SAMPLE_POST)
        self.assertIn("## Generated Post", preamble)
        self.assertEqual(body, "Hello LinkedIn draft\nLine two")
        self.assertIn("Merchant Payments Title", news)
        self.assertIn("temp.png", image)

        updated = merge_generated_post_content(SAMPLE_POST, "Updated body\nSecond line")
        self.assertTrue(updated.endswith("Updated body\nSecond line\n"))
        self.assertEqual(parse_post_markdown_from_content(updated), "Updated body\nSecond line")

    def test_validate_relative_post_path_rejects_traversal(self):
        with self.assertRaises(ValueError):
            validate_relative_post_path("../secrets.md", self.post_dir)

    def test_read_and_save_post_draft(self):
        detail = read_post_draft(self.config, "2026-06-09_001_payment_linkedin.md")
        self.assertEqual(detail.generated_post, "Hello LinkedIn draft\nLine two")

        saved = save_post_draft(
            self.config,
            "2026-06-09_001_payment_linkedin.md",
            "Saved from Web UI",
        )
        self.assertEqual(saved.generated_post, "Saved from Web UI")
        self.assertTrue(os.path.exists(f"{self.post_path}.bak"))

        reloaded = read_post_draft(self.config, "2026-06-09_001_payment_linkedin.md")
        self.assertEqual(reloaded.generated_post, "Saved from Web UI")
        self.assertEqual(parse_post_markdown(self.post_path), "Saved from Web UI")

    def test_resolve_post_dir_from_config(self):
        self.assertEqual(resolve_post_dir(config=self.config), os.path.abspath(self.post_dir))


def parse_post_markdown_from_content(content: str) -> str:
    import tempfile

    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".md", delete=False) as handle:
        handle.write(content)
        path = handle.name
    try:
        return parse_post_markdown(path)
    finally:
        os.remove(path)


if __name__ == "__main__":
    unittest.main()