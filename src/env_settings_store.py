import os
import re
from typing import Any, Dict, List, Optional, Tuple

API_KEY_MASK = "***"
API_KEY_UNCHANGED = "__UNCHANGED__"

MANAGED_KEYS: Tuple[str, ...] = (
    "GEMINI_API_KEY",
    "AI_PROVIDER",
    "AI_MODEL",
    "SEARCH_PROVIDER",
    "HEADLESS",
    "OUTPUT_DIR",
    "EXCEL_FILE",
    "BACKUP_ENABLED",
    "IMAGE_DIR",
    "POST_DIR",
    "LOG_DIR",
    "DEFAULT_LANGUAGE",
    "MAX_RESULTS_PER_KEYWORD",
    "MAX_POSTS_PER_RUN",
)

SETTINGS_SECTIONS: Tuple[Dict[str, Any], ...] = (
    {
        "id": "gemini",
        "title": "Gemini API Configuration",
        "keys": ("GEMINI_API_KEY", "AI_PROVIDER", "AI_MODEL"),
    },
    {
        "id": "search",
        "title": "Search Configuration",
        "keys": ("SEARCH_PROVIDER", "HEADLESS"),
    },
    {
        "id": "output",
        "title": "Output Configuration",
        "keys": (
            "OUTPUT_DIR",
            "EXCEL_FILE",
            "BACKUP_ENABLED",
            "IMAGE_DIR",
            "POST_DIR",
            "LOG_DIR",
        ),
    },
    {
        "id": "limits",
        "title": "Run Limits & Preferences",
        "keys": ("DEFAULT_LANGUAGE", "MAX_RESULTS_PER_KEYWORD", "MAX_POSTS_PER_RUN"),
    },
)

DEFAULT_VALUES: Dict[str, str] = {
    "GEMINI_API_KEY": "",
    "AI_PROVIDER": "gemini",
    "AI_MODEL": "gemini-1.5-flash",
    "SEARCH_PROVIDER": "bing",
    "HEADLESS": "false",
    "OUTPUT_DIR": "./output",
    "EXCEL_FILE": "./output/Trillion $ news.xlsx",
    "BACKUP_ENABLED": "false",
    "IMAGE_DIR": "./output/Ảnh Trillion $ news",
    "POST_DIR": "./output/posts",
    "LOG_DIR": "./output/logs",
    "DEFAULT_LANGUAGE": "en",
    "MAX_RESULTS_PER_KEYWORD": "10",
    "MAX_POSTS_PER_RUN": "5",
}

ALLOWED_SEARCH_PROVIDERS = frozenset({"bing", "browser"})
ALLOWED_AI_PROVIDERS = frozenset({"gemini"})
_BOOL_KEYS = frozenset({"HEADLESS", "BACKUP_ENABLED"})
_INT_KEYS = frozenset({"MAX_RESULTS_PER_KEYWORD", "MAX_POSTS_PER_RUN"})


def resolve_env_path(filepath: Optional[str] = None) -> str:
    """Resolve the operator .env file path."""
    raw = filepath or os.getenv("ENV_FILE", ".env")
    return os.path.abspath(raw)


def _parse_assignment(line: str) -> Optional[Tuple[str, str]]:
    if "=" not in line:
        return None
    key, value = line.split("=", 1)
    key = key.strip()
    if not key or key.startswith("#"):
        return None
    return key, value.strip()


def parse_env_assignments(path: str) -> Dict[str, str]:
    """Read key=value pairs from a .env file (last assignment wins)."""
    if not os.path.exists(path):
        return {}
    assignments: Dict[str, str] = {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            parsed = _parse_assignment(line)
            if parsed is not None:
                key, value = parsed
                assignments[key] = value
    return assignments


def _coerce_bool_string(value: Any, field: str) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    text = str(value or "").strip().lower()
    if text in {"true", "1", "yes", "on"}:
        return "true"
    if text in {"false", "0", "no", "off"}:
        return "false"
    raise ValueError(f"{field} must be true or false")


def _coerce_positive_int(value: Any, field: str) -> str:
    try:
        number = int(str(value).strip())
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be a positive integer") from exc
    if number < 1:
        raise ValueError(f"{field} must be at least 1")
    return str(number)


def normalize_settings_updates(
    updates: Dict[str, Any],
    *,
    existing: Optional[Dict[str, str]] = None,
) -> Dict[str, str]:
    """Validate and normalize operator settings before persisting."""
    if not isinstance(updates, dict):
        raise ValueError("settings payload must be an object")

    existing = existing or {}
    normalized: Dict[str, str] = {}

    for key in MANAGED_KEYS:
        if key not in updates:
            continue
        raw_value = updates[key]

        if key == "GEMINI_API_KEY":
            text = str(raw_value or "").strip()
            if text in {"", API_KEY_MASK, API_KEY_UNCHANGED}:
                if existing.get("GEMINI_API_KEY"):
                    normalized[key] = existing["GEMINI_API_KEY"]
                else:
                    normalized[key] = ""
            else:
                normalized[key] = text
            continue

        if key in _BOOL_KEYS:
            normalized[key] = _coerce_bool_string(raw_value, key)
            continue

        if key in _INT_KEYS:
            normalized[key] = _coerce_positive_int(raw_value, key)
            continue

        text = str(raw_value or "").strip()
        if not text:
            raise ValueError(f"{key} cannot be empty")
        normalized[key] = text

    if "AI_PROVIDER" in normalized:
        provider = normalized["AI_PROVIDER"].strip().lower()
        if provider not in ALLOWED_AI_PROVIDERS:
            raise ValueError(f"AI_PROVIDER must be one of: {', '.join(sorted(ALLOWED_AI_PROVIDERS))}")
        normalized["AI_PROVIDER"] = provider

    if "SEARCH_PROVIDER" in normalized:
        provider = normalized["SEARCH_PROVIDER"].strip().lower()
        if provider not in ALLOWED_SEARCH_PROVIDERS:
            raise ValueError(
                f"SEARCH_PROVIDER must be one of: {', '.join(sorted(ALLOWED_SEARCH_PROVIDERS))}"
            )
        normalized["SEARCH_PROVIDER"] = provider

    if "DEFAULT_LANGUAGE" in normalized:
        language = normalized["DEFAULT_LANGUAGE"].strip().lower()
        if not re.fullmatch(r"[a-z]{2}", language):
            raise ValueError("DEFAULT_LANGUAGE must be a two-letter language code (e.g. en)")
        normalized["DEFAULT_LANGUAGE"] = language

    return normalized


def merge_settings(
    current: Optional[Dict[str, str]] = None,
    updates: Optional[Dict[str, str]] = None,
) -> Dict[str, str]:
    merged = dict(DEFAULT_VALUES)
    if current:
        merged.update({key: value for key, value in current.items() if key in MANAGED_KEYS})
    if updates:
        merged.update(updates)
    return merged


def serialize_env_file(values: Dict[str, str], extra: Optional[Dict[str, str]] = None) -> str:
    """Write managed keys in canonical section order; append unknown keys at the end."""
    lines: List[str] = []
    for section in SETTINGS_SECTIONS:
        lines.append(f"# {section['title']}")
        for key in section["keys"]:
            if key in values:
                lines.append(f"{key}={values[key]}")
        lines.append("")

    if extra:
        lines.append("# Additional variables")
        for key in sorted(extra):
            lines.append(f"{key}={extra[key]}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def read_env_settings(env_path: Optional[str] = None) -> Dict[str, Any]:
    """Load operator settings for the Web UI (API key masked)."""
    path = resolve_env_path(env_path)
    parsed = parse_env_assignments(path)
    merged = merge_settings(parsed)
    extra = {key: value for key, value in parsed.items() if key not in MANAGED_KEYS}

    api_key = merged.get("GEMINI_API_KEY", "")

    return {
        "env_path": path,
        "env_exists": os.path.exists(path),
        "gemini_api_key_configured": bool(api_key),
        "values": merged,
        "sections": [
            {
                "id": section["id"],
                "title": section["title"],
                "fields": [
                    {
                        "key": key,
                        "value": merged.get(key, DEFAULT_VALUES.get(key, "")),
                        "type": (
                            "boolean"
                            if key in _BOOL_KEYS
                            else "integer"
                            if key in _INT_KEYS
                            else "select"
                            if key == "SEARCH_PROVIDER"
                            else "text"
                        ),
                        "options": (
                            sorted(ALLOWED_SEARCH_PROVIDERS)
                            if key == "SEARCH_PROVIDER"
                            else None
                        ),
                    }
                    for key in section["keys"]
                ],
            }
            for section in SETTINGS_SECTIONS
        ],
        "extra_keys": sorted(extra.keys()),
    }


def save_env_settings(
    updates: Dict[str, Any],
    env_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Persist operator settings to .env and return the masked read payload."""
    path = resolve_env_path(env_path)
    current = parse_env_assignments(path)
    normalized_updates = normalize_settings_updates(updates, existing=current)
    merged = merge_settings(current, normalized_updates)
    extra = {key: value for key, value in current.items() if key not in MANAGED_KEYS}

    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        f.write(serialize_env_file(merged, extra=extra or None))

    return read_env_settings(path)