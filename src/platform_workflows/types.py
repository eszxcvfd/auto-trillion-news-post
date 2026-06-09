from dataclasses import dataclass, field
from typing import Callable, Optional


@dataclass
class PostingWorkflowContext:
    """Shared inputs for a single row x platform posting attempt."""

    platform_key: str
    post_content: str
    image_path: Optional[str] = None
    row_id: Optional[int] = None
    sheet_name: Optional[str] = None
    title: Optional[str] = None
    confirm_callback: Optional[Callable] = None


@dataclass
class PostingWorkflowResult:
    success: bool
    post_url: Optional[str] = None
    failure_reason: Optional[str] = None
    workflow_id: str = ""


@dataclass
class PostingEvent:
    """Structured observability record for one posting step."""

    workflow_id: str
    platform: str
    action: str
    status: str
    message: str = ""
    row_id: Optional[int] = None
    sheet_name: Optional[str] = None
    session_state: Optional[str] = None
    result_status: Optional[str] = None