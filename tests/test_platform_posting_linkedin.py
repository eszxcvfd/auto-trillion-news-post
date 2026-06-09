import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from src.platform_posting import (
    _insert_linkedin_caption_via_js,
    _paste_linkedin_caption,
    _upload_linkedin_image,
)
from src.platform_workflows.linkedin_workflow import (
    _find_linkedin_start_post,
    _open_linkedin_editor,
)
from src.platform_workflows.profiles import PLATFORM_PROFILES


class TestLinkedInPosting(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.image_path = os.path.join(self.test_dir, "card.png")
        with open(self.image_path, "wb") as handle:
            handle.write(b"png")

    def test_upload_linkedin_image_fails_when_file_missing(self):
        page = MagicMock()
        self.assertFalse(_upload_linkedin_image(page, os.path.join(self.test_dir, "missing.png")))

    @patch("src.platform_workflows.linkedin_workflow._linkedin_caption_editor")
    def test_paste_linkedin_caption_uses_js_first(self, mock_get_editor):
        page = MagicMock()
        mock_editor = MagicMock()
        mock_get_editor.return_value = mock_editor
        with patch("src.platform_workflows.linkedin_workflow._insert_linkedin_caption_via_js", return_value=True):
            _paste_linkedin_caption(page, "LinkedIn body")
        page.keyboard.insert_text.assert_not_called()

    def test_insert_linkedin_caption_via_js_returns_evaluate_result(self):
        editor = MagicMock()
        editor.evaluate.return_value = True
        self.assertTrue(_insert_linkedin_caption_via_js(editor, "LinkedIn body"))
        editor.evaluate.assert_called_once()

    def test_open_linkedin_editor_clicks_start_post_and_waits_for_modal(self):
        page = MagicMock()
        profile = PLATFORM_PROFILES["linkedin"]
        start_btn = MagicMock()
        start_btn.is_visible.return_value = True
        page.get_by_role.return_value.count.return_value = 0
        page.get_by_text.return_value.count.return_value = 0

        with patch(
            "src.platform_workflows.linkedin_workflow._linkedin_caption_editor",
            side_effect=[None, None, MagicMock(count=MagicMock(return_value=1), first=MagicMock(is_visible=MagicMock(return_value=True)))],
        ), patch(
            "src.platform_workflows.linkedin_workflow.first_visible",
            return_value=(start_btn, "button.share-box-feed-entry__trigger"),
        ), patch(
            "src.platform_workflows.linkedin_workflow._click_linkedin_target",
            return_value=True,
        ) as mock_click:
            selector = _open_linkedin_editor(page, profile)

        self.assertEqual(selector, "div.ql-editor[contenteditable='true']")
        mock_click.assert_called_once()

    def test_find_linkedin_start_post_prefers_role_button(self):
        page = MagicMock()
        role_btn = MagicMock()
        role_btn.is_visible.return_value = True
        page.get_by_role.return_value.count.return_value = 1
        page.get_by_role.return_value.first = role_btn

        target, hint = _find_linkedin_start_post(page, PLATFORM_PROFILES["linkedin"])
        self.assertIs(target, role_btn)
        self.assertIn("Start a post", hint)


if __name__ == "__main__":
    unittest.main()