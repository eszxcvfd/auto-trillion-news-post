import os
import sys

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None

from src.models import NewsItem
from src.config import AppConfig
from src.platform_posting import (
    prepare_posting_assets,
    run_platform_assisted_posting,
)


def parse_post_markdown(filepath: str) -> str:
    """Reads a generated markdown post file and extracts the content after '## Generated Post'."""
    if not os.path.exists(filepath):
        print(f"[ERROR] Post markdown file not found: {filepath}")
        return ""
        
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
        
    marker = "## Generated Post"
    idx = content.find(marker)
    if idx == -1:
        return content.strip()
        
    post_body = content[idx + len(marker):].strip()
    return post_body


def run_assisted_posting(
    item: NewsItem,
    config: AppConfig,
    post_content: str = None,
    confirm_callback=None,
    workbook_path: str = None,
) -> bool:
    """
    Launch assisted posting for the requested platform using the shared
    platform posting adapters.
    """
    if sync_playwright is None:
        print("[ERROR] Playwright is not installed. Please run pip install -r requirements.txt to install it.")
        return False

    if post_content is None:
        if not item.generated_post_file:
            print(f"[ERROR] No generated post file path found for ID {item.id}.")
            return False
        post_content = parse_post_markdown(item.generated_post_file)

    image_path, error = prepare_posting_assets(
        item, config, post_content, workbook_path=workbook_path
    )
    if error:
        print(f"[ERROR] {error}")
        return False

    if image_path:
        print(f"[INFO] Found image to upload: {image_path}")
    elif item.image_file:
        print(f"[WARNING] Image file not found for reference: {item.image_file}")

    return run_platform_assisted_posting(
        item,
        config,
        post_content,
        image_path,
        confirm_callback=confirm_callback,
    )