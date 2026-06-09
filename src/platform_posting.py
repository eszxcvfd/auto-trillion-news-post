"""
Platform posting facade.

Shared workbook eligibility lives in posting_core. Platform-owned browser
automation lives in src.platform_workflows.* and is dispatched through the
workflow registry.
"""

import os
from typing import Callable, Optional, Tuple

from src.config import AppConfig
from src.models import NewsItem
from src.platform_capabilities import (
    is_posting_supported,
    platform_requires_image,
    resolve_local_image_path,
)
from src.platform_workflows.facebook_workflow import (
    _facebook_caption_editor,
    _insert_facebook_caption_via_js,
    _paste_facebook_caption,
    _upload_facebook_image,
)
from src.platform_workflows.linkedin_workflow import (
    _insert_linkedin_caption_via_js,
    _paste_linkedin_caption,
    _upload_linkedin_image,
)
from src.platform_workflows.profiles import PLATFORM_PROFILES, PlatformPostingProfile
from src.platform_workflows.registry import (
    get_workflow_id,
    run_platform_posting_for_item,
    validate_platform_session as _validate_platform_session,
)
from src.posting_core import PLATFORM_CANONICAL, canonicalize_platform

__all__ = [
    "PLATFORM_PROFILES",
    "PlatformPostingProfile",
    "prepare_posting_assets",
    "run_platform_assisted_posting",
    "validate_platform_session",
    "get_workflow_id",
    "_facebook_caption_editor",
    "_insert_facebook_caption_via_js",
    "_paste_facebook_caption",
    "_upload_facebook_image",
    "_insert_linkedin_caption_via_js",
    "_paste_linkedin_caption",
    "_upload_linkedin_image",
]


def prepare_posting_assets(
    item: NewsItem,
    config: AppConfig,
    post_content: str,
    workbook_path: Optional[str] = None,
) -> Tuple[Optional[str], Optional[str]]:
    """
    Validate posting support and resolve image path.
    Returns (image_path, error_message).
    """
    platform_name = item.platform or "linkedin"
    try:
        platform_key = canonicalize_platform(platform_name)
    except ValueError as e:
        return None, str(e)

    if not is_posting_supported(platform_key):
        return None, (
            f"Assisted posting for '{PLATFORM_CANONICAL[platform_key]}' "
            "is not supported in the current release slice."
        )

    if platform_requires_image(platform_key):
        image_path = resolve_local_image_path(item.image_file, config, workbook_path)
        if not image_path:
            return None, (
                f"Platform '{PLATFORM_CANONICAL[platform_key]}' requires a local image file, "
                "but none was found for this row."
            )
    else:
        image_path = resolve_local_image_path(item.image_file, config, workbook_path)

    if not post_content:
        return None, f"Empty post content for ID {item.id}."
    return image_path, None


def run_platform_assisted_posting(
    item: NewsItem,
    config: AppConfig,
    post_content: str,
    image_path: Optional[str],
    confirm_callback: Optional[Callable] = None,
) -> bool:
    return run_platform_posting_for_item(
        item,
        config,
        post_content,
        image_path,
        confirm_callback=confirm_callback,
    )


def validate_platform_session(page, platform_key: str) -> bool:
    return _validate_platform_session(page, platform_key)