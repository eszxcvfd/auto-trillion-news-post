import os
import json
import shutil
import tempfile
import unittest
from unittest.mock import patch, MagicMock

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

    def test_api_config_workbook_invalid(self):
        # Missing path
        response = self.client.post('/api/config/workbook', json={})
        self.assertEqual(response.status_code, 400)
        
        # Invalid extension
        response = self.client.post('/api/config/workbook', json={"path": "test.txt"})
        self.assertEqual(response.status_code, 400)

    def test_api_config_workbook_valid(self):
        test_path = "subfolder/another_workbook.xlsx"
        response = self.client.post('/api/config/workbook', json={"path": test_path})
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data["excel_file"], os.path.abspath(test_path))
        self.assertEqual(os.environ["EXCEL_FILE"], os.path.abspath(test_path))

    def test_api_workbooks(self):
        # Create a dummy workbook in test dir
        wb_path = os.path.join(self.test_dir, "test_wb.xlsx")
        with open(wb_path, "w") as f:
            f.write("")
            
        response = self.client.get('/api/workbooks')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        # Verify it lists the workbook
        wb_names = [wb["name"] for wb in data]
        self.assertIn("test_wb.xlsx", wb_names)

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

    def test_api_post_confirm_no_job(self):
        with patch('src.web_ui.active_job', None):
            response = self.client.post('/api/post/confirm', json={"url": "https://..."})
            self.assertEqual(response.status_code, 400)

    def test_api_post_skip_no_job(self):
        with patch('src.web_ui.active_job', None):
            response = self.client.post('/api/post/skip')
            self.assertEqual(response.status_code, 400)

    @patch('src.web_ui.check_platform_session')
    def test_api_sessions(self, mock_check):
        mock_check.side_effect = lambda plat, cfg: "logged-in" if plat == "linkedin" else "login-required"
        
        response = self.client.get('/api/sessions')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["linkedin"], "logged-in")
        self.assertEqual(data["facebook"], "login-required")
        self.assertEqual(data["instagram"], "unsupported")

    @patch('src.web_ui.write_post_result')
    def test_manual_write_result_missing_fields(self, mock_write):
        response = self.client.post('/api/write-result', json={})
        self.assertEqual(response.status_code, 400)

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

if __name__ == "__main__":
    unittest.main()
