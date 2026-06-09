import unittest
from unittest.mock import MagicMock, patch

from src.platform_workflows.linkedin_workflow import WORKFLOW_ID as LINKEDIN_WORKFLOW_ID
from src.platform_workflows.facebook_workflow import WORKFLOW_ID as FACEBOOK_WORKFLOW_ID
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
    def test_all_supported_platforms_have_isolated_workflows(self):
        expected = {
            "linkedin",
            "facebook",
            "x",
            "instagram",
            "pinterest",
            "threads",
            "tiktok",
            "youtube",
        }
        self.assertEqual(set(WORKFLOW_REGISTRY.keys()), expected)

    def test_workflow_ids_are_unique_per_platform(self):
        workflow_ids = list_registered_workflows()
        self.assertEqual(len(workflow_ids), len(set(workflow_ids.values())))
        self.assertEqual(workflow_ids["linkedin"], LINKEDIN_WORKFLOW_ID)
        self.assertEqual(workflow_ids["facebook"], FACEBOOK_WORKFLOW_ID)
        self.assertEqual(get_workflow_id("LinkedIn"), LINKEDIN_WORKFLOW_ID)

    def test_linkedin_and_facebook_use_different_runner_modules(self):
        linkedin = get_platform_workflow("linkedin")
        facebook = get_platform_workflow("facebook")
        self.assertNotEqual(linkedin.run, facebook.run)
        self.assertNotEqual(linkedin.workflow_id, facebook.workflow_id)

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
    def test_one_platform_failure_does_not_change_other_workflow_registration(self, mock_sync_playwright):
        mock_page = MagicMock()
        mock_context = MagicMock()
        mock_context.pages = [mock_page]
        mock_p = MagicMock()
        mock_p.chromium.launch_persistent_context.return_value = mock_context
        mock_cm = MagicMock()
        mock_cm.__enter__.return_value = mock_p
        mock_sync_playwright.return_value = mock_cm

        facebook_workflow = get_platform_workflow("facebook")
        with patch.object(facebook_workflow, "run", side_effect=RuntimeError("facebook selector drift")):
            context = PostingWorkflowContext(
                platform_key="facebook",
                post_content="Body",
            )
            result = run_platform_posting(context, AppConfig())
            self.assertFalse(result.success)
            self.assertEqual(result.workflow_id, FACEBOOK_WORKFLOW_ID)

        linkedin = get_platform_workflow("linkedin")
        self.assertEqual(linkedin.workflow_id, LINKEDIN_WORKFLOW_ID)
        self.assertIsNot(linkedin.run, facebook_workflow.run)


if __name__ == "__main__":
    unittest.main()