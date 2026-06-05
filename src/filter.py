import re
import urllib.parse
from src.models import NewsItem
from src.config import AppConfig

def get_domain(url: str) -> str:
    try:
        parsed = urllib.parse.urlparse(url)
        domain = parsed.netloc.lower()
        if domain.startswith("www."):
            domain = domain[4:]
        return domain
    except Exception:
        return ""

def normalize_url(url: str) -> str:
    try:
        parsed = urllib.parse.urlparse(url)
        # Reconstruct URL without query parameters or fragments
        normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        normalized = normalized.lower().rstrip('/')
        return normalized
    except Exception:
        return url.lower().strip()

def normalize_title(title: str) -> str:
    if not title:
        return ""
    title = title.lower()
    # Remove all non-alphanumeric characters except spaces
    title = re.sub(r'[^a-z0-9\s]', '', title)
    title = " ".join(title.split())
    return title

def is_trillion_news(item: NewsItem, config: AppConfig) -> bool:
    if not item.title:
        return False
        
    title_lower = item.title.lower()
    snippet_lower = (item.snippet or "").lower()
    
    # Check if any required terms are present in title or snippet
    match_found = False
    for term in config.require_terms:
        term_lower = term.lower()
        if term_lower in title_lower or term_lower in snippet_lower:
            match_found = True
            break
            
    if not match_found:
        return False
        
    # Check exclude domains
    if item.url:
        domain = get_domain(item.url)
        for excl_domain in config.exclude_domains:
            if excl_domain.lower() in domain:
                return False
                
    return True

def deduplicate_news(items: list[NewsItem], existing_urls: set[str] = None, existing_titles: set[str] = None) -> list[NewsItem]:
    seen_urls = existing_urls if existing_urls is not None else set()
    seen_titles = existing_titles if existing_titles is not None else set()
    
    unique_items = []
    
    for item in items:
        if not item.url or not item.title:
            continue
            
        norm_url = normalize_url(item.url)
        norm_title = normalize_title(item.title)
        
        if norm_url in seen_urls or norm_title in seen_titles:
            continue
            
        seen_urls.add(norm_url)
        seen_titles.add(norm_title)
        unique_items.append(item)
        
    return unique_items
