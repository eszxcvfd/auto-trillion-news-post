"""Profile-based posting workflow for platforms without custom composer logic."""

from typing import Callable, Dict, Optional, Tuple

from src.platform_workflows.browser_common import (
    fill_composer_generic,
    open_editor,
    run_assisted_flow,
    validate_session_for_profile,
)
from src.platform_workflows.profiles import PLATFORM_PROFILES, PlatformPostingProfile

try:
    from playwright.sync_api import Page
except ImportError:
    Page = object  # type: ignore


def _workflow_id_for(platform_key: str) -> str:
    return f"workflow.{platform_key}.profile.v1"


def run_profile_posting(
    platform_key: str,
    page: Page,
    post_content: str,
    image_path: Optional[str],
    confirm_callback: Optional[Callable] = None,
) -> Tuple[bool, Optional[str]]:
    profile = PLATFORM_PROFILES[platform_key]
    workflow_id = _workflow_id_for(platform_key)
    print(f"[INFO] Dispatching {workflow_id} for {profile.key}")
    return run_assisted_flow(
        page,
        profile,
        post_content,
        image_path,
        confirm_callback,
        open_editor_fn=open_editor,
        fill_composer_fn=fill_composer_generic,
    )


def validate_profile_session(platform_key: str, page: Page) -> bool:
    return validate_session_for_profile(page, PLATFORM_PROFILES[platform_key])


PROFILE_WORKFLOW_PLATFORMS = ("x", "instagram", "pinterest", "threads", "tiktok", "youtube")


def build_profile_workflow_registry() -> Dict[str, dict]:
    registry = {}
    for platform_key in PROFILE_WORKFLOW_PLATFORMS:
        registry[platform_key] = {
            "workflow_id": _workflow_id_for(platform_key),
            "run": lambda page, content, image, cb, key=platform_key: run_profile_posting(
                key, page, content, image, cb
            ),
            "validate_session": lambda page, key=platform_key: validate_profile_session(key, page),
        }
    return registry