import os
from typing import Dict, Optional, Tuple

from src.config import AppConfig
from src.posting_core import canonicalize_platform, PLATFORM_CANONICAL

# MVP capability matrix from SPEC.md section 8.12
PLATFORM_CAPABILITIES: Dict[str, Dict[str, object]] = {
    "linkedin": {"text_only_allowed": True, "image_required": False},
    "facebook": {"text_only_allowed": True, "image_required": False},
    "x": {"text_only_allowed": True, "image_required": False},
    "instagram": {"text_only_allowed": False, "image_required": True},
    "pinterest": {"text_only_allowed": False, "image_required": True},
    "threads": {"text_only_allowed": True, "image_required": False},
    "tiktok": {
        "text_only_allowed": False,
        "image_required": True,
        "best_effort": True,
        "mvp_mode": "photo/image post when the account UI supports it; not full video upload",
    },
    "youtube": {
        "text_only_allowed": False,
        "image_required": True,
        "best_effort": True,
        "mvp_mode": "Community Post when the channel supports it; not video upload or Shorts",
    },
}

# Platforms with assisted posting adapters in the current release slice.
SUPPORTED_POSTING_PLATFORMS = {
    "linkedin",
    "facebook",
    "x",
    "instagram",
    "pinterest",
    "threads",
    "tiktok",
    "youtube",
}

BEST_EFFORT_POSTING_PLATFORMS = {"tiktok", "youtube"}

# Platforms with session onboarding/check support in Web UI.
SUPPORTED_SESSION_PLATFORMS = {
    "linkedin",
    "facebook",
    "x",
    "instagram",
    "pinterest",
    "threads",
    "tiktok",
    "youtube",
}

SESSION_DOMAINS = {
    "linkedin": "linkedin.com",
    "facebook": "facebook.com",
    "x": "x.com",
    "instagram": "instagram.com",
    "pinterest": "pinterest.com",
    "threads": "threads.net",
    "tiktok": "tiktok.com",
    "youtube": "youtube.com",
}

SESSION_LOGIN_URLS = {
    "linkedin": "https://www.linkedin.com/login",
    "facebook": "https://www.facebook.com/login/",
    "x": "https://x.com/i/flow/login",
    "instagram": "https://www.instagram.com/accounts/login/",
    "pinterest": "https://www.pinterest.com/login/",
    "threads": "https://www.threads.net/login",
    "tiktok": "https://www.tiktok.com/login",
    "youtube": "https://accounts.google.com/signin",
}


def is_best_effort_posting(platform: str) -> bool:
    try:
        platform_key = canonicalize_platform(platform)
    except ValueError:
        return False
    return platform_key in BEST_EFFORT_POSTING_PLATFORMS


def get_platform_mvp_mode(platform: str) -> Optional[str]:
    try:
        platform_key = canonicalize_platform(platform)
    except ValueError:
        return None
    return PLATFORM_CAPABILITIES[platform_key].get("mvp_mode")  # type: ignore[return-value]


def platform_requires_image(platform: str) -> bool:
    platform_key = canonicalize_platform(platform)
    return bool(PLATFORM_CAPABILITIES[platform_key]["image_required"])


def is_posting_supported(platform: str) -> bool:
    try:
        platform_key = canonicalize_platform(platform)
    except ValueError:
        return False
    return platform_key in SUPPORTED_POSTING_PLATFORMS


def resolve_local_image_path(
    image_link: Optional[str],
    config: AppConfig,
    workbook_path: Optional[str] = None,
) -> Optional[str]:
    """Resolve a workbook image reference to a local filesystem path when possible."""
    if not image_link or not str(image_link).strip():
        return None

    raw = str(image_link).strip()
    if raw.lower().startswith(("http://", "https://")):
        return None

    candidates = [raw]
    if workbook_path:
        candidates.append(os.path.join(os.path.dirname(workbook_path), raw))
    if getattr(config, "image_dir", None):
        candidates.append(os.path.join(config.image_dir, os.path.basename(raw)))
        candidates.append(os.path.join(config.image_dir, raw))

    for candidate in candidates:
        if candidate and os.path.isfile(candidate):
            return os.path.abspath(candidate)
    return None


def check_platform_media_requirements(
    platform: str,
    image_link: Optional[str],
    config: Optional[AppConfig] = None,
    workbook_path: Optional[str] = None,
) -> Tuple[str, Optional[str]]:
    """
    Validate image requirements for a platform.

    Returns:
      ('ok', None) when requirements are satisfied or not applicable.
      ('skipped_missing_required_media', reason) when image is required but unavailable.
    """
    try:
        platform_key = canonicalize_platform(platform)
    except ValueError as e:
        return "skipped_invalid_platform", str(e)

    if not PLATFORM_CAPABILITIES[platform_key]["image_required"]:
        return "ok", None

    image_path = None
    if config is not None:
        image_path = resolve_local_image_path(image_link, config, workbook_path)

    display_name = PLATFORM_CANONICAL[platform_key]
    if image_path:
        return "ok", None

    if image_link and str(image_link).strip().lower().startswith(("http://", "https://")):
        return (
            "skipped_missing_required_media",
            f"Platform '{display_name}' requires an image, but remote image URLs are not yet resolved in assisted posting.",
        )

    return (
        "skipped_missing_required_media",
        f"Platform '{display_name}' requires an image, but no local image file was found for this row.",
    )