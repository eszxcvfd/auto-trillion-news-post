import os
import json
import shutil
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from src.web_ui import app, OnboardingJob
from src.config import AppConfig
from src.scheduler import init_db, save_platform_session_status, get_platform_sessions_status

class TestSessionOnboarding(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.old_cwd = os.getcwd()
        os.chdir(self.test_dir)
        
        # Setup AppConfig overrides via environment
        self.db_path = os.path.join(self.test_dir, "scheduler.db")
        os.environ["EXCEL_FILE"] = os.path.join(self.test_dir, "Trillion $ news.xlsx")
        os.environ["OUTPUT_DIR"] = self.test_dir
        os.environ["IMAGE_DIR"] = os.path.join(self.test_dir, "images")
        os.environ["POST_DIR"] = os.path.join(self.test_dir, "posts")
        os.environ["LOG_DIR"] = os.path.join(self.test_dir, "logs")
        
        app.template_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src', 'templates')
        self.client = app.test_client()
        init_db(self.db_path)

    def tearDown(self):
        os.chdir(self.old_cwd)
        shutil.rmtree(self.test_dir)
        for key in ["EXCEL_FILE", "OUTPUT_DIR", "IMAGE_DIR", "POST_DIR", "LOG_DIR"]:
            if key in os.environ:
                del os.environ[key]

    def test_session_db_helpers(self):
        # Initial empty check
        status = get_platform_sessions_status(self.db_path)
        self.assertEqual(len(status), 0)

        # Save session status
        save_platform_session_status(self.db_path, "linkedin", "ready", '{"username": "test_user"}')
        status = get_platform_sessions_status(self.db_path)
        self.assertEqual(len(status), 1)
        self.assertIn("linkedin", status)
        self.assertEqual(status["linkedin"]["status"], "ready")
        self.assertEqual(status["linkedin"]["metadata"], '{"username": "test_user"}')
        self.assertIsNotNone(status["linkedin"]["last_checked_at"])

        # Update session status
        save_platform_session_status(self.db_path, "linkedin", "expired")
        status = get_platform_sessions_status(self.db_path)
        self.assertEqual(status["linkedin"]["status"], "expired")
        # metadata should be preserved via coalesce if none passed
        self.assertEqual(status["linkedin"]["metadata"], '{"username": "test_user"}')

    def test_api_sessions_status(self):
        save_platform_session_status(self.db_path, "linkedin", "ready")
        response = self.client.get('/api/sessions/status')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        self.assertIn("linkedin", data)
        self.assertEqual(data["linkedin"]["status"], "ready")
        self.assertIn("facebook", data)
        self.assertEqual(data["facebook"]["status"], "login-required")
        self.assertIn("x", data)
        self.assertEqual(data["x"]["status"], "login-required")

    @patch('src.web_ui.threading.Thread')
    def test_api_sessions_onboard_lifecycle(self, mock_thread):
        # 1. Start onboarding
        # Clear active onboarding job
        import src.web_ui
        src.web_ui.active_onboarding_job = None

        response = self.client.post('/api/sessions/onboard', json={"platform": "linkedin"})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("Session onboarding started", data["message"])
        self.assertEqual(data["job"]["platform"], "linkedin")
        self.assertEqual(data["job"]["status"], "preparing")
        mock_thread.assert_called_once()

        # 2. Get status
        response = self.client.get('/api/sessions/onboard/status')
        self.assertEqual(response.status_code, 200)
        status_data = json.loads(response.data)
        self.assertTrue(status_data["active"])
        self.assertEqual(status_data["job"]["platform"], "linkedin")

        # Set status to pending-operator to allow confirm
        src.web_ui.active_onboarding_job.status = "pending-operator"

        # 3. Confirm onboarding
        response = self.client.post('/api/sessions/onboard/confirm')
        self.assertEqual(response.status_code, 200)
        confirm_data = json.loads(response.data)
        self.assertEqual(confirm_data["message"], "Confirmation signal sent")
        self.assertEqual(src.web_ui.active_onboarding_job.action_type, "done")
        self.assertTrue(src.web_ui.active_onboarding_job.action_received.is_set())

        # 4. Cancel onboarding (should also succeed since job exists)
        # Reset action_received for testing cancel
        src.web_ui.active_onboarding_job.action_received.clear()
        src.web_ui.active_onboarding_job.action_type = None

        response = self.client.post('/api/sessions/onboard/cancel')
        self.assertEqual(response.status_code, 200)
        cancel_data = json.loads(response.data)
        self.assertEqual(cancel_data["message"], "Cancellation signal sent")
        self.assertEqual(src.web_ui.active_onboarding_job.action_type, "cancel")
        self.assertTrue(src.web_ui.active_onboarding_job.action_received.is_set())

    @patch('playwright.sync_api.sync_playwright')
    def test_api_sessions_clear(self, mock_playwright):
        # 1. Directory doesn't exist
        response = self.client.post('/api/sessions/clear', json={"platform": "linkedin"})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("Session cleared for linkedin", data["message"])
        
        # Check database is updated
        status = get_platform_sessions_status(self.db_path)
        self.assertEqual(status["linkedin"]["status"], "login-required")

        # 2. Directory exists, clear cookies
        os.makedirs(os.path.join(self.test_dir, ".browser_context"))
        
        mock_context = MagicMock()
        mock_p_instance = MagicMock()
        mock_p_instance.chromium.launch_persistent_context.return_value = mock_context
        mock_playwright.return_value.__enter__.return_value = mock_p_instance

        response = self.client.post('/api/sessions/clear', json={"platform": "facebook"})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("Session cleared for facebook", data["message"])
        
        mock_context.clear_cookies.assert_any_call(domain="facebook.com")
        mock_context.clear_cookies.assert_any_call(domain=".facebook.com")
        mock_context.close.assert_called_once()

        status = get_platform_sessions_status(self.db_path)
        self.assertEqual(status["facebook"]["status"], "login-required")

if __name__ == "__main__":
    unittest.main()
