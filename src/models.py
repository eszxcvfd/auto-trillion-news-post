from dataclasses import dataclass, asdict
from typing import Optional

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
