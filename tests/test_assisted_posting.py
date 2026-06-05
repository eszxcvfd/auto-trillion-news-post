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

    @patch("src.assisted_posting.sync_playwright")
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
            image_file="test.png"
        )
        
        result = run_assisted_posting(item, self.config)
        self.assertTrue(result)
        
        # Verify calls
        mock_p.chromium.launch_persistent_context.assert_called_once()
        mock_page.goto.assert_called_with("https://www.linkedin.com/feed/", timeout=45000)
        mock_page.fill.assert_called()
        mock_context.close.assert_called_once()

    @patch("src.assisted_posting.sync_playwright")
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
            
        item = NewsItem(id=1, generated_post_file=post_path)
        
        result = run_assisted_posting(item, self.config)
        self.assertFalse(result)

if __name__ == "__main__":
    unittest.main()
