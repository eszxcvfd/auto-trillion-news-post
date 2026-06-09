import os
import sys
import uuid
import time
import threading
import datetime
from typing import Dict, Any, Optional
from flask import Flask, jsonify, request, send_from_directory, render_template

from src.config import AppConfig, load_dotenv
from src.env_settings_store import read_env_settings, resolve_env_path, save_env_settings
from src.models import NewsItem
from src.business_workbook import (
    delete_workbook_row,
    detect_workbook_type,
    filter_dashboard_workbook_rows,
    ingest_business_workbook,
    regenerate_linkedin_draft_for_row,
)
from src.keywords_store import (
    KeywordRecord,
    keyword_records_to_api,
    load_keyword_records,
    normalize_keyword_records,
    resolve_keywords_path,
    save_keyword_records,
)
from src.platform_capabilities import (
    PROJECT_DEFAULT_PLATFORM,
    PROJECT_DEFAULT_PLATFORM_LABEL,
    PROJECT_SUPPORTED_PLATFORM_CSV,
    SUPPORTED_SESSION_PLATFORMS,
    SESSION_DOMAINS,
    SESSION_LOGIN_URLS,
    normalize_project_platform,
    normalize_project_platforms_csv,
)
from src.posting_core import (
    build_posting_plan,
    filter_link_post_for_project_scope,
    list_eligible_platforms,
    list_row_post_blockers,
    resolve_manual_post_target,
    PLATFORM_CANONICAL,
)
from src.writeback import (
    CANONICAL_WORKBOOK_FILENAME,
    canonical_workbook_path,
    is_timestamped_workbook_backup,
    resolve_workbook_path,
    write_post_result,
)
from src.assisted_posting import run_assisted_posting
from src.post_draft_store import (
    linkedin_draft_file_for_row,
    list_post_drafts,
    post_draft_detail_to_api,
    post_draft_record_to_api,
    read_post_draft,
    resolve_post_dir,
    save_post_draft,
)

app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), 'templates'))


def _row_to_api_dict(row, config: AppConfig, workbook_path: str) -> Dict[str, Any]:
    """Serialize a workbook row with eligible manual-post platform targets."""
    row_dict = row.to_dict()
    row_dict["link_post_raw"] = filter_link_post_for_project_scope(row_dict.get("link_post_raw"))
    row_dict["eligible_platforms"] = [
        {"platform": platform_key, "label": PLATFORM_CANONICAL[platform_key]}
        for platform_key, _ in list_eligible_platforms(
            row,
            config=config,
            workbook_path=workbook_path,
            manual_retry=True,
        )
    ]
    row_dict["post_blockers"] = list_row_post_blockers(
        row,
        config=config,
        workbook_path=workbook_path,
        manual_retry=True,
    )
    row_dict["linkedin_draft_file"] = linkedin_draft_file_for_row(
        getattr(row, "linkedin_draft_ref", None),
        config,
    )
    return row_dict

# Global active job tracking
active_job = None
active_job_lock = threading.Lock()

ACTIVE_POSTING_STATUSES = ("preparing", "pending-operator")
TERMINAL_POSTING_STATUSES = ("success", "skipped", "error")


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
        self.skip_requested = False

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

    def is_active(self) -> bool:
        return self.status in ACTIVE_POSTING_STATUSES


def _release_active_job(job: ActiveJob) -> None:
    """Keep the terminal job visible for operator UI until the next post starts."""
    return

# Global active onboarding tracking
active_onboarding_job = None
active_onboarding_job_lock = threading.Lock()

class OnboardingJob:
    def __init__(self, platform: str):
        self.job_id = str(uuid.uuid4())
        self.platform = platform
        self.status = "preparing"  # preparing, pending-operator, success, error
        self.error_message = None
        
        # Coordination
        self.action_received = threading.Event()
        self.action_type = None  # "done" or "cancel"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "platform": self.platform,
            "status": self.status,
            "error_message": self.error_message
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
        "default_platform": config.default_platform,
        "default_platform_label": PROJECT_DEFAULT_PLATFORM_LABEL,
        "supported_platforms": [PROJECT_DEFAULT_PLATFORM],
        "platform_locked": True,
    })

@app.route('/api/settings', methods=['GET'])
def get_settings():
    """Return operator-editable .env settings."""
    return jsonify(read_env_settings())


@app.route('/api/settings', methods=['PUT'])
def update_settings():
    """Persist operator settings to the active .env file."""
    data = request.json or {}
    payload = data.get("settings", data)
    try:
        saved = save_env_settings(payload)
        load_dotenv(resolve_env_path())
        return jsonify({
            **saved,
            "message": "Settings saved. Some changes apply on the next action or restart.",
        })
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except OSError as exc:
        return jsonify({"error": f"Failed to write settings: {exc}"}), 500


@app.route('/api/config/workbook', methods=['POST'])
def update_workbook():
    """Pin the active workbook to the canonical Trillion $ news.xlsx file."""
    config = AppConfig()
    data = request.json or {}
    path = data.get("path")
    canonical_path = canonical_workbook_path(config.output_dir)

    if path:
        abs_path = os.path.abspath(path)
        if not abs_path.endswith('.xlsx'):
            return jsonify({"error": "Workbook must be an .xlsx file"}), 400
        if is_timestamped_workbook_backup(abs_path):
            return jsonify({
                "error": (
                    "Backup workbooks cannot be used as the active workbook. "
                    f"Use '{CANONICAL_WORKBOOK_FILENAME}' only."
                )
            }), 400
        if os.path.basename(abs_path) != CANONICAL_WORKBOOK_FILENAME:
            return jsonify({
                "error": (
                    f"Only the canonical workbook '{CANONICAL_WORKBOOK_FILENAME}' "
                    "is supported for operator flows."
                )
            }), 400
        if abs_path != canonical_path:
            return jsonify({
                "error": (
                    f"Active workbook must remain at '{canonical_path}'."
                )
            }), 400

    os.environ["EXCEL_FILE"] = canonical_path

    return jsonify({
        "message": "Active workbook path updated",
        "excel_file": canonical_path
    })

@app.route('/api/workbooks', methods=['GET'])
def list_workbooks():
    """Return the single canonical operator workbook."""
    config = AppConfig()
    canonical_path = resolve_workbook_path(config.output_dir, config.excel_file)
    os.environ["EXCEL_FILE"] = canonical_path

    return jsonify([
        {
            "name": CANONICAL_WORKBOOK_FILENAME,
            "path": canonical_path,
            "folder": os.path.basename(os.path.abspath(config.output_dir)),
            "canonical": True,
        }
    ])

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
        rows = filter_dashboard_workbook_rows(rows)
        
        # Group rows by sheet
        sheets_dict = {}
        for r in rows:
            if r.sheet_name not in sheets_dict:
                sheets_dict[r.sheet_name] = []
            sheets_dict[r.sheet_name].append(_row_to_api_dict(r, config, filepath))
            
        sheets_list = []
        for name, r_list in sheets_dict.items():
            sheets_list.append({
                "name": name,
                "rows": r_list
            })
            
        modified_at = None
        try:
            modified_at = datetime.datetime.fromtimestamp(
                os.path.getmtime(filepath)
            ).isoformat()
        except OSError:
            pass

        return jsonify({
            "path": os.path.abspath(filepath),
            "modified_at": modified_at,
            "sheets": sheets_list,
            "warnings": warnings
        })
    except Exception as e:
        return jsonify({
            "error": f"Failed to inspect workbook: {e}",
            "path": os.path.abspath(filepath)
        }), 500

@app.route('/api/posts', methods=['GET'])
def list_posts_api():
    """List markdown post drafts under POST_DIR."""
    config = AppConfig()
    query = request.args.get("q", default="", type=str)
    records = list_post_drafts(config, query=query.strip() or None)
    return jsonify({
        "post_dir": resolve_post_dir(config=config),
        "posts": [post_draft_record_to_api(record) for record in records],
        "count": len(records),
    })


@app.route('/api/posts/<path:relative_path>', methods=['GET'])
def get_post_draft_api(relative_path: str):
    """Return one post draft with parsed sections for the editor."""
    config = AppConfig()
    try:
        detail = read_post_draft(config, relative_path)
        return jsonify(post_draft_detail_to_api(detail))
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": f"Failed to read post draft: {e}"}), 500


@app.route('/api/posts/<path:relative_path>', methods=['PUT'])
def put_post_draft_api(relative_path: str):
    """Save the Generated Post body for one markdown draft."""
    config = AppConfig()
    data = request.get_json(silent=True) or {}
    generated_post = data.get("generated_post")
    if generated_post is None:
        return jsonify({"error": "generated_post is required"}), 400
    if not isinstance(generated_post, str):
        return jsonify({"error": "generated_post must be a string"}), 400

    try:
        detail = save_post_draft(config, relative_path, generated_post)
        print(
            f"[INFO] post_draft_save path={detail.relative_path} "
            f"bytes={len(generated_post.encode('utf-8'))} status=success"
        )
        return jsonify({
            "message": "Post draft saved",
            "post": post_draft_detail_to_api(detail),
        })
    except PermissionError as e:
        return jsonify({"error": str(e)}), 423
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": f"Failed to save post draft: {e}"}), 500


@app.route('/api/keywords', methods=['GET'])
def get_keywords():
    """Return the canonical harvest keyword list with enabled state."""
    path = resolve_keywords_path()
    records = load_keyword_records(path)
    return jsonify({
        "path": path,
        "keywords": keyword_records_to_api(records),
        "active_count": sum(1 for record in records if record.enabled),
    })


@app.route('/api/keywords', methods=['PUT'])
def put_keywords():
    """Replace the full keyword list after validation."""
    data = request.get_json(silent=True) or {}
    raw_keywords = data.get("keywords")
    if not isinstance(raw_keywords, list):
        return jsonify({"error": "keywords must be a list"}), 400

    try:
        records = [
            KeywordRecord(
                text=str(item.get("text", "")),
                enabled=bool(item.get("enabled", True)),
            )
            for item in raw_keywords
        ]
        normalized = normalize_keyword_records(records)
        path = save_keyword_records(normalized)
        print(
            f"[INFO] keywords_save path={path} count={len(normalized)} "
            f"active={sum(1 for record in normalized if record.enabled)}"
        )
        return jsonify({
            "message": "Keywords saved",
            "path": path,
            "keywords": keyword_records_to_api(normalized),
            "active_count": sum(1 for record in normalized if record.enabled),
        })
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to save keywords: {e}"}), 500


@app.route('/api/workbook/rows', methods=['DELETE'])
def delete_workbook_row_api():
    """Delete one article row from the active workbook (backup first)."""
    data = request.get_json(silent=True) or {}
    sheet_name = (data.get("sheet_name") or "").strip()
    row_idx = data.get("row_idx")

    if not sheet_name:
        return jsonify({"error": "sheet_name is required"}), 400
    if row_idx is None:
        return jsonify({"error": "row_idx is required"}), 400

    config = AppConfig()
    filepath = config.excel_file
    if not os.path.exists(filepath):
        return jsonify({"error": "Active workbook does not exist"}), 404

    try:
        result = delete_workbook_row(config, sheet_name=sheet_name, row_idx=row_idx)
        print(
            f"[INFO] workbook_row_delete sheet={sheet_name} row_idx={row_idx} "
            f"row_id={result.get('row_id')} status=success"
        )
        return jsonify({
            "message": "Workbook row deleted",
            "result": result,
        })
    except PermissionError as e:
        return jsonify({"error": str(e)}), 423
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": f"Failed to delete workbook row: {e}"}), 500


@app.route('/api/workbook/rows/regenerate-draft', methods=['POST'])
def regenerate_workbook_row_draft():
    """Regenerate the LinkedIn draft for one workbook row."""
    data = request.get_json(silent=True) or {}
    sheet_name = (data.get("sheet_name") or "").strip()
    row_idx = data.get("row_idx")

    if not sheet_name:
        return jsonify({"error": "sheet_name is required"}), 400
    if row_idx is None:
        return jsonify({"error": "row_idx is required"}), 400

    config = AppConfig()
    filepath = config.excel_file
    if not os.path.exists(filepath):
        return jsonify({"error": "Active workbook does not exist"}), 404

    try:
        result = regenerate_linkedin_draft_for_row(
            config,
            sheet_name=sheet_name,
            row_idx=row_idx,
        )
        print(
            f"[INFO] workbook_row_regenerate sheet={sheet_name} row_idx={row_idx} "
            f"row_id={result.get('row_id')} platform={result.get('platform')} status=success"
        )
        return jsonify({
            "message": "LinkedIn draft regenerated",
            "result": result,
        })
    except PermissionError as e:
        return jsonify({"error": str(e)}), 423
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": f"Failed to regenerate LinkedIn draft: {e}"}), 500


@app.route('/api/workbook/repair-drafts', methods=['POST'])
def repair_workbook_drafts():
    """Clear draft cells in Excel that point to missing markdown files."""
    config = AppConfig()
    filepath = config.excel_file

    if not os.path.exists(filepath):
        return jsonify({"error": "Active workbook does not exist"}), 404

    try:
        from src.business_workbook import repair_broken_draft_references

        actions = repair_broken_draft_references(config)
        return jsonify({
            "message": "Workbook draft references repaired",
            "actions": actions,
            "cleared_count": len(actions),
        })
    except PermissionError as e:
        return jsonify({"error": str(e)}), 423
    except Exception as e:
        return jsonify({"error": f"Failed to repair workbook drafts: {e}"}), 500


@app.route('/api/plan', methods=['GET'])
def get_plan():
    """Generates the posting plan (dry-run) for the active workbook."""
    config = AppConfig()
    filepath = config.excel_file
    limit = request.args.get("limit", default=2, type=int)
    platforms_str = request.args.get("platforms", default=PROJECT_SUPPORTED_PLATFORM_CSV)
    platforms = [
        p.strip()
        for p in normalize_project_platforms_csv(platforms_str, strict=False).split(",")
        if p.strip()
    ]
    
    if not os.path.exists(filepath):
        return jsonify({"error": "Active workbook does not exist"}), 404
        
    try:
        rows, _ = ingest_business_workbook(filepath)
        plan = build_posting_plan(
            rows,
            platforms,
            limit_per_platform=limit,
            config=config,
            workbook_path=filepath,
        )
        return jsonify(plan.to_dict())
    except Exception as e:
        return jsonify({"error": f"Failed to build posting plan: {e}"}), 500

@app.route('/api/drafts/run', methods=['POST'])
def start_draft_run():
    """Starts a manual harvest-and-generate run for the active operator surface."""
    data = request.json or {}
    keywords_path = (data.get("keywords_path") or "keywords.txt").strip()
    platforms_raw = (data.get("platforms") or "").strip()
    limit = data.get("limit")

    if limit is not None:
        try:
            limit = int(limit)
        except (TypeError, ValueError):
            return jsonify({"error": "limit must be an integer"}), 400
        if limit < 1:
            return jsonify({"error": "limit must be greater than 0"}), 400

    try:
        platforms = [
            p.strip()
            for p in normalize_project_platforms_csv(platforms_raw, strict=True).split(",")
            if p.strip()
        ]
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    config = AppConfig()
    db_path = os.path.join(config.output_dir, "scheduler.db")

    try:
        from src.scheduler import start_manual_draft_run
        run_id = start_manual_draft_run(
            db_path=db_path,
            config=config,
            keywords_path=keywords_path,
            platforms=platforms,
            limit=limit,
        )
        return jsonify({
            "message": "Manual draft run started",
            "run_id": run_id,
        }), 202
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/sessions', methods=['GET'])
def get_sessions():
    """Checks the saved login session status for the LinkedIn-only operator flow."""
    config = AppConfig()
    db_path = os.path.join(config.output_dir, "scheduler.db")
    from src.scheduler import save_platform_session_status
    
    results = {}
    
    for p in sorted(SUPPORTED_SESSION_PLATFORMS):
        status = check_platform_session(p, config)
        results[p] = status
        db_status = "ready" if status == "logged-in" else "login-required"
        save_platform_session_status(db_path, p, db_status)

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
        from src.platform_posting import PLATFORM_PROFILES, validate_platform_session

        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(**launch_kwargs)
            page = context.new_page() if not context.pages else context.pages[0]

            if platform in PLATFORM_PROFILES:
                logged_in = validate_platform_session(page, platform)
                context.close()
                return "logged-in" if logged_in else "login-required"

            context.close()
            return "unsupported"
    except Exception as e:
        print(f"[ERROR] Session check failed for {platform}: {e}", file=sys.stderr)
        return "error"

# --- Session Onboarding API Endpoints ---

@app.route('/api/sessions/status', methods=['GET'])
def get_sessions_status_api():
    config = AppConfig()
    db_path = os.path.join(config.output_dir, "scheduler.db")
    from src.scheduler import get_platform_sessions_status
    try:
        status_map = get_platform_sessions_status(db_path)
        result = {}
        for p in sorted(SUPPORTED_SESSION_PLATFORMS):
            if p in status_map:
                result[p] = status_map[p]
            else:
                result[p] = {
                    "status": "login-required",
                    "last_checked_at": None,
                    "metadata": None
                }
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/sessions/onboard', methods=['POST'])
def start_session_onboard():
    global active_onboarding_job
    data = request.json or {}
    platform = data.get("platform")
    if not platform:
        return jsonify({"error": "platform is required"}), 400
        
    try:
        platform = normalize_project_platform(platform, strict=True)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    if platform not in SUPPORTED_SESSION_PLATFORMS:
        return jsonify({"error": f"Platform '{platform}' is not supported for onboarding"}), 400
        
    config = AppConfig()
    
    with active_job_lock:
        if active_job is not None and active_job.status in ["preparing", "pending-operator"]:
            return jsonify({"error": "A posting job is currently in progress. Please wait until it completes."}), 400
            
    with active_onboarding_job_lock:
        if active_onboarding_job is not None and active_onboarding_job.status in ["preparing", "pending-operator"]:
            return jsonify({"error": "Another onboarding session is already active."}), 400
            
        active_onboarding_job = OnboardingJob(platform)
        
    thread = threading.Thread(target=run_onboarding_in_background, args=(active_onboarding_job, config))
    thread.daemon = True
    thread.start()
    
    return jsonify({
        "message": "Session onboarding started",
        "job": active_onboarding_job.to_dict()
    })

@app.route('/api/sessions/onboard/status', methods=['GET'])
def get_onboard_status():
    global active_onboarding_job
    with active_onboarding_job_lock:
        if active_onboarding_job is None:
            return jsonify({"active": False})
        return jsonify({
            "active": True,
            "job": active_onboarding_job.to_dict()
        })

@app.route('/api/sessions/onboard/confirm', methods=['POST'])
def confirm_onboard():
    global active_onboarding_job
    with active_onboarding_job_lock:
        if active_onboarding_job is None:
            return jsonify({"error": "No active onboarding job"}), 400
        if active_onboarding_job.status != "pending-operator":
            return jsonify({"error": f"Job status is {active_onboarding_job.status}, expected pending-operator"}), 400
            
        active_onboarding_job.action_type = "done"
        active_onboarding_job.action_received.set()
        
        return jsonify({
            "message": "Confirmation signal sent",
            "job": active_onboarding_job.to_dict()
        })

@app.route('/api/sessions/onboard/cancel', methods=['POST'])
def cancel_onboard():
    global active_onboarding_job
    with active_onboarding_job_lock:
        if active_onboarding_job is None:
            return jsonify({"error": "No active onboarding job"}), 400
            
        active_onboarding_job.action_type = "cancel"
        active_onboarding_job.action_received.set()
        
        if active_onboarding_job.status == "preparing":
            active_onboarding_job.status = "error"
            active_onboarding_job.error_message = "Cancelled by operator."
            
        return jsonify({
            "message": "Cancellation signal sent",
            "job": active_onboarding_job.to_dict()
        })

@app.route('/api/sessions/clear', methods=['POST'])
def clear_platform_session():
    data = request.json or {}
    platform = data.get("platform")
    if not platform:
        return jsonify({"error": "platform is required"}), 400
        
    try:
        platform = normalize_project_platform(platform, strict=True)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    if platform not in SUPPORTED_SESSION_PLATFORMS:
        return jsonify({"error": f"Platform '{platform}' is not supported"}), 400
        
    config = AppConfig()
    browser_context_dir = os.path.abspath(os.path.join(config.output_dir, ".browser_context"))
    
    if not os.path.exists(browser_context_dir):
        db_path = os.path.join(config.output_dir, "scheduler.db")
        from src.scheduler import save_platform_session_status
        save_platform_session_status(db_path, platform, "login-required")
        return jsonify({"message": f"Session cleared for {platform}"})
        
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(
                user_data_dir=browser_context_dir,
                headless=True,
                locale="en-US"
            )
            target_domain = SESSION_DOMAINS.get(platform)
            if target_domain:
                context.clear_cookies(domain=target_domain)
                context.clear_cookies(domain=f".{target_domain}")
            context.close()
            
        db_path = os.path.join(config.output_dir, "scheduler.db")
        from src.scheduler import save_platform_session_status
        save_platform_session_status(db_path, platform, "login-required")
        
        return jsonify({"message": f"Session cleared for {platform}"})
    except Exception as e:
        return jsonify({"error": f"Failed to clear session: {e}"}), 500

def run_onboarding_in_background(job: OnboardingJob, config: AppConfig):
    """Target for the background onboarding thread."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        job.status = "error"
        job.error_message = "Playwright is not installed."
        return

    browser_context_dir = os.path.abspath(os.path.join(config.output_dir, ".browser_context"))
    os.makedirs(browser_context_dir, exist_ok=True)
    
    launch_kwargs = {
        "user_data_dir": browser_context_dir,
        "headless": False,
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
            
            target_url = SESSION_LOGIN_URLS.get(job.platform, "https://www.google.com")
            page.goto(target_url, timeout=30000)
            
            job.status = "pending-operator"
            
            signaled = job.action_received.wait(timeout=300)
            
            if not signaled:
                job.status = "error"
                job.error_message = "Operator session onboarding timed out."
            elif job.action_type == "done":
                print(f"[ONBOARDING] Validating session for {job.platform}...")
                logged_in = False
                
                from src.platform_posting import PLATFORM_PROFILES, validate_platform_session

                if job.platform in PLATFORM_PROFILES:
                    logged_in = validate_platform_session(page, job.platform)
                else:
                    logged_in = False
                
                if logged_in:
                    job.status = "success"
                    db_path = os.path.join(config.output_dir, "scheduler.db")
                    from src.scheduler import save_platform_session_status
                    save_platform_session_status(db_path, job.platform, "ready")
                else:
                    job.status = "error"
                    job.error_message = "Validation failed. Operator is not logged in."
                    db_path = os.path.join(config.output_dir, "scheduler.db")
                    from src.scheduler import save_platform_session_status
                    save_platform_session_status(db_path, job.platform, "login-required")
            else:
                job.status = "error"
                job.error_message = "Session onboarding was cancelled by the operator."
                
            context.close()
            
    except Exception as e:
        job.status = "error"
        job.error_message = str(e)
        print(f"[ONBOARDING ERROR] Background onboarding failed: {e}", file=sys.stderr)

@app.route('/api/post/status', methods=['GET'])
def get_post_status():
    """Gets the status of the current active posting job."""
    global active_job
    with active_job_lock:
        if active_job is not None:
            return jsonify({
                "active": active_job.is_active(),
                "job": active_job.to_dict()
            })
            
    # Try scheduler job
    import src.scheduler as scheduler_module
    with scheduler_module.scheduler_active_job_lock:
        scheduler_job = scheduler_module.scheduler_active_job
        if scheduler_job is not None:
            return jsonify({
                "active": scheduler_job.status in ACTIVE_POSTING_STATUSES,
                "job": scheduler_job.to_dict()
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
        if active_job is not None and active_job.is_active():
            return jsonify({"error": "A posting job is already in progress"}), 400

        # Replace any completed job so status polling can show the new run.
        if active_job is not None and not active_job.is_active():
            active_job = None
            
        try:
            platform = normalize_project_platform(platform, strict=True)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400

        # Verify row exists and platform content is valid
        try:
            rows, _ = ingest_business_workbook(filepath, sheet_scope=[sheet_name])
            matching_rows = [r for r in rows if r.id == row_id]
            if not matching_rows:
                return jsonify({"error": f"Row ID {row_id} not found in sheet '{sheet_name}'"}), 404
                
            row = matching_rows[0]
            try:
                platform_key, draft_content = resolve_manual_post_target(
                    row,
                    platform,
                    config=config,
                    workbook_path=filepath,
                )
            except ValueError as e:
                return jsonify({"error": str(e)}), 400

            # Initialize active job for exactly one row x platform pair
            active_job = ActiveJob(platform_key, row_id, sheet_name, row.title)
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
        if draft_content and isinstance(draft_content, str):
            from src.draft_paths import load_draft_from_cell, looks_like_file_reference

            resolved_draft = load_draft_from_cell(
                draft_content,
                filepath,
                getattr(config, "post_dir", None),
            )
            if resolved_draft is not None:
                draft_content = resolved_draft
            elif looks_like_file_reference(str(draft_content)):
                raise ValueError(
                    "Draft file reference exists in Excel but the markdown file is missing. "
                    "Run Generate Drafts or Repair Broken Draft Links first."
                )

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
            if job.skip_requested or job.action_type == "skip":
                return False, None
            job.status = "pending-operator"
            # Block this background thread until API sets job.action_received
            job.action_received.wait()
            if job.action_type == "confirm":
                return True, job.post_url
            else:
                return False, None
                
        print(f"[WEB UI] Launching assisted posting for ID {row.id} on '{job.platform}'...")
        success = run_assisted_posting(
            item,
            config,
            post_content=draft_content,
            confirm_callback=confirm_callback,
            workbook_path=filepath,
        )
        
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
    finally:
        _release_active_job(job)

@app.route('/api/post/confirm', methods=['POST'])
def confirm_post():
    """Signals the waiting posting thread that the post was successfully published."""
    global active_job
    data = request.json or {}
    url = data.get("url", "").strip()
    
    with active_job_lock:
        if active_job is not None:
            if active_job.status in TERMINAL_POSTING_STATUSES:
                return jsonify({
                    "message": "Posting job already completed",
                    "job": active_job.to_dict()
                })
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
            if active_job.status in TERMINAL_POSTING_STATUSES:
                return jsonify({
                    "message": "Posting job already completed",
                    "job": active_job.to_dict()
                })
            if active_job.status not in ACTIVE_POSTING_STATUSES:
                return jsonify({
                    "error": f"Job is not skippable (current status: {active_job.status})"
                }), 400

            active_job.action_type = "skip"
            active_job.skip_requested = True

            if active_job.status == "pending-operator":
                active_job.action_received.set()
            # While still preparing, keep status unchanged so polling/skip stay coordinated
            # until the background thread observes skip_requested in confirm_callback.

            return jsonify({
                "message": "Skip/cancel signal sent",
                "job": active_job.to_dict()
            })
            
    # Try scheduler job
    import src.scheduler as scheduler_module
    with scheduler_module.scheduler_active_job_lock:
        scheduler_job = scheduler_module.scheduler_active_job
        if scheduler_job is not None:
            if scheduler_job.status not in ACTIVE_POSTING_STATUSES:
                return jsonify({
                    "error": f"Job is not skippable (current status: {scheduler_job.status})"
                }), 400

            scheduler_job.action_type = "skip"
            scheduler_job.skip_requested = True

            if scheduler_job.status == "pending-operator":
                scheduler_job.action_received.set()

            return jsonify({
                "message": "Skip/cancel signal sent",
                "job": scheduler_job.to_dict()
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
        platform = normalize_project_platform(platform, strict=True)
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
            platforms=normalize_project_platforms_csv(data.get("platforms"), strict=False),
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
        
    # Never use request.json here: Content-Type application/json with an empty body
    # makes Flask return 400 before this handler runs.
    enabled_val = None
    if request.content_length:
        payload = request.get_json(silent=True)
        if isinstance(payload, dict):
            enabled_val = payload.get("enabled")
    if enabled_val is None and request.args.get("enabled") is not None:
        enabled_val = request.args.get("enabled", "").lower() in ("1", "true", "yes")
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
