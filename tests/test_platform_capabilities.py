import os
import shutil
import tempfile
import unittest

from src.config import AppConfig
from src.models import BusinessWorkbookRow
from src.platform_capabilities import (
    BEST_EFFORT_POSTING_PLATFORMS,
    check_platform_media_requirements,
    get_platform_mvp_mode,
    is_best_effort_posting,
    is_posting_supported,
    platform_requires_image,
    resolve_local_image_path,
)
from src.posting_core import evaluate_row_eligibility, list_eligible_platforms


class TestPlatformCapabilities(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.config = AppConfig()
        self.config.image_dir = os.path.join(self.test_dir, "images")
        os.makedirs(self.config.image_dir, exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_platform_requires_image(self):
        self.assertTrue(platform_requires_image("instagram"))
        self.assertTrue(platform_requires_image("pinterest"))
        self.assertFalse(platform_requires_image("threads"))
        self.assertFalse(platform_requires_image("linkedin"))

    def test_is_posting_supported(self):
        self.assertTrue(is_posting_supported("instagram"))
        self.assertTrue(is_posting_supported("facebook"))
        self.assertTrue(is_posting_supported("x"))
        self.assertTrue(is_posting_supported("tiktok"))
        self.assertTrue(is_posting_supported("youtube"))
        self.assertFalse(is_posting_supported("unsupported_platform"))

    def test_best_effort_platform_metadata(self):
        self.assertEqual(BEST_EFFORT_POSTING_PLATFORMS, {"tiktok", "youtube"})
        self.assertTrue(is_best_effort_posting("tiktok"))
        self.assertFalse(is_best_effort_posting("threads"))
        self.assertIn("photo/image", get_platform_mvp_mode("tiktok"))
        self.assertIn("Community Post", get_platform_mvp_mode("youtube"))

    def test_resolve_local_image_path(self):
        image_name = "card.png"
        image_path = os.path.join(self.config.image_dir, image_name)
        with open(image_path, "w") as f:
            f.write("")

        resolved = resolve_local_image_path(image_name, self.config)
        self.assertEqual(resolved, os.path.abspath(image_path))

    def test_check_platform_media_requirements(self):
        status, reason = check_platform_media_requirements("threads", None, self.config)
        self.assertEqual(status, "ok")
        self.assertIsNone(reason)

        status, reason = check_platform_media_requirements("instagram", None, self.config)
        self.assertEqual(status, "skipped_missing_required_media")
        self.assertIn("requires an image", reason)

    def test_evaluate_row_eligibility_rejects_image_required_without_media(self):
        row = BusinessWorkbookRow(
            sheet_name="Payment",
            row_idx=2,
            id=1,
            title="Test Title",
            instagram_draft="Instagram content",
        )

        status, reason = evaluate_row_eligibility(
            row,
            "instagram",
            config=self.config,
        )
        self.assertEqual(status, "skipped_missing_required_media")
        self.assertIn("requires an image", reason)

    def test_list_eligible_platforms_excludes_image_required_without_media(self):
        row = BusinessWorkbookRow(
            sheet_name="Payment",
            row_idx=2,
            id=1,
            title="Test Title",
            instagram_draft="Instagram content",
            threads_draft="Threads content",
        )

        eligible = list_eligible_platforms(row, config=self.config)
        self.assertEqual([p for p, _ in eligible], ["threads"])


if __name__ == "__main__":
    unittest.main()