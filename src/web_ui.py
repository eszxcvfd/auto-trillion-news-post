import os
import sys
import uuid
import time
import threading
from typing import Dict, Any, Optional
from flask import Flask, jsonify, request, send_from_directory, render_template

from src.config import AppConfig
from src.models import NewsItem
from src.business_workbook import detect_workbook_type, ingest_business_workbook
from src.posting_core import build_posting_plan, canonicalize_platform, PLATFORM_ATTRS
from src.writeback import write_post_result
from src.assisted_posting import run_assisted_posting

app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), 'templates'))

# Global active job tracking
active_job = None
active_job_lock = threading.Lock()

class ActiveJob:
    def __init__(self, platform: str, row_id: int, sheet_name: str, title: str):
        self.job_id = str(uuid.uuid4())
        self.platform = platform
        self.row_id = row_id
        self.sheet_name = sheet_name
        self.title = title
        self.status = "preparing"  # preparing, pending-operator, success, skipped, error
        self.error_message = None
        self.post_url = None
        
        # Coordination
        self.action_received = threading.Event()
        self.action_type = None  # "confirm" or "skip"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "platform": self.platform,
            "row_id": self.row_id,
            "sheet_name": self.sheet_name,
            "title": self.title,
            "status": self.status,
            "error_message": self.error_message,
            "post_url": self.post_url
        }

@app.route('/')
def index():
    """Serves the main frontend page."""
    return render_template('index.html')

@app.route('/api/config', methods=['GET'])
def get_config():
    """Returns the current application configuration."""
    config = AppConfig()
    return jsonify({
        "excel_file": os.path.abspath(config.excel_file),
        "output_dir": os.path.abspath(config.output_dir),
        "image_dir": os.path.abspath(config.image_dir),
        "post_dir": os.path.abspath(config.post_dir),
        "log_dir": os.path.abspath(config.log_dir),
        "default_platform": config.default_platform
    })

@app.route('/api/config/workbook', methods=['POST'])
def update_workbook():
    """Updates the active workbook path."""
    data = request.json or {}
    path = data.get("path")
    if not path:
        return jsonify({"error": "Path is required"}), 400
        
    # Standardize path
    abs_path = os.path.abspath(path)
    if not abs_path.endswith('.xlsx'):
        return jsonify({"error": "Workbook must be an .xlsx file"}), 400
        
    # Since config is read from environment/AppConfig, we update environment variable
    # to let AppConfig pick it up dynamically for subsequent calls
    os.environ["EXCEL_FILE"] = abs_path
    
    return jsonify({
        "message": "Active workbook path updated",
        "excel_file": abs_path
    })

@app.route('/api/workbooks', methods=['GET'])
def list_workbooks():
    """Scans and lists all Excel files in the workspace and output directory."""
    config = AppConfig()
    workbooks = []
    
    dirs_to_scan = [
        ".",
        config.output_dir
    ]
    
    seen_paths = set()
    for d in dirs_to_scan:
        if not os.path.exists(d):
            continue
        try:
            for f in os.listdir(d):
                if f.endswith('.xlsx') and not f.startswith('~$'):
                    full_path = os.path.abspath(os.path.join(d, f))
                    if full_path not in seen_paths:
                        seen_paths.add(full_path)
                        workbooks.append({
                            "name": f,
                            "path": full_path,
                            "folder": os.path.basename(os.path.abspath(d))
                        })
        except Exception:
            pass
            
    return jsonify(workbooks)

@app.route('/api/workbook/inspect', methods=['GET'])
def inspect_workbook():
    """Reads the active business workbook and returns sheets and rows."""
    config = AppConfig()
    filepath = config.excel_file
    
    if not os.path.exists(filepath):
        return jsonify({
            "error": "Workbook does not exist",
            "path": os.path.abspath(filepath),
            "sheets": []
        }), 404
        
    try:
        wb_type = detect_workbook_type(filepath)
    except Exception as e:
        return jsonify({
            "error": f"Failed to detect workbook type: {e}",
            "path": os.path.abspath(filepath),
            "sheets": []
        }), 400
        
    if wb_type == "legacy":
        return jsonify({
            "error": "The active file is a legacy Contract A workbook. Please convert it first.",
            "path": os.path.abspath(filepath),
            "sheets": []
        }), 400
        
    try:
        rows, warnings = ingest_business_workbook(filepath)
        
        # Group rows by sheet
        sheets_dict = {}
        for r in rows:
            if r.sheet_name not in sheets_dict:
                sheets_dict[r.sheet_name] = []
            sheets_dict[r.sheet_name].append(r.to_dict())
            
        sheets_list = []
        for name, r_list in sheets_dict.items():
            sheets_list.append({
                "name": name,
                "rows": r_list
            })
            
        return jsonify({
            "path": os.path.abspath(filepath),
            "sheets": sheets_list,
            "warnings": warnings
        })
    except Exception as e:
        return jsonify({
            "error": f"Failed to inspect workbook: {e}",
            "path": os.path.abspath(filepath)
        }), 500

@app.route('/api/plan', methods=['GET'])
def get_plan():
    """Generates the posting plan (dry-run) for the active workbook."""
    config = AppConfig()
    filepath = config.excel_file
    limit = request.args.get("limit", default=2, type=int)
    platforms_str = request.args.get("platforms", default="linkedin,facebook,x,instagram,pinterest,threads,tiktok,youtube")
    platforms = [p.strip() for p in platforms_str.split(",") if p.strip()]
    
    if not os.path.exists(filepath):
        return jsonify({"error": "Active workbook does not exist"}), 404
        
    try:
        rows, _ = ingest_business_workbook(filepath)
        plan = build_posting_plan(rows, platforms, limit_per_platform=limit)
        return jsonify(plan.to_dict())
    except Exception as e:
        return jsonify({"error": f"Failed to build posting plan: {e}"}), 500

@app.route('/api/sessions', methods=['GET'])
def get_sessions():
    """Checks the login session status for LinkedIn (and placeholder check for others)."""
    config = AppConfig()
    
    results = {}
    platforms = ["linkedin", "facebook", "x"]
    
    # We check LinkedIn status
    results["linkedin"] = check_platform_session("linkedin", config)
    results["facebook"] = check_platform_session("facebook", config)
    results["x"] = check_platform_session("x", config)
    
    # Rest are uncheckable/unsupported for now
    for p in ["instagram", "pinterest", "threads", "tiktok", "youtube"]:
        results[p] = "unsupported"
        
    return jsonify(results)

def check_platform_session(platform: str, config: AppConfig) -> str:
    """Helper to check login session for a platform in headless mode."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return "error"
        
    browser_context_dir = os.path.abspath(os.path.join(config.output_dir, ".browser_context"))
    if not os.path.exists(browser_context_dir):
        return "login-required"
        
    launch_kwargs = {
        "user_data_dir": browser_context_dir,
        "headless": True,
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "viewport": {"width": 1280, "height": 800},
        "args": ["--disable-extensions"],
        "locale": "en-US",
    }
    if getattr(config, "playwright_chromium_executable_path", None):
        launch_kwargs["executable_path"] = config.playwright_chromium_executable_path
        
    try:
        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(**launch_kwargs)
            page = context.new_page() if not context.pages else context.pages[0]
            
            if platform == "linkedin":
                page.goto("https://www.linkedin.com/feed/", timeout=15000)
                # Check for start post triggers
                start_post_selectors = [
                    "button.share-box-feed-entry__trigger",
                    "button:has-text('Start a post')",
                    "button:has-text('Đăng bài viết')",
                    "div.share-box-feed-entry__trigger"
                ]
                logged_in = False
                for sel in start_post_selectors:
                    try:
                        elem = page.query_selector(sel)
                        if elem and elem.is_visible():
                            logged_in = True
                            break
                    except Exception:
                        pass
                if not logged_in:
                    if "feed" in page.url or page.query_selector("#global-nav") or page.query_selector(".global-nav"):
                        logged_in = True
                        
                context.close()
                return "logged-in" if logged_in else "login-required"
                
            elif platform == "facebook":
                page.goto("https://www.facebook.com/", timeout=15000)
                # If we see login input fields, we are logged out
                is_logged_out = page.query_selector("input[name='email']") or "login" in page.url
                context.close()
                return "login-required" if is_logged_out else "logged-in"
                
            elif platform == "x":
                page.goto("https://x.com/home", timeout=15000)
                # If we are redirected to x.com/login or see sign-in selectors
                is_logged_out = "login" in page.url or page.query_selector("[data-testid='loginButton']")
                context.close()
                return "login-required" if is_logged_out else "logged-in"
                
            context.close()
            return "unsupported"
    except Exception as e:
        print(f"[ERROR] Session check failed for {platform}: {e}", file=sys.stderr)
        return "error"

@app.route('/api/post/status', methods=['GET'])
def get_post_status():
    """Gets the status of the current active posting job."""
    global active_job
    with active_job_lock:
        if active_job is not None:
            return jsonify({
                "active": True,
                "job": active_job.to_dict()
            })
            
    # Try scheduler job
    from src.scheduler import scheduler_active_job, scheduler_active_job_lock
    with scheduler_active_job_lock:
        if scheduler_active_job is not None:
            return jsonify({
                "active": True,
                "job": scheduler_active_job.to_dict()
            })
            
    return jsonify({"active": False})

@app.route('/api/post', methods=['POST'])
def start_post():
    """Triggers assisted posting for a specific row and platform."""
    global active_job
    data = request.json or {}
    platform = data.get("platform")
    row_id = data.get("row_id")
    sheet_name = data.get("sheet_name")
    
    if not platform or row_id is None or not sheet_name:
        return jsonify({"error": "platform, row_id, and sheet_name are required"}), 400
        
    try:
        row_id = int(row_id)
    except ValueError:
        return jsonify({"error": "row_id must be an integer"}), 400
        
    config = AppConfig()
    filepath = config.excel_file
    
    if not os.path.exists(filepath):
        return jsonify({"error": "Active workbook does not exist"}), 404
        
    # Check if a job is already in progress
    with active_job_lock:
        if active_job is not None and active_job.status in ["preparing", "pending-operator"]:
            return jsonify({"error": "A posting job is already in progress"}), 400
            
        # Verify row exists and platform content is valid
        try:
            rows, _ = ingest_business_workbook(filepath, sheet_scope=[sheet_name])
            matching_rows = [r for r in rows if r.id == row_id]
            if not matching_rows:
                return jsonify({"error": f"Row ID {row_id} not found in sheet '{sheet_name}'"}), 404
                
            row = matching_rows[0]
            platform_key = canonicalize_platform(platform)
            attr_name = PLATFORM_ATTRS.get(platform_key)
            draft_content = getattr(row, attr_name, None)
            
            if not draft_content:
                return jsonify({"error": f"No draft content for '{platform}' on row {row_id}"}), 400
                
            # Initialize active job
            active_job = ActiveJob(platform, row_id, sheet_name, row.title)
        except Exception as e:
            return jsonify({"error": str(e)}), 400
            
    # Start background thread to run assisted posting
    thread = threading.Thread(target=run_posting_in_background, args=(active_job, row, draft_content, filepath, config))
    thread.daemon = True
    thread.start()
    
    return jsonify({
        "message": "Posting job started",
        "job": active_job.to_dict()
    })

def run_posting_in_background(job: ActiveJob, row: Any, draft_content: str, filepath: str, config: AppConfig):
    """Target for the background posting thread."""
    try:
        # Resolve draft_content if it points to a file path
        if draft_content and isinstance(draft_content, str):
            test_paths = [
                draft_content,
                os.path.join(os.path.dirname(filepath), draft_content) if filepath else "",
                os.path.join(config.post_dir, os.path.basename(draft_content)) if hasattr(config, "post_dir") else ""
            ]
            for p in test_paths:
                if p and os.path.exists(p) and os.path.isfile(p):
                    from src.assisted_posting import parse_post_markdown
                    parsed = parse_post_markdown(p)
                    if parsed:
                        draft_content = parsed
                        break

        # Construct NewsItem wrapper for run_assisted_posting
        item = NewsItem(
            id=row.id,
            title=row.title,
            image_file=row.image_link,
            platform=job.platform,
            status="new"
        )
        
        # Callback to execute when browser is ready and waiting for operator action
        def confirm_callback():
            job.status = "pending-operator"
            # Block this background thread until API sets job.action_received
            job.action_received.wait()
            if job.action_type == "confirm":
                return True, job.post_url
            else:
                return False, None
                
        print(f"[WEB UI] Launching assisted posting for ID {row.id} on '{job.platform}'...")
        success = run_assisted_posting(item, config, post_content=draft_content, confirm_callback=confirm_callback)
        
        if success:
            url_input = getattr(item, "post_url", "").strip()
            status_val = url_input if url_input else "[posted-no-link]"
            
            write_post_result(
                workbook_path=filepath,
                sheet_name=row.sheet_name,
                row_idx=row.row_idx,
                platform=job.platform,
                status_value=status_val,
                backup_enabled=config.backup_enabled
            )
            job.status = "success"
            job.post_url = status_val
            print(f"[WEB UI SUCCESS] Successfully wrote posting result to Excel for row {row.id}")
        else:
            if job.action_type == "skip":
                write_post_result(
                    workbook_path=filepath,
                    sheet_name=row.sheet_name,
                    row_idx=row.row_idx,
                    platform=job.platform,
                    status_value="[skip] skipped by operator",
                    backup_enabled=config.backup_enabled
                )
                job.status = "skipped"
                print(f"[WEB UI SKIPPED] Job for row {row.id} was explicitly skipped by operator")
            else:
                job.status = "error"
                job.error_message = "Post was not completed or confirmation timed out."
                print(f"[WEB UI ERROR] Post for row {row.id} was not confirmed as posted.")
                
    except Exception as e:
        job.status = "error"
        job.error_message = str(e)
        print(f"[WEB UI ERROR] Background job error: {e}", file=sys.stderr)

@app.route('/api/post/confirm', methods=['POST'])
def confirm_post():
    """Signals the waiting posting thread that the post was successfully published."""
    global active_job
    data = request.json or {}
    url = data.get("url", "").strip()
    
    with active_job_lock:
        if active_job is not None:
            if active_job.status != "pending-operator":
                return jsonify({"error": f"Job is not in pending-operator state (current status: {active_job.status})"}), 400
                
            active_job.post_url = url
            active_job.action_type = "confirm"
            active_job.action_received.set()
            
            return jsonify({
                "message": "Confirmation signal sent",
                "job": active_job.to_dict()
            })
            
    # Try scheduler job
    from src.scheduler import scheduler_active_job, scheduler_active_job_lock
    with scheduler_active_job_lock:
        if scheduler_active_job is not None:
            if scheduler_active_job.status != "pending-operator":
                return jsonify({"error": f"Job is not in pending-operator state (current status: {scheduler_active_job.status})"}), 400
                
            scheduler_active_job.post_url = url
            scheduler_active_job.action_type = "confirm"
            scheduler_active_job.action_received.set()
            
            return jsonify({
                "message": "Confirmation signal sent",
                "job": scheduler_active_job.to_dict()
            })
            
    return jsonify({"error": "No active posting job"}), 400

@app.route('/api/post/skip', methods=['POST'])
def skip_post():
    """Signals the waiting posting thread to skip/cancel the current post."""
    global active_job
    with active_job_lock:
        if active_job is not None:
            if active_job.status != "pending-operator" and active_job.status != "preparing":
                pass
                
            active_job.action_type = "skip"
            active_job.action_received.set()
            
            # If it was in preparing (not yet waiting on confirm_callback), we can force status to skipped
            if active_job.status == "preparing":
                active_job.status = "skipped"
                
            return jsonify({
                "message": "Skip/cancel signal sent",
                "job": active_job.to_dict()
            })
            
    # Try scheduler job
    from src.scheduler import scheduler_active_job, scheduler_active_job_lock
    with scheduler_active_job_lock:
        if scheduler_active_job is not None:
            if scheduler_active_job.status != "pending-operator" and scheduler_active_job.status != "preparing":
                pass
                
            scheduler_active_job.action_type = "skip"
            scheduler_active_job.action_received.set()
            
            # If it was in preparing, force status to skipped
            if scheduler_active_job.status == "preparing":
                scheduler_active_job.status = "skipped"
                
            return jsonify({
                "message": "Skip/cancel signal sent",
                "job": scheduler_active_job.to_dict()
            })
            
    return jsonify({"error": "No active posting job"}), 400

@app.route('/api/write-result', methods=['POST'])
def manual_write_result():
    """Manually writes a posting result back to a row."""
    data = request.json or {}
    sheet = data.get("sheet")
    row = data.get("row")
    platform = data.get("platform")
    status = data.get("status")
    
    if not sheet or row is None or not platform or status is None:
        return jsonify({"error": "sheet, row, platform, and status are required"}), 400
        
    try:
        row = int(row)
    except ValueError:
        return jsonify({"error": "row must be an integer"}), 400
        
    config = AppConfig()
    filepath = config.excel_file
    
    if not os.path.exists(filepath):
        return jsonify({"error": "Active workbook does not exist"}), 404
        
    try:
        new_val = write_post_result(
            workbook_path=filepath,
            sheet_name=sheet,
            row_idx=row,
            platform=platform,
            status_value=status,
            backup_enabled=config.backup_enabled
        )
        return jsonify({
            "message": "Posting result written to workbook",
            "new_value": new_val
        })
    except Exception as e:
        return jsonify({"error": f"Failed to write result: {e}"}), 500

# --- Scheduler API Endpoints ---

@app.route('/api/schedules', methods=['GET'])
def get_schedules():
    """Lists all schedule definitions."""
    config = AppConfig()
    db_path = os.path.join(config.output_dir, "scheduler.db")
    from src.scheduler import list_schedules
    try:
        schedules = list_schedules(db_path)
        return jsonify(schedules)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/schedules', methods=['POST'])
def add_schedule():
    """Creates a new schedule definition."""
    data = request.json or {}
    name = data.get("name")
    expression = data.get("expression")
    job_type = data.get("job_type")
    
    if not name or not expression or not job_type:
        return jsonify({"error": "name, expression, and job_type are required"}), 400
        
    if job_type not in ["draft", "post"]:
        return jsonify({"error": "job_type must be 'draft' or 'post'"}), 400
        
    config = AppConfig()
    db_path = os.path.join(config.output_dir, "scheduler.db")
    from src.scheduler import create_schedule
    try:
        schedule_id = create_schedule(
            db_path=db_path,
            name=name,
            expression=expression,
            job_type=job_type,
            workbook_path=data.get("workbook_path"),
            sheet_name=data.get("sheet_name"),
            platforms=data.get("platforms"),
            post_limit=data.get("post_limit", 2)
        )
        return jsonify({"message": "Schedule created", "id": schedule_id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/schedules/<int:id>/toggle', methods=['POST'])
def toggle_schedule(id):
    """Enables or disables a schedule definition."""
    config = AppConfig()
    db_path = os.path.join(config.output_dir, "scheduler.db")
    
    import sqlite3
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT name, enabled FROM schedules WHERE id = ?", (id,))
    sch = c.fetchone()
    conn.close()
    
    if not sch:
        return jsonify({"error": f"Schedule ID {id} not found"}), 404
        
    data = request.json or {}
    enabled_val = data.get("enabled")
    if enabled_val is None:
        new_enabled = 0 if sch["enabled"] == 1 else 1
    else:
        new_enabled = 1 if enabled_val else 0
        
    from src.scheduler import update_schedule
    try:
        update_schedule(db_path, sch["name"], enabled=new_enabled)
        return jsonify({
            "message": f"Schedule '{sch['name']}' {'enabled' if new_enabled == 1 else 'disabled'}",
            "enabled": new_enabled == 1
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/schedules/<int:id>/run', methods=['POST'])
def trigger_schedule(id):
    """Manually triggers a schedule execution in the background."""
    config = AppConfig()
    db_path = os.path.join(config.output_dir, "scheduler.db")
    
    import sqlite3
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT id FROM schedules WHERE id = ?", (id,))
    sch = c.fetchone()
    conn.close()
    
    if not sch:
        return jsonify({"error": f"Schedule ID {id} not found"}), 404
        
    from src.scheduler import run_schedule_now
    try:
        run_id = run_schedule_now(db_path, id, config)
        return jsonify({
            "message": "Schedule run triggered in background",
            "run_id": run_id
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/schedules/<int:id>', methods=['DELETE'])
def remove_schedule(id):
    """Deletes a schedule definition."""
    config = AppConfig()
    db_path = os.path.join(config.output_dir, "scheduler.db")
    
    import sqlite3
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT id FROM schedules WHERE id = ?", (id,))
    sch = c.fetchone()
    conn.close()
    
    if not sch:
        return jsonify({"error": f"Schedule ID {id} not found"}), 404
        
    from src.scheduler import delete_schedule
    try:
        delete_schedule(db_path, id)
        return jsonify({"message": "Schedule deleted"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/history', methods=['GET'])
def get_history():
    """Lists all schedule run executions."""
    config = AppConfig()
    db_path = os.path.join(config.output_dir, "scheduler.db")
    limit = request.args.get("limit", default=50, type=int)
    from src.scheduler import list_run_history
    try:
        history = list_run_history(db_path, limit=limit)
        return jsonify(history)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/history/<run_id>', methods=['GET'])
def get_history_detail(run_id):
    """Gets details for a specific run execution, including row-level outcomes."""
    config = AppConfig()
    db_path = os.path.join(config.output_dir, "scheduler.db")
    from src.scheduler import get_run_history_detail
    try:
        detail = get_run_history_detail(db_path, run_id)
        if not detail:
            return jsonify({"error": f"Run ID {run_id} not found"}), 404
        return jsonify(detail)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def start_web_server(port: int = 8080):
    """Starts the Flask development server."""
    print(f"=== Starting local Web UI Operator Surface on http://localhost:{port} ===")
    config = AppConfig()
    db_path = os.path.join(config.output_dir, "scheduler.db")
    from src.scheduler import SchedulerDaemon
    daemon = SchedulerDaemon(db_path, config)
    daemon.start()
    try:
        app.run(host="localhost", port=port, debug=False)
    finally:
        daemon.stop()
