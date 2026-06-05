import unittest
from unittest.mock import patch

import main


class TestMainDependencyGuards(unittest.TestCase):
    @patch("main.search_sync_playwright", new=None)
    @patch("main.execute_search")
    @patch("main.execute_generate")
    def test_execute_run_stops_when_playwright_is_missing(self, mock_execute_generate, mock_execute_search):
        with patch("builtins.print") as mock_print:
            main.execute_run("keywords.txt", platform="linkedin", limit=5)

        mock_execute_search.assert_not_called()
        mock_execute_generate.assert_not_called()
        mock_print.assert_any_call(
            "[ERROR] Playwright is not installed. Please run pip install -r requirements.txt to install it."
        )

    @patch("main.search_sync_playwright", new=None)
    @patch("main.search_news")
    def test_execute_search_stops_when_playwright_is_missing(self, mock_search_news):
        with patch("builtins.print") as mock_print:
            main.execute_search("keywords.txt", limit=5)

        mock_search_news.assert_not_called()
        mock_print.assert_any_call(
            "[ERROR] Playwright is not installed. Please run pip install -r requirements.txt to install it."
        )


if __name__ == "__main__":
    unittest.main()
