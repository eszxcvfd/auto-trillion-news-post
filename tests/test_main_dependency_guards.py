import unittest
from unittest.mock import patch, MagicMock

import main


class TestNormalizeGeneratePlatform(unittest.TestCase):
    def test_blank_platform_means_all(self):
        self.assertEqual(main.normalize_generate_platform(None), "all")
        self.assertEqual(main.normalize_generate_platform(""), "all")
        self.assertEqual(main.normalize_generate_platform("   "), "all")
        self.assertEqual(main.normalize_generate_platform("none"), "all")

    def test_explicit_platform_is_preserved(self):
        self.assertEqual(main.normalize_generate_platform("facebook"), "facebook")


class TestExecuteRunGenerateScope(unittest.TestCase):
    @patch("main.AppConfig")
    @patch("main.execute_generate")
    @patch("main.execute_search")
    def test_backfills_all_missing_drafts_when_harvest_saves_nothing(
        self,
        mock_execute_search,
        mock_execute_generate,
        mock_app_config,
    ):
        mock_execute_search.return_value = []
        mock_app_config.return_value = MagicMock(excel_file="/tmp/Trillion $ news.xlsx")

        with patch("os.path.exists", return_value=True), patch(
            "src.business_workbook.detect_workbook_type",
            return_value="business",
        ):
            main.execute_run("keywords.txt", platform=None, limit=2)

        mock_execute_generate.assert_called_once_with("all", None, target_ids=None)

    @patch("main.AppConfig")
    @patch("main.execute_generate")
    @patch("main.execute_search")
    def test_limits_generation_to_newly_saved_rows(
        self,
        mock_execute_search,
        mock_execute_generate,
        mock_app_config,
    ):
        saved_item = MagicMock(keyword="Payment services", id=3)
        mock_execute_search.return_value = [saved_item]
        mock_app_config.return_value = MagicMock(excel_file="/tmp/Trillion $ news.xlsx")

        with patch("os.path.exists", return_value=True), patch(
            "src.business_workbook.detect_workbook_type",
            return_value="business",
        ):
            main.execute_run("keywords.txt", platform=None, limit=2)

        mock_execute_generate.assert_called_once_with(
            "all",
            2,
            target_ids=[("Payment services", 3)],
        )


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
