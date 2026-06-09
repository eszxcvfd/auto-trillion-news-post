import json
import sys
from typing import Optional

from src.platform_workflows.types import PostingEvent


def emit_posting_event(event: PostingEvent) -> None:
    """Emit a structured posting event to stderr for operator logs and run history."""
    payload = {
        "workflow_id": event.workflow_id,
        "platform": event.platform,
        "action": event.action,
        "status": event.status,
        "message": event.message,
        "row_id": event.row_id,
        "sheet_name": event.sheet_name,
        "session_state": event.session_state,
        "result_status": event.result_status,
    }
    print(f"[POSTING_EVENT] {json.dumps(payload, ensure_ascii=False)}", file=sys.stderr)


def log_workflow_start(
    workflow_id: str,
    platform: str,
    row_id: Optional[int] = None,
    sheet_name: Optional[str] = None,
) -> None:
    emit_posting_event(
        PostingEvent(
            workflow_id=workflow_id,
            platform=platform,
            action="workflow.start",
            status="running",
            row_id=row_id,
            sheet_name=sheet_name,
        )
    )


def log_workflow_result(
    workflow_id: str,
    platform: str,
    success: bool,
    failure_reason: Optional[str] = None,
    row_id: Optional[int] = None,
    sheet_name: Optional[str] = None,
) -> None:
    emit_posting_event(
        PostingEvent(
            workflow_id=workflow_id,
            platform=platform,
            action="workflow.finish",
            status="success" if success else "error",
            message=failure_reason or "",
            row_id=row_id,
            sheet_name=sheet_name,
            result_status="posted" if success else "failed",
        )
    )