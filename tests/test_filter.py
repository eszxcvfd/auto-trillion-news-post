import unittest
from src.models import NewsItem
from src.config import AppConfig
from src.filter import (
    normalize_url,
    normalize_title,
    is_trillion_news,
    deduplicate_news,
    get_domain
)

class TestFilterLogic(unittest.TestCase):
    def setUp(self):
        # Create a mock config
        self.config = AppConfig()
        self.config.require_terms = ["trillion", "trillion-dollar", "$ trillion", "USD"]
        self.config.exclude_domains = ["reddit.com", "x.com"]

    def test_normalize_url(self):
        self.assertEqual(
            normalize_url("HTTPS://Example.Com/News/Article?utm_source=test&utm_medium=email"),
            "https://example.com/news/article"
        )
        self.assertEqual(
            normalize_url("https://example.com/path/"),
            "https://example.com/path"
        )

    def test_normalize_title(self):
        self.assertEqual(
            normalize_title("Merchant Payments: A $100 Trillion Opportunity!"),
            "merchant payments a 100 trillion opportunity"
        )
        self.assertEqual(
            normalize_title("  Multiple   Spaces   Here  "),
            "multiple spaces here"
        )

    def test_get_domain(self):
        self.assertEqual(get_domain("https://www.google.com/search"), "google.com")
        self.assertEqual(get_domain("http://reddit.com/r/all"), "reddit.com")

    def test_is_trillion_news_matching(self):
        # Match on title
        item1 = NewsItem(title="Merchant Payments a $100 Trillion Opportunity", url="https://example.com/1")
        self.assertTrue(is_trillion_news(item1, self.config))
        
        # Match on snippet
        item2 = NewsItem(title="Fintech Sector Analysis", snippet="The market cap of AI will reach trillions soon.", url="https://example.com/2")
        self.assertTrue(is_trillion_news(item2, self.config))

    def test_is_trillion_news_not_matching(self):
        # No trillion terms
        item = NewsItem(title="Merchant Payments a $100 Billion Opportunity", snippet="Huge growth expected.", url="https://example.com/3")
        self.assertFalse(is_trillion_news(item, self.config))

    def test_is_trillion_news_exclude_domains(self):
        # Contains trillion but in excluded domain
        item = NewsItem(title="AI is a trillion dollar market", url="https://www.reddit.com/r/news/123")
        self.assertFalse(is_trillion_news(item, self.config))

    def test_deduplicate_news(self):
        items = [
            NewsItem(title="Article One", url="https://example.com/1?utm=1"),
            NewsItem(title="Article One", url="https://example.com/1?utm=2"), # Duplicate URL & Title
            NewsItem(title="Article Two", url="https://example.com/2"),
            NewsItem(title="ARTICLE ONE", url="https://example.com/3"), # Duplicate Title (case-insensitive)
            NewsItem(title="Article Three", url="https://example.com/1"), # Duplicate URL
        ]
        
        deduped = deduplicate_news(items)
        self.assertEqual(len(deduped), 2)
        self.assertEqual(deduped[0].title, "Article One")
        self.assertEqual(deduped[1].title, "Article Two")

if __name__ == "__main__":
    unittest.main()
