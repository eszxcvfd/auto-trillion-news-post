from dataclasses import dataclass, asdict
from typing import Optional, Dict, List

@dataclass
class NewsItem:
    id: Optional[int] = None
    found_date: Optional[str] = None
    keyword: Optional[str] = None
    title: Optional[str] = None
    source: Optional[str] = None
    url: Optional[str] = None
    snippet: Optional[str] = None
    published_text: Optional[str] = None
    image_file: Optional[str] = None
    platform: Optional[str] = None
    top_hashtags: Optional[str] = None
    generated_post_file: Optional[str] = None
    status: str = "new"
    notes: Optional[str] = None

    def to_dict(self):
        return asdict(self)


@dataclass
class BusinessWorkbookRow:
    sheet_name: str
    row_idx: int
    id: Optional[int] = None
    title: Optional[str] = None
    image_link: Optional[str] = None
    linkedin_draft: Optional[str] = None
    facebook_draft: Optional[str] = None
    x_draft: Optional[str] = None
    instagram_draft: Optional[str] = None
    pinterest_draft: Optional[str] = None
    threads_draft: Optional[str] = None
    tiktok_draft: Optional[str] = None
    youtube_draft: Optional[str] = None
    link_post_raw: Optional[str] = None
    broken_draft_refs: Optional[Dict[str, str]] = None

    def to_dict(self):
        return asdict(self)


@dataclass
class PlatformPostState:
    platform: str        # Canonical platform name (e.g. 'LinkedIn')
    status_type: str     # 'success', 'retryable', 'skip'
    raw_value: str       # E.g. 'https://...', '[posted-no-link]', '[error] reason'

    def to_dict(self):
        return asdict(self)


@dataclass
class LinkPostDocument:
    raw_text: Optional[str]
    states: Dict[str, PlatformPostState] # map platform key (lowercase) -> PlatformPostState

    def to_dict(self):
        return {
            "raw_text": self.raw_text,
            "states": {k: v.to_dict() for k, v in self.states.items()}
        }


@dataclass
class PostingCandidate:
    sheet_name: str
    row_idx: int
    id: Optional[int]
    title: str
    platform: str
    draft_content: str
    image_link: Optional[str]

    def to_dict(self):
        return asdict(self)


@dataclass
class PostingPlan:
    candidates: Dict[str, List[PostingCandidate]] # map platform key (lowercase) -> list of candidates
    skipped_summary: List[str] # List of warnings/explanations for skipped rows

    def to_dict(self):
        return {
            "candidates": {k: [c.to_dict() for c in v] for k, v in self.candidates.items()},
            "skipped_summary": self.skipped_summary
        }


