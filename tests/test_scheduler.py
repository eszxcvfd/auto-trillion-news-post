import os
import shutil
import tempfile
import unittest
import datetime
import sqlite3
from unittest.mock import patch

from src.config import AppConfig
from src.scheduler import (
    init_db,
    calculate_next_run,
    create_schedule,
    update_schedule,
    delete_schedule,
    list_schedules,
    list_run_history,
    get_run_history_detail,
    get_active_manual_draft_run,
    run_schedule_job,
    run_manual_draft_job,
    start_manual_draft_run,
    trigger_due_schedules,
    get_db_connection
)

class TestScheduler(unittest.TestCase):
    def setUp(self):
        # Create temp folder for DB
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, "scheduler.db")
        self.config = AppConfig()
        
    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_calculate_next_run_intervals(self):
        start = datetime.datetime(2026, 6, 6, 12, 0, 0)
        
        # Minutes
        next_run = calculate_next_run("every 15m", start)
        self.assertEqual(next_run, datetime.datetime(2026, 6, 6, 12, 15, 0))
        
        # Hours
        next_run = calculate_next_run("every 2h", start)
        self.assertEqual(next_run, datetime.datetime(2026, 6, 6, 14, 0, 0))
        
        # Days
        next_run = calculate_next_run("every 1d", start)
        self.assertEqual(next_run, datetime.datetime(2026, 6, 7, 12, 0, 0))

    def test_calculate_next_run_cron(self):
        # Every 30 minutes
        start = datetime.datetime(2026, 6, 6, 12, 15, 0)
        next_run = calculate_next_run("*/30 * * * *", start)
        self.assertEqual(next_run, datetime.datetime(2026, 6, 6, 12, 30, 0))
        
        # Daily at 9:00 AM
        start = datetime.datetime(2026, 6, 6, 8, 0, 0)
        next_run = calculate_next_run("0 9 * * *", start)
        self.assertEqual(next_run, datetime.datetime(2026, 6, 6, 9, 0, 0))
        
        # Daily at 9:00 AM (start is after today's 9:00 AM)
        start = datetime.datetime(2026, 6, 6, 9, 30, 0)
        next_run = calculate_next_run("0 9 * * *", start)
        self.assertEqual(next_run, datetime.datetime(2026, 6, 7, 9, 0, 0))

    def test_db_init_and_crud(self):
        init_db(self.db_path)
        self.assertTrue(os.path.exists(self.db_path))
        
        # Verify empty schedules list
        schedules = list_schedules(self.db_path)
        self.assertEqual(len(schedules), 0)
        
        # Create schedule
        sch_id = create_schedule(
            self.db_path, 
            name="test-draft", 
            expression="0 * * * *", 
            job_type="draft",
            platforms="linkedin,facebook",
            post_limit=3
        )
        self.assertGreater(sch_id, 0)
        
        # List and verify
        schedules = list_schedules(self.db_path)
        self.assertEqual(len(schedules), 1)
        sch = schedules[0]
        self.assertEqual(sch["name"], "test-draft")
        self.assertEqual(sch["expression"], "0 * * * *")
        self.assertEqual(sch["job_type"], "draft")
        self.assertEqual(sch["platforms"], "linkedin")
        self.assertEqual(sch["post_limit"], 3)
        self.assertEqual(sch["enabled"], 1)
        self.assertIsNotNone(sch["next_run_at"])
        
        # Update schedule (expression change triggers next_run recalculation)
        update_schedule(self.db_path, name="test-draft", expression="*/30 * * * *", enabled=0)
        schedules = list_schedules(self.db_path)
        sch = schedules[0]
        self.assertEqual(sch["expression"], "*/30 * * * *")
        self.assertEqual(sch["enabled"], 0)
        
        # Delete schedule
        delete_schedule(self.db_path, sch["id"])
        schedules = list_schedules(self.db_path)
        self.assertEqual(len(schedules), 0)

    def test_history_logging_and_details(self):
        init_db(self.db_path)
        sch_id = create_schedule(
            self.db_path, 
            name="test-history", 
            expression="*/15 * * * *", 
            job_type="draft"
        )
        
        # Create a mock run directly in DB
        conn = get_db_connection(self.db_path)
        c = conn.cursor()
        run_uuid = "test-run-1234"
        c.execute("""
            INSERT INTO runs (schedule_id, run_id, status, trigger_type, started_at, finished_at, summary)
            VALUES (?, ?, 'completed', 'scheduled', '2026-06-06T12:00:00', '2026-06-06T12:05:00', 'Done')
        """, (sch_id, run_uuid))
        
        # Insert details
        c.execute("""
            INSERT INTO run_details (run_id, sheet_name, row_id, platform, status, message)
            VALUES (?, 'Payment', 2, 'linkedin', 'success', 'http://post.link')
        """, (run_uuid,))
        conn.commit()
        conn.close()
        
        # Query list history
        history = list_run_history(self.db_path)
        self.assertEqual(len(history), 1)
        run = history[0]
        self.assertEqual(run["schedule_name"], "test-history")
        self.assertEqual(run["run_id"], run_uuid)
        self.assertEqual(run["status"], "completed")
        self.assertEqual(run["summary"], "Done")
        
        # Query details
        detail = get_run_history_detail(self.db_path, run_uuid)
        self.assertIsNotNone(detail)
        self.assertEqual(detail["run_id"], run_uuid)
        self.assertEqual(len(detail["details"]), 1)
        det = detail["details"][0]
        self.assertEqual(det["sheet_name"], "Payment")
        self.assertEqual(det["row_id"], 2)
        self.assertEqual(det["platform"], "linkedin")
        self.assertEqual(det["status"], "success")
        self.assertEqual(det["message"], "http://post.link")

    def test_due_triggers(self):
        init_db(self.db_path)
        
        # Create a schedule that is due (next_run_at in past)
        sch_id_due = create_schedule(
            self.db_path, 
            name="due-job", 
            expression="*/15 * * * *", 
            job_type="draft"
        )
        
        # Create a schedule that is not due (next_run_at in future)
        sch_id_future = create_schedule(
            self.db_path, 
            name="future-job", 
            expression="0 9 * * *", 
            job_type="draft"
        )
        
        # Artificially set next_run_at for due-job in past
        conn = get_db_connection(self.db_path)
        c = conn.cursor()
        c.execute("UPDATE schedules SET next_run_at = '2026-05-01T00:00:00' WHERE id = ?", (sch_id_due,))
        # Artificially set next_run_at for future-job in future
        c.execute("UPDATE schedules SET next_run_at = '2026-07-01T00:00:00' WHERE id = ?", (sch_id_future,))
        conn.commit()
        conn.close()
        
        # Call trigger_due_schedules (should launch due-job in background thread)
        # We can test run_schedule_job directly to verify behavior without waiting for thread
        from unittest.mock import patch
        with patch("main.execute_run") as mock_execute_run:
            mock_execute_run.return_value = []
            run_schedule_job(self.db_path, sch_id_due, "scheduled", self.config)
        
        # Verify run was created and marked as completed/failed
        history = list_run_history(self.db_path)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["schedule_id"], sch_id_due)

    def test_manual_draft_run_records_history(self):
        keywords_path = os.path.join(self.test_dir, "keywords.txt")
        with open(keywords_path, "w", encoding="utf-8") as f:
            f.write("Fintech trillion $\n")

        with patch("main.execute_run") as mock_execute_run:
            mock_execute_run.return_value = None
            run_manual_draft_job(
                self.db_path,
                self.config,
                keywords_path=keywords_path,
                platforms=["linkedin"],
                limit=2,
                explicit_run_id="manual-draft-1",
            )

        history = list_run_history(self.db_path)
        self.assertEqual(len(history), 1)
        run = history[0]
        self.assertIsNone(run["schedule_id"])
        self.assertEqual(run["trigger_type"], "manual")
        self.assertEqual(run["status"], "completed")
        self.assertIn("Platform runs succeeded: 1", run["summary"])

        detail = get_run_history_detail(self.db_path, "manual-draft-1")
        self.assertIsNotNone(detail)
        self.assertEqual(len(detail["details"]), 1)
        self.assertEqual(detail["details"][0]["platform"], "linkedin")
        self.assertEqual(detail["details"][0]["status"], "success")

    def test_start_manual_draft_run_rejects_overlap(self):
        init_db(self.db_path)
        conn = get_db_connection(self.db_path)
        c = conn.cursor()
        c.execute("""
            INSERT INTO runs (schedule_id, run_id, status, trigger_type, started_at)
            VALUES (NULL, 'manual-running', 'running', 'manual', '2026-06-09T10:00:00')
        """)
        conn.commit()
        conn.close()

        active_run = get_active_manual_draft_run(self.db_path)
        self.assertIsNotNone(active_run)
        self.assertEqual(active_run["run_id"], "manual-running")

        with self.assertRaises(ValueError):
            start_manual_draft_run(self.db_path, self.config)

if __name__ == "__main__":
    unittest.main()
