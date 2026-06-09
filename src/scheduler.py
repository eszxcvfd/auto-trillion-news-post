import os
import sys
import sqlite3
import datetime
import uuid
import threading
import time
from typing import List, Dict, Any, Tuple, Optional

from src.config import AppConfig
from src.models import NewsItem
from src.business_workbook import ingest_business_workbook
from src.posting_core import build_posting_plan, canonicalize_platform, PLATFORM_ATTRS
from src.writeback import write_post_result
from src.assisted_posting import run_assisted_posting
from src.platform_workflows.registry import get_workflow_id

def _persist_run_details(cursor, run_id: str, row_details: List[Tuple]) -> None:
    """Insert run detail rows, optionally including workflow_id as the 6th tuple value."""
    for details in row_details:
        workflow_id = details[5] if len(details) > 5 else None
        cursor.execute(
            """
            INSERT INTO run_details (run_id, sheet_name, row_id, platform, status, message, workflow_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (run_id, details[0], details[1], details[2], details[3], details[4], workflow_id),
        )


def get_db_connection(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path: str):
    """Initializes the SQLite database tables for scheduling and run history."""
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
    conn = get_db_connection(db_path)
    c = conn.cursor()
    
    # Schedules Table
    c.execute("""
    CREATE TABLE IF NOT EXISTS schedules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        expression TEXT NOT NULL,          -- Cron (e.g. "*/30 * * * *") or interval (e.g. "every 1h")
        job_type TEXT NOT NULL,            -- "draft" or "post"
        enabled INTEGER DEFAULT 1,         -- 0 or 1
        last_run_at TEXT,
        next_run_at TEXT,
        workbook_path TEXT,
        sheet_name TEXT,
        platforms TEXT,                    -- Comma-separated (e.g. "linkedin,facebook")
        post_limit INTEGER DEFAULT 2
    )
    """)
    
    # Run History Table
    c.execute("""
    CREATE TABLE IF NOT EXISTS runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        schedule_id INTEGER,
        run_id TEXT UNIQUE NOT NULL,       -- uuid
        status TEXT NOT NULL,              -- "running", "completed", "partial", "failed", "missed"
        trigger_type TEXT NOT NULL,        -- "scheduled" or "manual"
        started_at TEXT NOT NULL,
        finished_at TEXT,
        summary TEXT,
        error_message TEXT,
        FOREIGN KEY(schedule_id) REFERENCES schedules(id) ON DELETE SET NULL
    )
    """)
    
    # Run Details Table (row-level/platform-level outcomes)
    c.execute("""
    CREATE TABLE IF NOT EXISTS run_details (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id TEXT NOT NULL,
        sheet_name TEXT NOT NULL,
        row_id INTEGER NOT NULL,
        platform TEXT NOT NULL,
        status TEXT NOT NULL,              -- "success", "skip", "error", "login-required"
        message TEXT,
        workflow_id TEXT,
        FOREIGN KEY(run_id) REFERENCES runs(run_id) ON DELETE CASCADE
    )
    """)

    # Backfill workflow_id column for existing databases.
    detail_columns = {row[1] for row in c.execute("PRAGMA table_info(run_details)")}
    if "workflow_id" not in detail_columns:
        c.execute("ALTER TABLE run_details ADD COLUMN workflow_id TEXT")
    
    # Platform Sessions Table (session operational status & metadata)
    c.execute("""
    CREATE TABLE IF NOT EXISTS platform_sessions (
        platform TEXT PRIMARY KEY,
        status TEXT NOT NULL,
        last_checked_at TEXT,
        metadata TEXT
    )
    """)
    
    conn.commit()
    conn.close()

# --- Cron / Interval Next Run Calculation ---

def parse_cron_field(field: str, min_val: int, max_val: int) -> set[int]:
    if field == "*":
        return set(range(min_val, max_val + 1))
    
    values = set()
    for part in field.split(","):
        if "/" in part:
            val_range, step = part.split("/", 1)
            step = int(step)
            if val_range == "*":
                start, end = min_val, max_val
            elif "-" in val_range:
                start, end = map(int, val_range.split("-"))
            else:
                start = int(val_range)
                end = max_val
            for v in range(start, end + 1, step):
                if min_val <= v <= max_val:
                    values.add(v)
        elif "-" in part:
            start, end = map(int, part.split("-"))
            for v in range(start, end + 1):
                if min_val <= v <= max_val:
                    values.add(v)
        else:
            v = int(part)
            if min_val <= v <= max_val:
                values.add(v)
    return values

def calculate_next_run(expression: str, start_time: datetime.datetime) -> datetime.datetime:
    """Computes the next datetime that matches the given cron or interval expression."""
    expression = expression.strip()
    
    # 1. Parse intervals (e.g., "every 15m", "every 2h", "every 1d")
    if expression.startswith("every "):
        parts = expression.split()
        if len(parts) == 2:
            duration_str = parts[1]
            if duration_str.endswith("m"):
                minutes = int(duration_str[:-1])
                return start_time + datetime.timedelta(minutes=minutes)
            elif duration_str.endswith("h"):
                hours = int(duration_str[:-1])
                return start_time + datetime.timedelta(hours=hours)
            elif duration_str.endswith("d"):
                days = int(duration_str[:-1])
                return start_time + datetime.timedelta(days=days)
                
    # 2. Parse standard 5-field cron
    fields = expression.split()
    if len(fields) != 5:
        raise ValueError(f"Invalid cron/interval expression: '{expression}'")
        
    minutes = parse_cron_field(fields[0], 0, 59)
    hours = parse_cron_field(fields[1], 0, 23)
    doms = parse_cron_field(fields[2], 1, 31)
    months = parse_cron_field(fields[3], 1, 12)
    dows = parse_cron_field(fields[4], 0, 6)
    
    # Truncate seconds and start looking at next minute
    current = start_time.replace(second=0, microsecond=0) + datetime.timedelta(minutes=1)
    limit_time = current + datetime.timedelta(days=366)
    
    while current < limit_time:
        if current.month not in months:
            # Skip to start of next month to optimize loop
            current = (current.replace(day=1, hour=0, minute=0) + datetime.timedelta(days=32)).replace(day=1)
            continue
            
        if current.day not in doms:
            current = (current.replace(hour=0, minute=0) + datetime.timedelta(days=1))
            continue
            
        # Map current.weekday() (0=Mon, 6=Sun) to cron DOW (0=Sun, 1=Mon, ..., 6=Sat)
        cron_dow = (current.weekday() + 1) % 7
        if cron_dow not in dows:
            current = (current.replace(hour=0, minute=0) + datetime.timedelta(days=1))
            continue
            
        if current.hour not in hours:
            current = (current.replace(minute=0) + datetime.timedelta(hours=1))
            continue
            
        if current.minute not in minutes:
            current += datetime.timedelta(minutes=1)
            continue
            
        return current
        
    raise ValueError("No matching schedule date found within 1 year.")

# --- Database CRUD and Query Operations ---

def create_schedule(db_path: str, name: str, expression: str, job_type: str, 
                    workbook_path: Optional[str] = None, sheet_name: Optional[str] = None, 
                    platforms: Optional[str] = None, post_limit: int = 2) -> int:
    """Creates a new schedule and computes its initial next_run_at."""
    init_db(db_path)
    
    # Validate expression
    next_run = calculate_next_run(expression, datetime.datetime.now())
    next_run_str = next_run.isoformat()
    
    conn = get_db_connection(db_path)
    c = conn.cursor()
    c.execute("""
    INSERT INTO schedules (name, expression, job_type, enabled, next_run_at, workbook_path, sheet_name, platforms, post_limit)
    VALUES (?, ?, ?, 1, ?, ?, ?, ?, ?)
    """, (name, expression, job_type, next_run_str, workbook_path, sheet_name, platforms, post_limit))
    schedule_id = c.lastrowid
    conn.commit()
    conn.close()
    return schedule_id

def update_schedule(db_path: str, name: str, expression: Optional[str] = None, 
                    enabled: Optional[int] = None, job_type: Optional[str] = None,
                    workbook_path: Optional[str] = None, sheet_name: Optional[str] = None,
                    platforms: Optional[str] = None, post_limit: Optional[int] = None):
    """Updates an existing schedule by name and recalculates next_run_at if expression changes."""
    conn = get_db_connection(db_path)
    c = conn.cursor()
    
    # Load current schedule
    c.execute("SELECT * FROM schedules WHERE name = ?", (name,))
    row = c.fetchone()
    if not row:
        conn.close()
        raise ValueError(f"Schedule '{name}' not found.")
        
    updates = []
    params = []
    
    if expression is not None:
        next_run = calculate_next_run(expression, datetime.datetime.now())
        updates.append("expression = ?")
        params.append(expression)
        updates.append("next_run_at = ?")
        params.append(next_run.isoformat())
        
    if enabled is not None:
        updates.append("enabled = ?")
        params.append(enabled)
        # Recalculate next run if being re-enabled
        if enabled == 1 and expression is None:
            next_run = calculate_next_run(row["expression"], datetime.datetime.now())
            updates.append("next_run_at = ?")
            params.append(next_run.isoformat())
            
    if job_type is not None:
        updates.append("job_type = ?")
        params.append(job_type)
    if workbook_path is not None:
        updates.append("workbook_path = ?")
        params.append(workbook_path)
    if sheet_name is not None:
        updates.append("sheet_name = ?")
        params.append(sheet_name)
    if platforms is not None:
        updates.append("platforms = ?")
        params.append(platforms)
    if post_limit is not None:
        updates.append("post_limit = ?")
        params.append(post_limit)
        
    if updates:
        params.append(name)
        query = f"UPDATE schedules SET {', '.join(updates)} WHERE name = ?"
        c.execute(query, params)
        conn.commit()
        
    conn.close()

def delete_schedule(db_path: str, schedule_id: int):
    """Deletes a schedule definition by ID."""
    conn = get_db_connection(db_path)
    c = conn.cursor()
    c.execute("DELETE FROM schedules WHERE id = ?", (schedule_id,))
    conn.commit()
    conn.close()

def list_schedules(db_path: str) -> List[Dict[str, Any]]:
    """Returns a list of all schedules in the database."""
    init_db(db_path)
    conn = get_db_connection(db_path)
    c = conn.cursor()
    c.execute("SELECT * FROM schedules ORDER BY name")
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def list_run_history(db_path: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Returns the runs list ordered by start time descending."""
    init_db(db_path)
    conn = get_db_connection(db_path)
    c = conn.cursor()
    c.execute("""
    SELECT r.*, s.name as schedule_name 
    FROM runs r 
    LEFT JOIN schedules s ON r.schedule_id = s.id 
    ORDER BY r.started_at DESC 
    LIMIT ?
    """, (limit,))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_run_history_detail(db_path: str, run_id: str) -> Optional[Dict[str, Any]]:
    """Gets a specific run summary and its row-level details."""
    conn = get_db_connection(db_path)
    c = conn.cursor()
    c.execute("""
    SELECT r.*, s.name as schedule_name 
    FROM runs r 
    LEFT JOIN schedules s ON r.schedule_id = s.id 
    WHERE r.run_id = ?
    """, (run_id,))
    run_row = c.fetchone()
    if not run_row:
        conn.close()
        return None
        
    c.execute("SELECT * FROM run_details WHERE run_id = ? ORDER BY id", (run_id,))
    detail_rows = c.fetchall()
    conn.close()
    
    run_dict = dict(run_row)
    run_dict["details"] = [dict(d) for d in detail_rows]
    return run_dict

def get_active_manual_draft_run(db_path: str) -> Optional[Dict[str, Any]]:
    """Returns the newest active manual draft run that is not tied to a schedule."""
    init_db(db_path)
    conn = get_db_connection(db_path)
    c = conn.cursor()
    c.execute("""
    SELECT *
    FROM runs
    WHERE schedule_id IS NULL AND trigger_type = 'manual' AND status = 'running'
    ORDER BY started_at DESC
    LIMIT 1
    """)
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None

def save_platform_session_status(db_path: str, platform: str, status: str, metadata: Optional[str] = None):
    """Saves or updates the session status of a platform in the SQLite store."""
    init_db(db_path)
    conn = get_db_connection(db_path)
    c = conn.cursor()
    now_str = datetime.datetime.now().isoformat()
    c.execute("""
    INSERT INTO platform_sessions (platform, status, last_checked_at, metadata)
    VALUES (?, ?, ?, ?)
    ON CONFLICT(platform) DO UPDATE SET
        status=excluded.status,
        last_checked_at=excluded.last_checked_at,
        metadata=coalesce(excluded.metadata, platform_sessions.metadata)
    """, (platform, status, now_str, metadata))
    conn.commit()
    conn.close()

def get_platform_sessions_status(db_path: str) -> Dict[str, Any]:
    """Returns status mapping for all platform session configurations."""
    init_db(db_path)
    conn = get_db_connection(db_path)
    c = conn.cursor()
    c.execute("SELECT * FROM platform_sessions")
    rows = c.fetchall()
    conn.close()
    
    result = {}
    for r in rows:
        result[r["platform"]] = {
            "status": r["status"],
            "last_checked_at": r["last_checked_at"],
            "metadata": r["metadata"]
        }
    return result

def start_manual_draft_run(
    db_path: str,
    config: AppConfig,
    keywords_path: str = "keywords.txt",
    platforms: Optional[List[Optional[str]]] = None,
    limit: Optional[int] = None,
) -> str:
    """Starts a one-off manual harvest-and-generate run and returns its run id."""
    init_db(db_path)
    active_run = get_active_manual_draft_run(db_path)
    if active_run is not None:
        raise ValueError("A manual draft run is already in progress.")

    run_id = str(uuid.uuid4())
    normalized_platforms = platforms or [None]

    t = threading.Thread(
        target=run_manual_draft_job,
        args=(db_path, config, keywords_path, normalized_platforms, limit, run_id),
    )
    t.daemon = True
    t.start()
    return run_id

def run_manual_draft_job(
    db_path: str,
    config: AppConfig,
    keywords_path: str = "keywords.txt",
    platforms: Optional[List[Optional[str]]] = None,
    limit: Optional[int] = None,
    explicit_run_id: Optional[str] = None,
):
    """Executes a one-off manual harvest-and-generate run and records durable history."""
    init_db(db_path)
    run_id = explicit_run_id or str(uuid.uuid4())
    started_at = datetime.datetime.now().isoformat()
    row_details: List[Tuple[str, int, str, str, str]] = []
    status = "completed"
    summary = ""
    error_msg = None

    conn = get_db_connection(db_path)
    c = conn.cursor()
    c.execute("""
    INSERT INTO runs (schedule_id, run_id, status, trigger_type, started_at)
    VALUES (NULL, ?, 'running', 'manual', ?)
    """, (run_id, started_at))
    conn.commit()
    conn.close()

    normalized_platforms = platforms or [None]

    try:
        if not os.path.exists(keywords_path):
            raise FileNotFoundError(f"Keywords file not found at: {keywords_path}")

        os.environ["EXCEL_FILE"] = os.path.abspath(config.excel_file)

        from main import execute_run

        success_count = 0
        error_count = 0

        for platform_name in normalized_platforms:
            platform_label = platform_name or config.default_platform or "default"
            try:
                execute_run(keywords_path, platform=platform_name, limit=limit)
                success_count += 1
                row_details.append((
                    "Workbook",
                    0,
                    platform_label,
                    "success",
                    f"Harvest and generation completed using '{keywords_path}'.",
                ))
            except SystemExit as exc:
                error_count += 1
                code = exc.code if exc.code is not None else 1
                row_details.append((
                    "Workbook",
                    0,
                    platform_label,
                    "error",
                    f"Draft pipeline exited early with code {code}.",
                ))
            except Exception as exc:
                error_count += 1
                row_details.append((
                    "Workbook",
                    0,
                    platform_label,
                    "error",
                    str(exc),
                ))

        if success_count > 0 and error_count > 0:
            status = "partial"
        elif success_count == 0 and error_count > 0:
            status = "failed"
        else:
            status = "completed"

        summary = (
            "Manual harvest and generation complete. "
            f"Platform runs succeeded: {success_count}, failed: {error_count}."
        )
    except Exception as exc:
        status = "failed"
        error_msg = str(exc)
        summary = "Manual harvest and generation failed."
        row_details.append(("Workbook", 0, "draft-run", "error", error_msg))
        print(f"[SCHEDULER ERROR] Manual draft run failed: {exc}", file=sys.stderr)

    finished_at = datetime.datetime.now().isoformat()
    conn = get_db_connection(db_path)
    c = conn.cursor()
    c.execute("""
    UPDATE runs
    SET status = ?, finished_at = ?, summary = ?, error_message = ?
    WHERE run_id = ?
    """, (status, finished_at, summary, error_msg, run_id))

    _persist_run_details(c, run_id, row_details)

    conn.commit()
    conn.close()

# --- Background Scheduler Execution logic ---

# Coordinator event hook to handle active posting confirms via Web UI
scheduler_active_job = None
scheduler_active_job_lock = threading.Lock()

ACTIVE_POSTING_STATUSES = ("preparing", "pending-operator")
TERMINAL_POSTING_STATUSES = ("success", "skipped", "error")


def _release_scheduler_active_job(job) -> None:
    """Clear the scheduler posting job once it reaches a terminal state."""
    global scheduler_active_job
    with scheduler_active_job_lock:
        if scheduler_active_job is job and scheduler_active_job.status in TERMINAL_POSTING_STATUSES:
            scheduler_active_job = None

def trigger_due_schedules(db_path: str, config: AppConfig):
    """Checks for due schedules and launches them in a background thread."""
    init_db(db_path)
    
    conn = get_db_connection(db_path)
    c = conn.cursor()
    
    now = datetime.datetime.now()
    now_str = now.isoformat()
    
    # Find enabled schedules whose next_run_at is in the past
    c.execute("SELECT * FROM schedules WHERE enabled = 1")
    rows = c.fetchall()
    
    due_schedules = []
    for row in rows:
        next_run_str = row["next_run_at"]
        if next_run_str:
            try:
                next_run = datetime.datetime.fromisoformat(next_run_str)
                if next_run <= now:
                    due_schedules.append(row)
            except Exception:
                pass
                
    conn.close()
    
    for sch in due_schedules:
        # Run each due schedule in its own daemon thread
        t = threading.Thread(target=run_schedule_job, args=(db_path, sch["id"], "scheduled", config))
        t.daemon = True
        t.start()

def run_schedule_now(db_path: str, schedule_id: int, config: AppConfig) -> str:
    """Manually triggers a schedule to run immediately and returns its run_id."""
    init_db(db_path)
    run_id = str(uuid.uuid4())
    
    t = threading.Thread(target=run_schedule_job, args=(db_path, schedule_id, "manual", config, run_id))
    t.daemon = True
    t.start()
    
    return run_id

def run_schedule_job(db_path: str, schedule_id: int, trigger_type: str, config: AppConfig, explicit_run_id: Optional[str] = None):
    """Executes a single schedule job, logging start, finish, details, and outcomes."""
    run_id = explicit_run_id or str(uuid.uuid4())
    started_at = datetime.datetime.now().isoformat()
    
    # 1. Initialize Run Record as running
    conn = get_db_connection(db_path)
    c = conn.cursor()
    c.execute("""
    INSERT INTO runs (schedule_id, run_id, status, trigger_type, started_at)
    VALUES (?, ?, 'running', ?, ?)
    """, (schedule_id, run_id, trigger_type, started_at))
    conn.commit()
    
    # Load the schedule definition
    c.execute("SELECT * FROM schedules WHERE id = ?", (schedule_id,))
    sch = c.fetchone()
    if not sch:
        c.execute("UPDATE runs SET status='failed', finished_at=?, error_message='Schedule definition not found' WHERE run_id=?", 
                  (datetime.datetime.now().isoformat(), run_id))
        conn.commit()
        conn.close()
        return
        
    conn.close()
    
    # 2. Update next run time for scheduled trigger
    if trigger_type == "scheduled":
        try:
            next_run = calculate_next_run(sch["expression"], datetime.datetime.now())
            next_run_str = next_run.isoformat()
            
            conn = get_db_connection(db_path)
            c = conn.cursor()
            c.execute("UPDATE schedules SET last_run_at=?, next_run_at=? WHERE id=?", 
                      (started_at, next_run_str, schedule_id))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[SCHEDULER ERROR] Failed to update next run calculation: {e}")
            
    # 3. Perform actual execution
    status = "completed"
    summary = ""
    error_msg = None
    row_details = [] # list of (sheet_name, row_id, platform, status, message)
    
    try:
        job_type = sch["job_type"]
        
        if job_type == "draft":
            # Running Search and AI post generation flow
            from main import execute_run
            # Scheduled runs use default keywords.txt
            keywords_file = "keywords.txt"
            limit = sch["post_limit"]
            platforms_str = sch["platforms"]
            platforms = [p.strip() for p in platforms_str.split(",") if p.strip()] if platforms_str else [None]
            
            print(f"[SCHEDULER] Starting draft generation for Run {run_id}")
            # Run for each platform
            total_saved = 0
            for plat in platforms:
                # execute_run handles search & AI generation
                saved = execute_run(keywords_file, platform=plat, limit=limit)
                if saved:
                    total_saved += len(saved)
                    
            summary = f"Harvest and generation complete. Processed {total_saved} articles."
            
        elif job_type == "post":
            # Running Posting flow
            excel_path = sch["workbook_path"] or config.excel_file
            sheet_name = sch["sheet_name"]
            platforms_str = sch["platforms"] or "linkedin,facebook,x,instagram,pinterest,threads,tiktok,youtube"
            platforms = [p.strip() for p in platforms_str.split(",") if p.strip()]
            limit = sch["post_limit"]
            
            if not os.path.exists(excel_path):
                raise FileNotFoundError(f"Workbook file not found at: {excel_path}")
                
            # Ingest workbook rows
            sheet_scope = [sheet_name] if sheet_name else None
            rows, warnings = ingest_business_workbook(excel_path, sheet_scope=sheet_scope)
            
            # Group warnings as details
            for w in warnings:
                row_details.append(("Workbook", 0, "Ingest", "warning", w))
                
            # Build posting plan
            plan = build_posting_plan(
                rows,
                platforms,
                limit_per_platform=limit,
                config=config,
                workbook_path=excel_path,
            )
            
            # Log skipped/excluded detail
            for skip_info in plan.skipped_summary:
                # Try parsing skip info for context
                # "Sheet 'Payment', Row 3 (ID: 2) skipped..."
                row_details.append((sheet_name or "Workbook", 0, "All", "skip", skip_info))
                
            # Trigger posting candidates
            total_candidates = sum(len(plan.candidates[p]) for p in plan.candidates)
            if total_candidates == 0:
                summary = "No eligible candidates to post."
            else:
                success_count = 0
                error_count = 0
                
                # Execute each candidate
                for platform_name, candidates in plan.candidates.items():
                    workflow_id = get_workflow_id(platform_name)
                    for c_idx, cand in enumerate(candidates):
                        print(
                            f"[SCHEDULER] Posting candidate {c_idx+1}/{len(candidates)} "
                            f"on '{platform_name}' via {workflow_id} (ID: {cand.id})"
                        )
                        
                        # Set up thread coordinator for operator confirmation with 5-minute timeout
                        global scheduler_active_job
                        from src.web_ui import ActiveJob
                        
                        job = ActiveJob(platform_name, cand.id, cand.sheet_name, cand.title)
                        with scheduler_active_job_lock:
                            scheduler_active_job = job
                            
                        draft_content = cand.draft_content
                        if draft_content and isinstance(draft_content, str):
                            from src.draft_paths import load_draft_from_cell

                            resolved_draft = load_draft_from_cell(
                                draft_content,
                                excel_path,
                                getattr(config, "post_dir", None),
                            )
                            if resolved_draft is not None:
                                draft_content = resolved_draft
                                        
                        # NewsItem mock wrapper
                        item = NewsItem(id=cand.id, title=cand.title, image_file=cand.image_link, platform=platform_name, status="new")
                        
                        # Non-blocking confirm callback with 5-minute timeout
                        def confirm_callback():
                            if job.skip_requested or job.action_type == "skip":
                                return False, None
                            job.status = "pending-operator"
                            # Wait up to 300 seconds for operator confirmation in Web UI
                            signaled = job.action_received.wait(timeout=300)
                            if not signaled:
                                # Timeout
                                job.status = "error"
                                job.error_message = "Operator confirmation timeout."
                                return False, None
                            if job.action_type == "confirm":
                                return True, job.post_url
                            else:
                                return False, None
                                
                        try:
                            post_success = run_assisted_posting(item, config, post_content=draft_content, confirm_callback=confirm_callback)
                            
                            if post_success:
                                url_val = getattr(item, "post_url", "").strip() or "[posted-no-link]"
                                write_post_result(excel_path, cand.sheet_name, cand.row_idx, platform_name, url_val, backup_enabled=config.backup_enabled)
                                row_details.append((
                                    cand.sheet_name,
                                    cand.id,
                                    platform_name,
                                    "success",
                                    f"Posted successfully. URL: {url_val}",
                                    workflow_id,
                                ))
                                success_count += 1
                            else:
                                if job.action_type == "skip":
                                    write_post_result(excel_path, cand.sheet_name, cand.row_idx, platform_name, "[skip] skipped by operator", backup_enabled=config.backup_enabled)
                                    row_details.append((
                                        cand.sheet_name,
                                        cand.id,
                                        platform_name,
                                        "skip",
                                        "Skipped by operator action",
                                        workflow_id,
                                    ))
                                else:
                                    err_text = job.error_message or "Post not published or timeout."
                                    row_details.append((
                                        cand.sheet_name,
                                        cand.id,
                                        platform_name,
                                        "error",
                                        err_text,
                                        workflow_id,
                                    ))
                                    error_count += 1
                        except Exception as ex:
                            row_details.append((
                                cand.sheet_name,
                                cand.id,
                                platform_name,
                                "error",
                                str(ex),
                                workflow_id,
                            ))
                            error_count += 1
                            
                        # Clear active job once it reaches a terminal state
                        _release_scheduler_active_job(job)
                            
                # Determine final run status
                if success_count > 0 and error_count > 0:
                    status = "partial"
                elif success_count == 0 and error_count > 0:
                    status = "failed"
                else:
                    status = "completed"
                    
                summary = f"Posting run complete. Successes: {success_count}, Errors: {error_count}."
                
    except Exception as e:
        status = "failed"
        error_msg = str(e)
        summary = "Critical execution error."
        print(f"[SCHEDULER ERROR] Scheduled run failed: {e}")
        
    finished_at = datetime.datetime.now().isoformat()
    
    # 4. Save terminal status and details in DB
    conn = get_db_connection(db_path)
    c = conn.cursor()
    c.execute("""
    UPDATE runs 
    SET status = ?, finished_at = ?, summary = ?, error_message = ? 
    WHERE run_id = ?
    """, (status, finished_at, summary, error_msg, run_id))
    
    _persist_run_details(c, run_id, row_details)

    conn.commit()
    conn.close()

# --- Poller Daemon Thread ---

class SchedulerDaemon:
    def __init__(self, db_path: str, config: AppConfig):
        self.db_path = db_path
        self.config = config
        self._stop_event = threading.Event()
        
    def start(self):
        init_db(self.db_path)
        self.thread = threading.Thread(target=self._run_loop)
        self.thread.daemon = True
        self.thread.start()
        print("[SCHEDULER] Background Scheduler Daemon started.")
        
    def stop(self):
        self._stop_event.set()
        if hasattr(self, "thread"):
            self.thread.join(timeout=2)
        print("[SCHEDULER] Background Scheduler Daemon stopped.")
        
    def _run_loop(self):
        # Poll every 10 seconds to check due schedules
        while not self._stop_event.is_set():
            try:
                trigger_due_schedules(self.db_path, self.config)
            except Exception as e:
                print(f"[SCHEDULER] Daemon loop exception: {e}", file=sys.stderr)
            time.sleep(10)
