import os
import shutil
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from src.models import NewsItem
from src.config import AppConfig
from src.assisted_posting import parse_post_markdown, run_assisted_posting

class TestAssistedPosting(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.config = AppConfig()
        self.config.post_dir = os.path.join(self.test_dir, "posts")
        self.config.image_dir = os.path.join(self.test_dir, "images")
        os.makedirs(self.config.post_dir, exist_ok=True)
        os.makedirs(self.config.image_dir, exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_parse_post_markdown_valid(self):
        filepath = os.path.join(self.config.post_dir, "2026-06-04_001_linkedin.md")
        content = """# Post 001 — Linkedin

## News

Title: Test News
Source: Bloomberg
URL: https://example.com

## Image

Ảnh Trillion $ news/test.png

## Generated Post

#Fintech #Strategy #Trillion
This is the strategically insightful post body.
#TAHKFoundation #HenryUniverses #USIran #USTariffs #Trump
"""
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
            
        parsed = parse_post_markdown(filepath)
        expected = "#Fintech #Strategy #Trillion\nThis is the strategically insightful post body.\n#TAHKFoundation #HenryUniverses #USIran #USTariffs #Trump"
        self.assertEqual(parsed, expected)

    def test_parse_post_markdown_missing_marker(self):
        filepath = os.path.join(self.config.post_dir, "no_marker.md")
        content = "Some raw post text without any headers."
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
            
        parsed = parse_post_markdown(filepath)
        self.assertEqual(parsed, "Some raw post text without any headers.")

    def test_parse_post_markdown_nonexistent(self):
        parsed = parse_post_markdown(os.path.join(self.config.post_dir, "nonexistent.md"))
        self.assertEqual(parsed, "")

    def test_run_assisted_posting_missing_file_info(self):
        item = NewsItem(id=1, generated_post_file=None)
        self.assertFalse(run_assisted_posting(item, self.config))

    def test_run_assisted_posting_nonexistent_file(self):
        item = NewsItem(id=1, generated_post_file=os.path.join(self.config.post_dir, "nonexistent.md"))
        self.assertFalse(run_assisted_posting(item, self.config))

    @patch("playwright.sync_api.sync_playwright")
    @patch("builtins.input")
    def test_run_assisted_posting_success_mock(self, mock_input, mock_sync_playwright):
        # Setup mocks
        mock_input.return_value = "y"
        
        # Mock Playwright structure:
        # sync_playwright() -> context_manager
        # context_manager.__enter__() -> p
        # p.chromium.launch_persistent_context() -> context
        # context.pages -> [page]
        # page.goto(), page.query_selector(), page.click(), page.fill()
        
        mock_p = MagicMock()
        mock_context = MagicMock()
        mock_page = MagicMock()
        
        mock_context.pages = [mock_page]
        mock_p.chromium.launch_persistent_context.return_value = mock_context
        
        # Set up context manager mock
        mock_cm = MagicMock()
        mock_cm.__enter__.return_value = mock_p
        mock_sync_playwright.return_value = mock_cm
        
        # Mock elements
        mock_start_post_btn = MagicMock()
        mock_start_post_btn.is_visible.return_value = True
        
        mock_editor = MagicMock()
        mock_editor.is_visible.return_value = True
        
        # Configure query_selector
        def query_selector_side_effect(selector):
            if "share-box-feed-entry" in selector or "Start a post" in selector:
                return mock_start_post_btn
            if "ql-editor" in selector or "textbox" in selector:
                return mock_editor
            if "input[type='file']" in selector:
                return MagicMock() # file input
            return None
            
        mock_page.query_selector.side_effect = query_selector_side_effect
        mock_page.url = "https://www.linkedin.com/feed/"
        
        # Create temp files
        post_path = os.path.join(self.config.post_dir, "test_post.md")
        with open(post_path, "w", encoding="utf-8") as f:
            f.write("## Generated Post\n\nTest content")
            
        img_path = os.path.join(self.config.image_dir, "test.png")
        with open(img_path, "w") as f:
            f.write("")
            
        item = NewsItem(
            id=1,
            generated_post_file=post_path,
            image_file="test.png",
            platform="linkedin",
        )
        
        with patch(
            "src.platform_posting._open_linkedin_editor",
            return_value="div.ql-editor[contenteditable='true']",
        ), patch(
            "src.platform_posting._insert_linkedin_caption_via_js",
            return_value=True,
        ), patch(
            "src.platform_posting._upload_linkedin_image",
            return_value=True,
        ):
            result = run_assisted_posting(item, self.config)
        self.assertTrue(result)

        mock_p.chromium.launch_persistent_context.assert_called_once()
        mock_page.goto.assert_called_with("https://www.linkedin.com/feed/", timeout=45000)
        mock_context.close.assert_called_once()

    @patch("playwright.sync_api.sync_playwright")
    @patch("builtins.input")
    def test_run_assisted_posting_skipped_mock(self, mock_input, mock_sync_playwright):
        mock_input.return_value = "n"
        
        mock_p = MagicMock()
        mock_context = MagicMock()
        mock_page = MagicMock()
        mock_context.pages = [mock_page]
        mock_p.chromium.launch_persistent_context.return_value = mock_context
        
        mock_cm = MagicMock()
        mock_cm.__enter__.return_value = mock_p
        mock_sync_playwright.return_value = mock_cm
        
        # Mock elements
        mock_start_post_btn = MagicMock()
        mock_start_post_btn.is_visible.return_value = True
        
        mock_editor = MagicMock()
        mock_editor.is_visible.return_value = True
        
        def query_selector_side_effect(selector):
            if "share-box-feed-entry" in selector or "Start a post" in selector:
                return mock_start_post_btn
            if "ql-editor" in selector or "textbox" in selector:
                return mock_editor
            return None
            
        mock_page.query_selector.side_effect = query_selector_side_effect
        mock_page.url = "https://www.linkedin.com/feed/"
        
        post_path = os.path.join(self.config.post_dir, "test_post.md")
        with open(post_path, "w", encoding="utf-8") as f:
            f.write("## Generated Post\n\nTest content")
            
        item = NewsItem(id=1, generated_post_file=post_path, platform="linkedin")
        
        result = run_assisted_posting(item, self.config)
        self.assertFalse(result)

    @patch("playwright.sync_api.sync_playwright")
    @patch("builtins.input")
    def test_run_assisted_posting_direct_content_mock(self, mock_input, mock_sync_playwright):
        mock_input.return_value = "y"
        
        mock_p = MagicMock()
        mock_context = MagicMock()
        mock_page = MagicMock()
        mock_context.pages = [mock_page]
        mock_p.chromium.launch_persistent_context.return_value = mock_context
        
        mock_cm = MagicMock()
        mock_cm.__enter__.return_value = mock_p
        mock_sync_playwright.return_value = mock_cm
        
        # Mock elements
        mock_start_post_btn = MagicMock()
        mock_start_post_btn.is_visible.return_value = True
        
        mock_editor = MagicMock()
        mock_editor.is_visible.return_value = True
        
        def query_selector_side_effect(selector):
            if "share-box-feed-entry" in selector or "Start a post" in selector:
                return mock_start_post_btn
            if "ql-editor" in selector or "textbox" in selector:
                return mock_editor
            return None
            
        mock_page.query_selector.side_effect = query_selector_side_effect
        mock_page.url = "https://www.linkedin.com/feed/"
        
        item = NewsItem(id=1, generated_post_file=None, platform="linkedin")

        with patch(
            "src.platform_posting._open_linkedin_editor",
            return_value="div.ql-editor[contenteditable='true']",
        ), patch(
            "src.platform_posting._insert_linkedin_caption_via_js",
            return_value=True,
        ) as mock_js_caption:
            result = run_assisted_posting(
                item, self.config, post_content="Direct post content"
            )
        self.assertTrue(result)
        mock_js_caption.assert_called_once_with(mock_page, "Direct post content")

    def test_run_assisted_posting_rejects_invalid_platform(self):
        item = NewsItem(id=1, platform="unsupported_platform", generated_post_file=None)
        self.assertFalse(
            run_assisted_posting(item, self.config, post_content="Draft content")
        )

    @patch("playwright.sync_api.sync_playwright")
    @patch("builtins.input")
    def test_run_assisted_posting_facebook_mock(self, mock_input, mock_sync_playwright):
        mock_input.return_value = "y"

        mock_p = MagicMock()
        mock_context = MagicMock()
        mock_page = MagicMock()
        mock_context.pages = [mock_page]
        mock_p.chromium.launch_persistent_context.return_value = mock_context

        mock_cm = MagicMock()
        mock_cm.__enter__.return_value = mock_p
        mock_sync_playwright.return_value = mock_cm

        mock_start_btn = MagicMock()
        mock_start_btn.is_visible.return_value = True
        mock_editor = MagicMock()
        mock_editor.is_visible.return_value = True

        def query_selector_side_effect(selector):
            if "on your mind" in selector or "Create a post" in selector:
                return mock_start_btn
            if "textbox" in selector or "contenteditable" in selector:
                return mock_editor
            return None

        mock_page.query_selector.side_effect = query_selector_side_effect
        mock_page.url = "https://www.facebook.com/"

        item = NewsItem(id=1, platform="facebook", generated_post_file=None)
        result = run_assisted_posting(item, self.config, post_content="Facebook draft text")
        self.assertTrue(result)
        mock_page.goto.assert_called_with("https://www.facebook.com/", timeout=45000)

    @patch("playwright.sync_api.sync_playwright")
    @patch("builtins.input")
    def test_run_assisted_posting_facebook_uploads_image_before_caption(
        self, mock_input, mock_sync_playwright
    ):
        mock_input.return_value = "y"

        mock_p = MagicMock()
        mock_context = MagicMock()
        mock_page = MagicMock()
        mock_context.pages = [mock_page]
        mock_p.chromium.launch_persistent_context.return_value = mock_context

        mock_cm = MagicMock()
        mock_cm.__enter__.return_value = mock_p
        mock_sync_playwright.return_value = mock_cm

        mock_start_btn = MagicMock()
        mock_start_btn.is_visible.return_value = True
        mock_editor = MagicMock()
        mock_editor.is_visible.return_value = True
        mock_dialog = MagicMock()
        mock_photo_btn = MagicMock()
        mock_photo_btn.is_visible.return_value = True
        call_order = []

        def query_selector_side_effect(selector):
            if "on your mind" in selector or "Create a post" in selector:
                return mock_start_btn
            if selector == "div[role='dialog']":
                return mock_dialog
            if "Photo/video" in selector or "Ảnh/video" in selector:
                return mock_photo_btn
            if "textbox" in selector or "contenteditable" in selector:
                return mock_editor
            return None

        mock_page.query_selector.side_effect = query_selector_side_effect
        mock_dialog.query_selector.return_value = mock_photo_btn

        def click_side_effect(*args, **kwargs):
            call_order.append("click")

        def paste_side_effect(*args, **kwargs):
            call_order.append("paste")

        mock_page.click.side_effect = click_side_effect
        mock_page.keyboard.insert_text.side_effect = paste_side_effect
        mock_page.url = "https://www.facebook.com/"

        item = NewsItem(
            id=1,
            platform="facebook",
            generated_post_file=None,
            image_file="card.png",
        )
        with patch(
            "src.assisted_posting.prepare_posting_assets",
            return_value=("/tmp/card.png", None),
        ), patch(
            "src.platform_posting._upload_facebook_image",
            side_effect=lambda *a, **k: call_order.append("upload") or True,
        ), patch(
            "src.platform_posting._insert_facebook_caption_via_js",
            side_effect=lambda *a, **k: call_order.append("paste") or True,
        ):
            result = run_assisted_posting(
                item,
                self.config,
                post_content="Facebook draft text",
            )

        self.assertTrue(result)
        self.assertIn("upload", call_order)
        self.assertIn("paste", call_order)
        self.assertLess(call_order.index("upload"), call_order.index("paste"))

    @patch("playwright.sync_api.sync_playwright")
    @patch("builtins.input")
    def test_run_assisted_posting_x_mock(self, mock_input, mock_sync_playwright):
        mock_input.return_value = "y"

        mock_p = MagicMock()
        mock_context = MagicMock()
        mock_page = MagicMock()
        mock_context.pages = [mock_page]
        mock_p.chromium.launch_persistent_context.return_value = mock_context

        mock_cm = MagicMock()
        mock_cm.__enter__.return_value = mock_p
        mock_sync_playwright.return_value = mock_cm

        mock_editor = MagicMock()
        mock_editor.is_visible.return_value = True

        def query_selector_side_effect(selector):
            if "tweetTextarea" in selector or "textbox" in selector or "contenteditable" in selector:
                return mock_editor
            return None

        mock_page.query_selector.side_effect = query_selector_side_effect
        mock_page.url = "https://x.com/compose/tweet"

        item = NewsItem(id=1, platform="x", generated_post_file=None)
        result = run_assisted_posting(item, self.config, post_content="X post draft")
        self.assertTrue(result)
        mock_page.goto.assert_called_with("https://x.com/compose/tweet", timeout=45000)

    def test_run_assisted_posting_requires_image_for_instagram(self):
        item = NewsItem(
            id=1,
            platform="instagram",
            generated_post_file=None,
        )
        self.assertFalse(
            run_assisted_posting(item, self.config, post_content="Instagram draft")
        )

    @patch("playwright.sync_api.sync_playwright")
    @patch("builtins.input")
    def test_run_assisted_posting_tiktok_best_effort_mock(self, mock_input, mock_sync_playwright):
        mock_input.return_value = "y"

        mock_p = MagicMock()
        mock_context = MagicMock()
        mock_page = MagicMock()
        mock_context.pages = [mock_page]
        mock_p.chromium.launch_persistent_context.return_value = mock_context

        mock_cm = MagicMock()
        mock_cm.__enter__.return_value = mock_p
        mock_sync_playwright.return_value = mock_cm

        mock_start_btn = MagicMock()
        mock_start_btn.is_visible.return_value = True
        mock_editor = MagicMock()
        mock_editor.is_visible.return_value = True

        def query_selector_side_effect(selector):
            if "upload" in selector.lower() or "select" in selector.lower():
                return mock_start_btn
            if "textbox" in selector or "textarea" in selector or "contenteditable" in selector:
                return mock_editor
            if "input[type='file']" in selector:
                return MagicMock()
            return None

        mock_page.query_selector.side_effect = query_selector_side_effect
        mock_page.url = "https://www.tiktok.com/upload"

        img_path = os.path.join(self.config.image_dir, "test.png")
        with open(img_path, "w") as f:
            f.write("")

        item = NewsItem(
            id=1,
            platform="tiktok",
            image_file="test.png",
            generated_post_file=None,
        )

        result = run_assisted_posting(item, self.config, post_content="TikTok photo caption")
        self.assertTrue(result)
        mock_page.goto.assert_called_with("https://www.tiktok.com/upload", timeout=45000)

if __name__ == "__main__":
    unittest.main()
