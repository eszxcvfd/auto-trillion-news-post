import os
import json
import shutil
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from src.models import BusinessWorkbookRow
import src.web_ui as web_ui_module
from src.web_ui import app, ActiveJob
from src.config import AppConfig

class TestWebUI(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.old_cwd = os.getcwd()
        os.chdir(self.test_dir)
        
        # Setup AppConfig overrides via environment
        os.environ["EXCEL_FILE"] = os.path.join(self.test_dir, "Trillion $ news.xlsx")
        os.environ["OUTPUT_DIR"] = self.test_dir
        os.environ["IMAGE_DIR"] = os.path.join(self.test_dir, "images")
        os.environ["POST_DIR"] = os.path.join(self.test_dir, "posts")
        os.environ["LOG_DIR"] = os.path.join(self.test_dir, "logs")
        
        # Ensure template folder is accessed correctly
        app.template_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src', 'templates')
        
        self.client = app.test_client()

    def tearDown(self):
        web_ui_module.active_job = None
        os.chdir(self.old_cwd)
        shutil.rmtree(self.test_dir)
        if "EXCEL_FILE" in os.environ:
            del os.environ["EXCEL_FILE"]

    def test_root_route(self):
        # Even if templates directory isn't exactly aligned, test main page response
        # We patch render_template to make it template-directory independent
        with patch('src.web_ui.render_template') as mock_render:
            mock_render.return_value = "<html>Mock HTML</html>"
            response = self.client.get('/')
            self.assertEqual(response.status_code, 200)
            self.assertIn(b"Mock HTML", response.data)
            mock_render.assert_called_with('index.html')

    def test_api_config(self):
        response = self.client.get('/api/config')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("excel_file", data)
        self.assertIn("output_dir", data)
        self.assertEqual(data["output_dir"], os.path.abspath(self.test_dir))
        self.assertEqual(data["default_platform"], "linkedin")
        self.assertTrue(data["platform_locked"])
        self.assertEqual(data["supported_platforms"], ["linkedin"])

    def test_api_config_workbook_invalid(self):
        # Missing path resets to the canonical workbook
        response = self.client.post('/api/config/workbook', json={})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data["excel_file"].endswith("Trillion $ news.xlsx"))

        # Invalid extension
        response = self.client.post('/api/config/workbook', json={"path": "test.txt"})
        self.assertEqual(response.status_code, 400)

    def test_api_config_workbook_valid(self):
        canonical_path = os.path.join(self.test_dir, "Trillion $ news.xlsx")
        with open(canonical_path, "w") as f:
            f.write("")

        response = self.client.post('/api/config/workbook', json={"path": canonical_path})
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertEqual(data["excel_file"], os.path.abspath(canonical_path))
        self.assertEqual(os.environ["EXCEL_FILE"], os.path.abspath(canonical_path))

    def test_api_config_workbook_rejects_backup_file(self):
        backup_path = os.path.join(self.test_dir, "Trillion $ news.20260609_090724.xlsx")
        with open(backup_path, "w") as f:
            f.write("")

        response = self.client.post('/api/config/workbook', json={"path": backup_path})
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn("Backup workbooks cannot be used", data["error"])

    def test_api_workbooks(self):
        response = self.client.get('/api/workbooks')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)

        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["name"], "Trillion $ news.xlsx")
        self.assertTrue(data[0]["canonical"])

    def test_api_workbook_inspect_missing(self):
        response = self.client.get('/api/workbook/inspect')
        self.assertEqual(response.status_code, 404)

    @patch('src.web_ui.ingest_business_workbook')
    @patch('src.web_ui.detect_workbook_type')
    def test_api_workbook_inspect_legacy_error(self, mock_detect, mock_ingest):
        # Create a dummy workbook file to satisfy exists check
        filepath = os.environ["EXCEL_FILE"]
        with open(filepath, "w") as f:
            f.write("")
            
        mock_detect.return_value = "legacy"
        
        response = self.client.get('/api/workbook/inspect')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn("legacy Contract A", data["error"])

    @patch('src.web_ui.ingest_business_workbook')
    @patch('src.web_ui.detect_workbook_type')
    def test_api_workbook_inspect_success(self, mock_detect, mock_ingest):
        filepath = os.environ["EXCEL_FILE"]
        with open(filepath, "w") as f:
            f.write("")
            
        mock_detect.return_value = "business"
        
        # Mock rows returned
        mock_row = MagicMock()
        mock_row.sheet_name = "Payment"
        mock_row.row_idx = 2
        mock_row.id = 1
        mock_row.title = "Test Article"
        mock_row.image_link = "local_image.png"
        mock_row.link_post_raw = "LinkedIn: [pending]"
        mock_row.to_dict.return_value = {
            "id": 1,
            "title": "Test Article",
            "sheet_name": "Payment",
            "row_idx": 2,
            "image_link": "local_image.png",
            "link_post_raw": "LinkedIn: [pending]"
        }
        
        mock_ingest.return_value = ([mock_row], ["Ingest warning test"])
        
        response = self.client.get('/api/workbook/inspect')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        self.assertEqual(len(data["sheets"]), 1)
        self.assertEqual(data["sheets"][0]["name"], "Payment")
        self.assertEqual(len(data["sheets"][0]["rows"]), 1)
        self.assertIn("Ingest warning test", data["warnings"])

    def test_api_post_status_inactive(self):
        # Reset global active job
        with patch('src.web_ui.active_job', None):
            response = self.client.get('/api/post/status')
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertFalse(data["active"])

    def test_api_post_status_active_job(self):
        job = ActiveJob("linkedin", 1, "Payment", "Test Article")
        job.status = "pending-operator"
        with patch('src.web_ui.active_job', job):
            response = self.client.get('/api/post/status')
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertTrue(data["active"])
            self.assertEqual(data["job"]["status"], "pending-operator")

    def test_api_post_status_terminal_job_returns_inactive(self):
        job = ActiveJob("linkedin", 2, "Payment", "Test Article")
        job.status = "skipped"
        web_ui_module.active_job = job
        try:
            response = self.client.get('/api/post/status')
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertFalse(data["active"])
            self.assertEqual(data["job"]["status"], "skipped")
            self.assertIs(web_ui_module.active_job, job)
        finally:
            web_ui_module.active_job = None

    def test_api_post_skip_pending_operator_after_status_poll(self):
        job = ActiveJob("linkedin", 1, "Payment", "Test Article")
        job.status = "pending-operator"
        web_ui_module.active_job = job
        try:
            status_response = self.client.get('/api/post/status')
            self.assertTrue(json.loads(status_response.data)["active"])

            skip_response = self.client.post('/api/post/skip')
            self.assertEqual(skip_response.status_code, 200)
            data = json.loads(skip_response.data)
            self.assertEqual(data["job"]["platform"], "linkedin")
            self.assertTrue(job.skip_requested)
            self.assertEqual(job.action_type, "skip")
        finally:
            web_ui_module.active_job = None

    def test_api_post_skip_during_preparing_keeps_job_active(self):
        job = ActiveJob("linkedin", 1, "Payment", "Test Article")
        job.status = "preparing"
        web_ui_module.active_job = job
        try:
            skip_response = self.client.post('/api/post/skip')
            self.assertEqual(skip_response.status_code, 200)

            status_response = self.client.get('/api/post/status')
            data = json.loads(status_response.data)
            self.assertTrue(data["active"])
            self.assertEqual(data["job"]["status"], "preparing")
            self.assertTrue(job.skip_requested)
            self.assertIs(web_ui_module.active_job, job)
        finally:
            web_ui_module.active_job = None

    @patch('src.scheduler.start_manual_draft_run')
    def test_api_drafts_run_starts_manual_draft_run(self, mock_start_manual_draft_run):
        mock_start_manual_draft_run.return_value = "run-123"

        response = self.client.post('/api/drafts/run', json={
            "keywords_path": "keywords.txt",
            "platforms": "linkedin",
            "limit": 3,
        })

        self.assertEqual(response.status_code, 202)
        data = json.loads(response.data)
        self.assertEqual(data["run_id"], "run-123")
        self.assertIn("started", data["message"].lower())
        mock_start_manual_draft_run.assert_called_once()

    def test_api_drafts_run_rejects_invalid_limit(self):
        response = self.client.post('/api/drafts/run', json={"limit": 0})
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn("greater than 0", data["error"])

    def test_api_post_confirm_no_job(self):
        with patch('src.web_ui.active_job', None):
            response = self.client.post('/api/post/confirm', json={"url": "https://..."})
            self.assertEqual(response.status_code, 400)

    def test_api_post_skip_no_job(self):
        with patch('src.web_ui.active_job', None):
            response = self.client.post('/api/post/skip')
            self.assertEqual(response.status_code, 400)

    def test_api_post_confirm_completed_job_is_idempotent(self):
        job = ActiveJob("linkedin", 6, "Payment", "Test Article")
        job.status = "success"
        job.post_url = "https://linkedin.com/post/1"
        web_ui_module.active_job = job
        try:
            response = self.client.post('/api/post/confirm', json={"url": "https://example.com"})
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertIn("already completed", data["message"].lower())
        finally:
            web_ui_module.active_job = None

    def test_api_post_skip_completed_job_is_idempotent(self):
        job = ActiveJob("linkedin", 6, "Payment", "Test Article")
        job.status = "success"
        web_ui_module.active_job = job
        try:
            response = self.client.post('/api/post/skip')
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertIn("already completed", data["message"].lower())
        finally:
            web_ui_module.active_job = None

    @patch('src.web_ui.check_platform_session')
    def test_api_sessions(self, mock_check):
        mock_check.side_effect = lambda plat, cfg: "logged-in"
        
        response = self.client.get('/api/sessions')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["linkedin"], "logged-in")
        self.assertEqual(list(data.keys()), ["linkedin"])

    @patch('src.web_ui.write_post_result')
    def test_manual_write_result_missing_fields(self, mock_write):
        response = self.client.post('/api/write-result', json={})
        self.assertEqual(response.status_code, 400)

    @patch('src.web_ui.ingest_business_workbook')
    @patch('src.web_ui.detect_workbook_type')
    def test_api_workbook_inspect_includes_eligible_platforms(self, mock_detect, mock_ingest):
        filepath = os.environ["EXCEL_FILE"]
        with open(filepath, "w") as f:
            f.write("")

        mock_detect.return_value = "business"
        mock_row = BusinessWorkbookRow(
            sheet_name="Payment",
            row_idx=2,
            id=1,
            title="Test Article",
            linkedin_draft="LinkedIn draft",
            link_post_raw="LinkedIn: https://linkedin.com/post/1",
        )
        mock_ingest.return_value = ([mock_row], [])

        response = self.client.get('/api/workbook/inspect')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)

        row = data["sheets"][0]["rows"][0]
        self.assertEqual(row["eligible_platforms"], [])
        self.assertEqual(len(row["post_blockers"]), 1)
        self.assertEqual(row["post_blockers"][0]["platform"], "linkedin")

    @patch('src.web_ui.threading.Thread')
    @patch('src.web_ui.ingest_business_workbook')
    def test_api_post_rejects_ineligible_platform(self, mock_ingest, mock_thread):
        web_ui_module.active_job = None
        filepath = os.environ["EXCEL_FILE"]
        with open(filepath, "w") as f:
            f.write("")

        mock_row = BusinessWorkbookRow(
            sheet_name="Payment",
            row_idx=2,
            id=1,
            title="Test Article",
            linkedin_draft="LinkedIn draft",
            link_post_raw="LinkedIn: https://linkedin.com/post/1",
        )
        mock_ingest.return_value = ([mock_row], [])

        response = self.client.post('/api/post', json={
            "platform": "linkedin",
            "row_id": 1,
            "sheet_name": "Payment",
        })
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn("Already posted", data["error"])
        mock_thread.assert_not_called()

    @patch('src.web_ui.threading.Thread')
    @patch('src.web_ui.ingest_business_workbook')
    def test_api_post_dispatches_single_selected_platform(self, mock_ingest, mock_thread):
        web_ui_module.active_job = None
        filepath = os.environ["EXCEL_FILE"]
        with open(filepath, "w") as f:
            f.write("")

        mock_row = BusinessWorkbookRow(
            sheet_name="Payment",
            row_idx=2,
            id=1,
            title="Test Article",
            linkedin_draft="LinkedIn draft",
        )
        mock_ingest.return_value = ([mock_row], [])

        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance

        response = self.client.post('/api/post', json={
            "platform": "linkedin",
            "row_id": 1,
            "sheet_name": "Payment",
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["job"]["platform"], "linkedin")
        mock_thread.assert_called_once()
        mock_thread_instance.start.assert_called_once()

    @patch('src.web_ui.write_post_result')
    def test_manual_write_result_success(self, mock_write):
        # Make the workbook exists check pass
        filepath = os.environ["EXCEL_FILE"]
        with open(filepath, "w") as f:
            f.write("")
            
        mock_write.return_value = "LinkedIn: https://linkedin.com/post/1"
        
        response = self.client.post('/api/write-result', json={
            "sheet": "Payment",
            "row": 2,
            "platform": "linkedin",
            "status": "https://linkedin.com/post/1"
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("written to workbook", data["message"])
        self.assertEqual(data["new_value"], "LinkedIn: https://linkedin.com/post/1")

    def test_api_schedule_toggle_accepts_json_body(self):
        from src.scheduler import create_schedule

        config = AppConfig()
        db_path = os.path.join(config.output_dir, "scheduler.db")
        schedule_id = create_schedule(
            db_path,
            name="toggle-test",
            expression="0 9 * * *",
            job_type="draft",
        )

        # Frontend used to send Content-Type without a body; Flask rejects that.
        response = self.client.post(
            f"/api/schedules/{schedule_id}/toggle",
            headers={"Content-Type": "application/json"},
            data="",
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertFalse(data["enabled"])

        response = self.client.post(
            f"/api/schedules/{schedule_id}/toggle",
            json={"enabled": True},
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data["enabled"])

if __name__ == "__main__":
    unittest.main()
