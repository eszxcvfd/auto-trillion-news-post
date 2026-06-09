import os
import tempfile
import unittest

from src.draft_paths import (
    draft_cell_has_content,
    format_post_path_for_workbook,
    load_draft_from_cell,
    resolve_post_draft_path,
)


class TestDraftPaths(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.output_dir = os.path.join(self.root, "output")
        self.posts_dir = os.path.join(self.output_dir, "posts")
        os.makedirs(self.posts_dir, exist_ok=True)
        self.workbook = os.path.join(self.output_dir, "Trillion $ news.xlsx")
        with open(self.workbook, "wb") as handle:
            handle.write(b"")

        self.post_file = os.path.join(self.posts_dir, "2026-06-09_006_payment_services_trillion_facebook.md")
        with open(self.post_file, "w", encoding="utf-8") as handle:
            handle.write(
                "# Post\n\n## Generated Post\n\nVietnam banks draft body"
            )

    def test_resolve_legacy_output_posts_reference(self):
        legacy = "posts/2026-06-09_006_payment_services_trillion_facebook.md"
        resolved = resolve_post_draft_path(legacy, self.workbook)
        self.assertEqual(resolved, self.post_file)

    def test_resolve_workbook_relative_posts_reference(self):
        relative = "posts/2026-06-09_006_payment_services_trillion_facebook.md"
        resolved = resolve_post_draft_path(relative, self.workbook)
        self.assertEqual(resolved, self.post_file)

    def test_load_draft_from_missing_file_returns_none(self):
        missing = "./output/posts/does-not-exist.md"
        self.assertIsNone(load_draft_from_cell(missing, self.workbook))

    def test_draft_cell_has_content_false_for_missing_file_reference(self):
        missing = "./output/posts/does-not-exist.md"
        self.assertFalse(draft_cell_has_content(missing, self.workbook, self.posts_dir))

    def test_format_post_path_for_workbook(self):
        class MockConfig:
            excel_file = os.path.join(self.output_dir, "Trillion $ news.xlsx")

        formatted = format_post_path_for_workbook(self.post_file, MockConfig())
        self.assertEqual(
            formatted,
            "posts/2026-06-09_006_payment_services_trillion_facebook.md",
        )


if __name__ == "__main__":
    unittest.main()