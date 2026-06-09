import os
from typing import Optional


def looks_like_file_reference(value: str) -> bool:
    normalized = value.replace("\\", "/").strip()
    return (
        normalized.endswith(".md")
        or normalized.startswith("./")
        or normalized.startswith("posts/")
        or "/posts/" in normalized
    )


def resolve_post_draft_path(
    cell_value: str,
    workbook_path: Optional[str] = None,
    post_dir: Optional[str] = None,
) -> Optional[str]:
    """Resolve a draft cell file reference to an existing markdown path."""
    if not cell_value:
        return None

    cell_value = str(cell_value).strip()
    if not cell_value:
        return None

    candidates = []
    workbook_dir = os.path.dirname(os.path.abspath(workbook_path)) if workbook_path else None
    basename = os.path.basename(cell_value.replace("\\", "/"))

    if os.path.isabs(cell_value):
        candidates.append(cell_value)

    candidates.append(cell_value)

    if workbook_dir:
        candidates.append(os.path.join(workbook_dir, cell_value))
        candidates.append(os.path.join(workbook_dir, "posts", basename))

        normalized = cell_value.replace("\\", "/")
        if normalized.startswith("./output/posts/") or normalized.startswith("output/posts/"):
            candidates.append(os.path.join(workbook_dir, "posts", basename))

    if post_dir:
        candidates.append(os.path.join(os.path.abspath(post_dir), basename))

    seen = set()
    for candidate in candidates:
        resolved = os.path.normpath(candidate)
        if resolved in seen:
            continue
        seen.add(resolved)
        if os.path.exists(resolved) and os.path.isfile(resolved):
            return resolved

    return None


def load_draft_from_cell(
    cell_value,
    workbook_path: Optional[str] = None,
    post_dir: Optional[str] = None,
) -> Optional[str]:
    """Load draft body from an inline cell value or referenced markdown file."""
    if cell_value is None:
        return None

    value = str(cell_value).strip()
    if not value or value == ".":
        return None

    resolved_path = resolve_post_draft_path(value, workbook_path, post_dir)
    if resolved_path:
        from src.assisted_posting import parse_post_markdown

        parsed = parse_post_markdown(resolved_path)
        return parsed if parsed else None

    if looks_like_file_reference(value):
        return None

    return value


def draft_cell_has_content(
    cell_value,
    workbook_path: Optional[str] = None,
    post_dir: Optional[str] = None,
) -> bool:
    return load_draft_from_cell(cell_value, workbook_path, post_dir) is not None


def format_post_path_for_workbook(filepath: str, config) -> str:
    """Store draft references relative to the workbook directory when possible."""
    abs_filepath = os.path.abspath(filepath)
    workbook_file = getattr(config, "excel_file", None)
    if workbook_file:
        workbook_dir = os.path.dirname(os.path.abspath(workbook_file))
        try:
            rel_path = os.path.relpath(abs_filepath, workbook_dir)
            if not rel_path.startswith(".."):
                return rel_path.replace("\\", "/")
        except ValueError:
            pass
    return abs_filepath