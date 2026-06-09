import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from src.platform_posting import (
    _insert_linkedin_caption_via_js,
    _paste_linkedin_caption,
    _upload_linkedin_image,
)


class TestLinkedInPosting(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.image_path = os.path.join(self.test_dir, "card.png")
        with open(self.image_path, "wb") as handle:
            handle.write(b"png")

    def test_upload_linkedin_image_fails_when_file_missing(self):
        page = MagicMock()
        self.assertFalse(_upload_linkedin_image(page, os.path.join(self.test_dir, "missing.png")))

    def test_paste_linkedin_caption_uses_js_first(self):
        page = MagicMock()
        with patch("src.platform_posting._insert_linkedin_caption_via_js", return_value=True):
            _paste_linkedin_caption(page, "LinkedIn body")
        page.keyboard.insert_text.assert_not_called()

    def test_insert_linkedin_caption_via_js_returns_evaluate_result(self):
        page = MagicMock()
        page.evaluate.return_value = True
        self.assertTrue(_insert_linkedin_caption_via_js(page, "LinkedIn body"))
        page.evaluate.assert_called_once()


if __name__ == "__main__":
    unittest.main()