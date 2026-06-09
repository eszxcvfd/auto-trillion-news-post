import os
from dataclasses import dataclass
from typing import List, Optional

DISABLED_PREFIX = "#kw:"


@dataclass
class KeywordRecord:
    text: str
    enabled: bool = True


def resolve_keywords_path(filepath: Optional[str] = None) -> str:
    """Resolve the canonical keywords file path."""
    raw = filepath or os.getenv("KEYWORDS_FILE", "keywords.txt")
    return os.path.abspath(raw)


def _parse_keyword_line(line: str) -> Optional[KeywordRecord]:
    stripped = line.strip()
    if not stripped:
        return None
    if stripped.startswith(DISABLED_PREFIX):
        text = stripped[len(DISABLED_PREFIX) :].strip()
        if not text:
            return None
        return KeywordRecord(text=text, enabled=False)
    if stripped.startswith("#"):
        return None
    return KeywordRecord(text=stripped, enabled=True)


def load_keyword_records(filepath: Optional[str] = None) -> List[KeywordRecord]:
    """Load all keyword records including disabled entries."""
    path = resolve_keywords_path(filepath)
    if not os.path.exists(path):
        return []
    records: List[KeywordRecord] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            record = _parse_keyword_line(line)
            if record is not None:
                records.append(record)
    return records


def load_active_keywords(filepath: Optional[str] = None) -> List[str]:
    """Return enabled keywords only — used by harvest/search pipeline."""
    return [record.text for record in load_keyword_records(filepath) if record.enabled]


def normalize_keyword_records(records: List[KeywordRecord]) -> List[KeywordRecord]:
    """Trim, drop empty entries, and reject duplicates (case-insensitive)."""
    if records is None:
        raise ValueError("keywords list is required")

    normalized: List[KeywordRecord] = []
    seen = set()
    for record in records:
        text = str(record.text or "").strip()
        if not text:
            continue
        key = text.casefold()
        if key in seen:
            raise ValueError(f"Duplicate keyword: '{text}'")
        seen.add(key)
        normalized.append(KeywordRecord(text=text, enabled=bool(record.enabled)))
    return normalized


def serialize_keyword_records(records: List[KeywordRecord]) -> str:
    lines = []
    for record in records:
        if record.enabled:
            lines.append(record.text)
        else:
            lines.append(f"{DISABLED_PREFIX} {record.text}")
    return "\n".join(lines) + ("\n" if lines else "")


def save_keyword_records(records: List[KeywordRecord], filepath: Optional[str] = None) -> str:
    """Persist keyword records to disk after validation."""
    path = resolve_keywords_path(filepath)
    normalized = normalize_keyword_records(records)
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(serialize_keyword_records(normalized))
    return path


def keyword_records_to_api(records: List[KeywordRecord]) -> List[dict]:
    return [
        {"id": idx, "text": record.text, "enabled": record.enabled}
        for idx, record in enumerate(records)
    ]