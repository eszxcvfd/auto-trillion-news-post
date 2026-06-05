import os
import shutil
import tempfile
import unittest
from src.models import NewsItem
from src.config import AppConfig
from src.ai_writer import validate_generated_post
from src.post_writer import extract_top_hashtags, write_post_file

class TestPostValidationAndWriting(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.config = AppConfig()
        self.config.post_dir = os.path.join(self.test_dir, "posts")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_validate_generated_post_valid_linkedin(self):
        content = """#Fintech #Payments #Banking #Strategy #Trillion
        
This is a professional strategically insightful post about the news.
We discuss the trillion-dollar opportunity here.

#TAHKFoundation #HenryUniverses #USIran #USTariffs #Trump"""
        self.assertTrue(validate_generated_post(content, "linkedin"))

    def test_validate_generated_post_invalid_linkedin_missing_top_tags(self):
        content = """#Fintech #Payments #Banking
        
This is a post with only 3 tags at the top.

#TAHKFoundation #HenryUniverses #USIran #USTariffs #Trump"""
        self.assertFalse(validate_generated_post(content, "linkedin"))

    def test_validate_generated_post_invalid_linkedin_missing_bottom_tags(self):
        content = """#Fintech #Payments #Banking #Strategy #Trillion
        
This is a post.

#TAHKFoundation #HenryUniverses"""
        self.assertFalse(validate_generated_post(content, "linkedin"))

    def test_validate_generated_post_contains_placeholder(self):
        content = """#Fintech #Payments #Banking #Strategy #Trillion
        
Post with a placeholder like {title}.

#TAHKFoundation #HenryUniverses #USIran #USTariffs #Trump"""
        self.assertFalse(validate_generated_post(content, "linkedin"))

    def test_validate_generated_post_valid_x(self):
        content = """This is a short tweet with #Fintech #AI #Trillion tags."""
        self.assertTrue(validate_generated_post(content, "x"))

    def test_extract_top_hashtags(self):
        content = """#Fintech #Payments #Banking #Strategy #Trillion #Extra
        Some other body text."""
        self.assertEqual(
            extract_top_hashtags(content),
            "#Fintech #Payments #Banking #Strategy #Trillion"
        )

    def test_write_post_file(self):
        item = NewsItem(
            id=12,
            found_date="2026-06-04",
            title="Merchant Payments $100 Trillion Opportunity",
            url="https://example.com/pay",
            source="Yahoo Finance",
            platform="linkedin",
            image_file="2026-06-04_012_payment_services.png"
        )
        post_content = "Generated content here."
        
        filepath = write_post_file(item, post_content, self.config)
        self.assertTrue(os.path.exists(filepath))
        self.assertEqual(os.path.basename(filepath), "2026-06-04_012_linkedin.md")
        
        # Verify markdown contents
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.read()
            self.assertIn("# Post 012 — Linkedin", lines)
            self.assertIn("Title: Merchant Payments $100 Trillion Opportunity", lines)
            self.assertIn("Source: Yahoo Finance", lines)
            self.assertIn("URL: https://example.com/pay", lines)
            self.assertIn("Generated Post\n\nGenerated content here.", lines)
            self.assertIn("../Ảnh Trillion $ news/2026-06-04_012_payment_services.png", lines)

if __name__ == "__main__":
    unittest.main()
