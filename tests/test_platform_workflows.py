import unittest
from unittest.mock import MagicMock, patch

from src.platform_workflows.linkedin_workflow import WORKFLOW_ID as LINKEDIN_WORKFLOW_ID
from src.platform_workflows.registry import (
    WORKFLOW_REGISTRY,
    get_platform_workflow,
    get_workflow_id,
    list_registered_workflows,
    run_platform_posting,
)
from src.platform_workflows.types import PostingWorkflowContext
from src.config import AppConfig


class TestPlatformWorkflowRegistry(unittest.TestCase):
    def test_registry_is_linkedin_only(self):
        self.assertEqual(set(WORKFLOW_REGISTRY.keys()), {"linkedin"})

    def test_workflow_ids_are_unique_per_platform(self):
        workflow_ids = list_registered_workflows()
        self.assertEqual(len(workflow_ids), len(set(workflow_ids.values())))
        self.assertEqual(workflow_ids["linkedin"], LINKEDIN_WORKFLOW_ID)
        self.assertEqual(get_workflow_id("LinkedIn"), LINKEDIN_WORKFLOW_ID)

    def test_get_platform_workflow_rejects_removed_platforms(self):
        linkedin = get_platform_workflow("linkedin")
        self.assertEqual(linkedin.workflow_id, LINKEDIN_WORKFLOW_ID)
        with self.assertRaises(ValueError):
            get_platform_workflow("facebook")

    @patch("playwright.sync_api.sync_playwright")
    def test_dispatch_reaches_platform_owned_runner(self, mock_sync_playwright):
        mock_page = MagicMock()
        mock_context = MagicMock()
        mock_context.pages = [mock_page]
        mock_p = MagicMock()
        mock_p.chromium.launch_persistent_context.return_value = mock_context
        mock_cm = MagicMock()
        mock_cm.__enter__.return_value = mock_p
        mock_sync_playwright.return_value = mock_cm

        linkedin_workflow = get_platform_workflow("linkedin")
        with patch.object(linkedin_workflow, "run", return_value=(True, "https://linkedin.com/post/1")) as mock_run:
            context = PostingWorkflowContext(
                platform_key="linkedin",
                post_content="Body",
                image_path=None,
                row_id=7,
                sheet_name="Payment",
            )
            result = run_platform_posting(context, AppConfig())
            self.assertTrue(result.success)
            self.assertEqual(result.workflow_id, LINKEDIN_WORKFLOW_ID)
            mock_run.assert_called_once()

    @patch("playwright.sync_api.sync_playwright")
    def test_removed_platform_returns_failure(self, mock_sync_playwright):
        mock_page = MagicMock()
        mock_context = MagicMock()
        mock_context.pages = [mock_page]
        mock_p = MagicMock()
        mock_p.chromium.launch_persistent_context.return_value = mock_context
        mock_cm = MagicMock()
        mock_cm.__enter__.return_value = mock_p
        mock_sync_playwright.return_value = mock_cm

        context = PostingWorkflowContext(
            platform_key="facebook",
            post_content="Body",
        )
        result = run_platform_posting(context, AppConfig())
        self.assertFalse(result.success)
        self.assertIn("not supported", result.failure_reason.lower())


if __name__ == "__main__":
    unittest.main()
