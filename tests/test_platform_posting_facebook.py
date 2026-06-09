import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from src.platform_posting import (
    _facebook_caption_editor,
    _insert_facebook_caption_via_js,
    _paste_facebook_caption,
    _upload_facebook_image,
)


class TestFacebookImageUpload(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.image_path = os.path.join(self.test_dir, "card.png")
        with open(self.image_path, "wb") as handle:
            handle.write(b"png")

    def test_upload_facebook_image_fails_when_file_missing(self):
        page = MagicMock()
        self.assertFalse(_upload_facebook_image(page, os.path.join(self.test_dir, "missing.png")))


class TestFacebookCaptionPaste(unittest.TestCase):
    def test_facebook_caption_editor_prefers_main_placeholder(self):
        page = MagicMock()
        dialog = MagicMock()

        preview_editor = MagicMock()
        preview_editor.get_attribute.return_value = ""
        main_editor = MagicMock()
        main_editor.get_attribute.return_value = "What's on your mind, Joh?"

        candidates = MagicMock()
        candidates.count.return_value = 2
        candidates.nth.side_effect = [preview_editor, main_editor]
        dialog.locator.return_value = candidates

        with patch(
            "src.platform_workflows.facebook_workflow._facebook_dialog_locators",
            return_value=iter([dialog]),
        ):
            selected = _facebook_caption_editor(page)
        self.assertIs(selected, main_editor)

    def test_paste_facebook_caption_uses_js_first(self):
        page = MagicMock()
        with patch("src.platform_workflows.facebook_workflow._insert_facebook_caption_via_js", return_value=True):
            _paste_facebook_caption(page, "Caption body")
        page.keyboard.insert_text.assert_not_called()

    def test_insert_facebook_caption_via_js_returns_evaluate_result(self):
        page = MagicMock()
        page.evaluate.return_value = True
        self.assertTrue(_insert_facebook_caption_via_js(page, "Caption body"))
        page.evaluate.assert_called_once()


if __name__ == "__main__":
    unittest.main()