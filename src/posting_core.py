import re
from typing import List, Dict, Tuple, Optional, TYPE_CHECKING
from src.models import (
    BusinessWorkbookRow,
    PlatformPostState,
    LinkPostDocument,
    PostingCandidate,
    PostingPlan
)

if TYPE_CHECKING:
    from src.config import AppConfig

# Canonical mapping of platform names (lowercase -> display name)
PLATFORM_CANONICAL = {
    "linkedin": "LinkedIn",
    "facebook": "Facebook",
    "x": "X",
    "x (twitter)": "X",
    "twitter": "X",
    "instagram": "Instagram",
    "pinterest": "Pinterest",
    "threads": "Threads",
    "tiktok": "TikTok",
    "youtube": "YouTube"
}

# Stable ordering for manual platform selection prompts
PLATFORM_ORDER = [
    "linkedin", "facebook", "x", "instagram",
    "pinterest", "threads", "tiktok", "youtube"
]

# Inverse lookup for attribute names
PLATFORM_ATTRS = {
    "linkedin": "linkedin_draft",
    "facebook": "facebook_draft",
    "x": "x_draft",
    "instagram": "instagram_draft",
    "pinterest": "pinterest_draft",
    "threads": "threads_draft",
    "tiktok": "tiktok_draft",
    "youtube": "youtube_draft"
}


def canonicalize_platform(name: str) -> str:
    """
    Convert any platform name variant to its canonical key (lowercase).
    Raises ValueError if platform is not supported.
    """
    normalized = str(name).strip().lower()
    if normalized in PLATFORM_CANONICAL:
        return PLATFORM_CANONICAL[normalized].lower()
    
    # Check if any canonical name contains the string
    for k, v in PLATFORM_CANONICAL.items():
        if normalized == v.lower():
            return v.lower()
            
    raise ValueError(f"Unsupported platform: '{name}'")


def parse_link_post_document(raw_text: Optional[str]) -> LinkPostDocument:
    """
    Parse the multi-line Link Post text cell.
    Expected format:
      Platform: Value
    e.g.
      LinkedIn: https://...
      X: [posted-no-link]
      Facebook: [error] authorization failed
      
    Allowed value patterns:
      - Success URL: starting with http:// or https://
      - Tag [posted-no-link]
      - Tag [pending]
      - Tag [skip] <optional reason>
      - Tag [error] <optional reason>
      - Tag [login-required]
      
    Raises ValueError if formatting is malformed to report to the operator.
    """
    states: Dict[str, PlatformPostState] = {}
    if not raw_text:
        return LinkPostDocument(raw_text=raw_text, states=states)
        
    lines = raw_text.splitlines()
    for line_idx, line in enumerate(lines):
        line_stripped = line.strip()
        if not line_stripped:
            continue
            
        if ":" not in line_stripped:
            raise ValueError(
                f"Malformed Link Post line {line_idx + 1}: '{line_stripped}' - missing ':' separator."
            )
            
        prefix, suffix = line_stripped.split(":", 1)
        platform_raw = prefix.strip()
        val_raw = suffix.strip()
        
        try:
            platform_key = canonicalize_platform(platform_raw)
        except ValueError:
            raise ValueError(
                f"Malformed Link Post line {line_idx + 1}: '{line_stripped}' - unrecognized platform '{platform_raw}'."
            )
            
        canonical_display_name = PLATFORM_CANONICAL[platform_key]
        
        # Validate the value syntax
        val_lower = val_raw.lower()
        if val_lower.startswith("http://") or val_lower.startswith("https://"):
            status_type = "success"
        elif val_lower.startswith("[posted-no-link]"):
            status_type = "success"
        elif val_lower.startswith("[skip]"):
            status_type = "skip"
        elif val_lower.startswith("[pending]") or val_lower.startswith("[error]") or val_lower.startswith("[login-required]"):
            status_type = "retryable"
        else:
            raise ValueError(
                f"Malformed Link Post line {line_idx + 1}: '{line_stripped}' - invalid status value '{val_raw}'. "
                f"Allowed values are URLs (http/https) or tags: [posted-no-link], [skip], [pending], [error], [login-required]."
            )
            
        states[platform_key] = PlatformPostState(
            platform=canonical_display_name,
            status_type=status_type,
            raw_value=val_raw
        )
        
    return LinkPostDocument(raw_text=raw_text, states=states)


def serialize_link_post_document(doc: LinkPostDocument) -> str:
    """
    Serialize LinkPostDocument back into a clean multi-line string.
    """
    lines = []
    # Order by canonical display names for neatness
    sorted_keys = sorted(doc.states.keys(), key=lambda k: PLATFORM_CANONICAL[k])
    for k in sorted_keys:
        state = doc.states[k]
        lines.append(f"{state.platform}: {state.raw_value}")
    return "\n".join(lines)


def evaluate_row_eligibility(
    row: BusinessWorkbookRow,
    platform: str,
    config: Optional["AppConfig"] = None,
    workbook_path: Optional[str] = None,
    manual_retry: bool = False,
) -> Tuple[str, Optional[str]]:
    """
    Evaluate whether a row is eligible to be posted on a given platform.
    
    Returns a tuple:
      (eligibility_status, reason)
    Where eligibility_status can be:
      - 'eligible': Row can be posted. Reason is None.
      - 'skipped_no_content': Platform draft is missing/whitespace/'.'
      - 'skipped_already_posted': Platform has already been successfully posted.
      - 'skipped_explicit_skip': Platform is marked as [skip] in Link Post.
      
    When manual_retry is True (Web UI manual post), operator [skip] states are
    treated as retryable so a skipped assisted-post attempt can be launched again.
    """
    try:
        platform_key = canonicalize_platform(platform)
    except ValueError as e:
        return "skipped_invalid_platform", str(e)
        
    # 1. Check if draft content exists
    attr_name = PLATFORM_ATTRS.get(platform_key)
    if not attr_name:
        return "skipped_invalid_platform", f"No attribute mapping for platform '{platform}'"
        
    draft_val = getattr(row, attr_name, None)
    if not draft_val:
        return "skipped_no_content", "No draft content"
        
    # 2. Check Link Post status
    if row.link_post_raw:
        # If parsing fails, we let it propagate to prevent silently ignoring errors
        link_post_doc = parse_link_post_document(row.link_post_raw)
        
        if platform_key in link_post_doc.states:
            state = link_post_doc.states[platform_key]
            if state.status_type == "success":
                return "skipped_already_posted", f"Already posted ({state.raw_value})"
            elif state.status_type == "skip":
                if manual_retry:
                    pass
                else:
                    return "skipped_explicit_skip", f"Explicitly skipped ({state.raw_value})"
            elif state.status_type == "retryable":
                pass

    if config is not None:
        from src.platform_capabilities import check_platform_media_requirements

        media_status, media_reason = check_platform_media_requirements(
            platform_key,
            row.image_link,
            config=config,
            workbook_path=workbook_path,
        )
        if media_status != "ok":
            return media_status, media_reason
                
    return "eligible", None


def list_row_post_blockers(
    row: BusinessWorkbookRow,
    config: Optional["AppConfig"] = None,
    workbook_path: Optional[str] = None,
    manual_retry: bool = False,
) -> List[Dict[str, str]]:
    """Return operator-facing blockers for platforms with draft or Link Post state."""
    link_states: Dict[str, PlatformPostState] = {}
    if row.link_post_raw:
        link_states = parse_link_post_document(row.link_post_raw).states

    blockers: List[Dict[str, str]] = []
    for platform_key in PLATFORM_ORDER:
        attr_name = PLATFORM_ATTRS[platform_key]
        draft_val = getattr(row, attr_name, None)
        has_link_state = platform_key in link_states
        if not draft_val and not has_link_state:
            continue

        status, reason = evaluate_row_eligibility(
            row,
            platform_key,
            config=config,
            workbook_path=workbook_path,
            manual_retry=manual_retry,
        )
        if status == "eligible":
            continue
        blockers.append({
            "platform": platform_key,
            "label": PLATFORM_CANONICAL[platform_key],
            "status": status,
            "reason": reason or "Not eligible",
        })
    return blockers


def list_eligible_platforms(
    row: BusinessWorkbookRow,
    config: Optional["AppConfig"] = None,
    workbook_path: Optional[str] = None,
    manual_retry: bool = False,
) -> List[Tuple[str, str]]:
    """
    Return eligible (platform_key, draft_content) pairs for a workbook row.
    Platforms are returned in canonical display order.
    """
    eligible: List[Tuple[str, str]] = []
    for platform_key in PLATFORM_ORDER:
        status, _ = evaluate_row_eligibility(
            row,
            platform_key,
            config=config,
            workbook_path=workbook_path,
            manual_retry=manual_retry,
        )
        if status != "eligible":
            continue
        attr_name = PLATFORM_ATTRS[platform_key]
        draft_val = getattr(row, attr_name)
        eligible.append((platform_key, draft_val))
    return eligible


def resolve_manual_post_target(
    row: BusinessWorkbookRow,
    platform: Optional[str] = None,
    config: Optional["AppConfig"] = None,
    workbook_path: Optional[str] = None,
) -> Tuple[str, str]:
    """
    Resolve one manual post target as a single row x platform pair.

    Returns (platform_key, draft_content).
    Raises ValueError with operator-facing feedback when the target cannot be resolved.
    """
    eligible = list_eligible_platforms(
        row,
        config=config,
        workbook_path=workbook_path,
        manual_retry=True,
    )
    if not eligible:
        blockers = list_row_post_blockers(
            row,
            config=config,
            workbook_path=workbook_path,
            manual_retry=True,
        )
        if blockers:
            details = "; ".join(
                f"{b['label']}: {b['reason']}" for b in blockers[:4]
            )
            raise ValueError(
                "No eligible platforms to post for this row. "
                f"Blocked targets — {details}"
            )
        raise ValueError(
            "No eligible platforms to post for this row. "
            "Generate drafts for this row first, then retry posting."
        )

    if platform is None:
        if len(eligible) == 1:
            return eligible[0]
        labels = [PLATFORM_CANONICAL[p] for p, _ in eligible]
        raise ValueError(
            f"Multiple eligible platforms found ({', '.join(labels)}). "
            "Specify one platform target."
        )

    try:
        platform_key = canonicalize_platform(platform)
    except ValueError as e:
        raise ValueError(str(e)) from e

    for p_key, draft_val in eligible:
        if p_key == platform_key:
            return p_key, draft_val

    status, reason = evaluate_row_eligibility(
        row,
        platform_key,
        config=config,
        workbook_path=workbook_path,
        manual_retry=True,
    )
    display_name = PLATFORM_CANONICAL[platform_key]
    if status == "skipped_no_content":
        raise ValueError(
            f"No draft content for platform '{display_name}' on this row. "
            "Please run generate first."
        )
    if status == "skipped_already_posted":
        raise ValueError(
            f"Platform '{display_name}' is already posted on this row ({reason})."
        )
    if status == "skipped_explicit_skip":
        raise ValueError(
            f"Platform '{display_name}' is explicitly skipped on this row ({reason})."
        )
    raise ValueError(
        f"Platform '{display_name}' is not eligible for posting on this row"
        + (f": {reason}" if reason else ".")
    )


def build_posting_plan(
    rows: List[BusinessWorkbookRow],
    platforms: List[str],
    limit_per_platform: int = 2,
    config: Optional["AppConfig"] = None,
    workbook_path: Optional[str] = None,
) -> PostingPlan:
    """
    Build a PostingPlan for the run.
    Iterates rows across sheets and ranks candidates per platform up to limit_per_platform.
    """
    # Canonicalize requested platforms
    canonical_platforms = []
    for p in platforms:
        try:
            canonical_platforms.append(canonicalize_platform(p))
        except ValueError:
            pass # Ignore invalid requested platforms in planning
            
    candidates: Dict[str, List[PostingCandidate]] = {p: [] for p in canonical_platforms}
    skipped_summary: List[str] = []
    
    # Count of eligible items accepted per platform
    accepted_counts: Dict[str, int] = {p: 0 for p in canonical_platforms}
    
    for row in rows:
        for p_key in canonical_platforms:
            display_name = PLATFORM_CANONICAL[p_key]
            attr_name = PLATFORM_ATTRS[p_key]
            draft_val = getattr(row, attr_name)
            
            # Run eligibility check
            # Wrap in try-except to catch Link Post parse errors with row/sheet context
            try:
                status, reason = evaluate_row_eligibility(
                    row,
                    p_key,
                    config=config,
                    workbook_path=workbook_path,
                )
            except Exception as e:
                # Add row context to the parse error
                err_msg = f"Sheet '{row.sheet_name}', Row {row.row_idx} (ID: {row.id}) Link Post parse error: {e}"
                raise ValueError(err_msg) from e
                
            if status == "eligible":
                candidate = PostingCandidate(
                    sheet_name=row.sheet_name,
                    row_idx=row.row_idx,
                    id=row.id,
                    title=row.title,
                    platform=display_name,
                    draft_content=draft_val,
                    image_link=row.image_link
                )
                
                # Check limits
                if accepted_counts[p_key] < limit_per_platform:
                    candidates[p_key].append(candidate)
                    accepted_counts[p_key] += 1
                else:
                    skipped_summary.append(
                        f"Sheet '{row.sheet_name}', Row {row.row_idx} (ID: {row.id}) skipped for platform '{display_name}' because maximum limit of {limit_per_platform} was reached."
                    )
            else:
                skipped_summary.append(
                    f"Sheet '{row.sheet_name}', Row {row.row_idx} (ID: {row.id}) skipped for platform '{display_name}': {reason}"
                )
                
    return PostingPlan(candidates=candidates, skipped_summary=skipped_summary)
