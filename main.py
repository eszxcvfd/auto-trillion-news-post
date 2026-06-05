import os
import argparse
import sys
import json
from src.config import AppConfig
from src.models import NewsItem
from src.searcher import search_news, sync_playwright as search_sync_playwright
from src.filter import is_trillion_news, deduplicate_news

# Embedded defaults
DEFAULT_ENV_EXAMPLE = """# Gemini API Configuration
GEMINI_API_KEY=your_gemini_api_key_here
AI_PROVIDER=gemini
AI_MODEL=gemini-1.5-flash

# Search Configuration
SEARCH_PROVIDER=bing
HEADLESS=false

# Output Configuration
OUTPUT_DIR=./output
EXCEL_FILE=./output/Trillion $ news.xlsx
IMAGE_DIR=./output/Ảnh Trillion $ news
POST_DIR=./output/posts
LOG_DIR=./output/logs

# Run Limits & Preferences
DEFAULT_PLATFORM=linkedin
DEFAULT_LANGUAGE=en
MAX_RESULTS_PER_KEYWORD=10
MAX_POSTS_PER_RUN=5
"""

DEFAULT_CONFIG_YAML = """# Default System Configuration
platform: linkedin
language: en

search:
  provider: bing
  max_results_per_keyword: 10
  require_terms:
    - trillion
    - trillion-dollar
    - "$ trillion"
    - "USD"
  exclude_domains:
    - reddit.com
    - x.com
    - facebook.com

hashtags:
  fixed_bottom:
    - TAHKFoundation
    - HenryUniverses
    - USIran
    - USTariffs
    - Trump

posting:
  mode: draft_only
  human_confirm_before_post: true
"""

DEFAULT_KEYWORDS_TXT = """Payment services trillion $
Mobile payments trillion $
Fintech trillion $
AI trillion dollar market
Healthcare trillion dollar market
Energy trillion dollar market
Real estate trillion dollar market
Banking trillion dollar market
Cross border payments trillion $
Digital payments trillion $
"""

def init_project():
    print("Initializing project scaffolding...")
    
    # Files to create if they don't exist
    files_to_create = {
        ".env.example": DEFAULT_ENV_EXAMPLE,
        "config.yaml": DEFAULT_CONFIG_YAML,
        "keywords.txt": DEFAULT_KEYWORDS_TXT
    }
    
    for filename, content in files_to_create.items():
        if os.path.exists(filename):
            print(f"[INFO] {filename} already exists, skipping.")
        else:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"[SUCCESS] Created {filename}")
            
    # Directories to create
    directories = [
        "output",
        "output/posts",
        "output/Ảnh Trillion $ news",
        "output/logs"
    ]
    
    for directory in directories:
        if os.path.exists(directory):
            print(f"[INFO] Directory {directory} already exists, skipping.")
        else:
            os.makedirs(directory, exist_ok=True)
            print(f"[SUCCESS] Created directory {directory}")
            
    print("Project initialization complete.")

def load_keywords(filepath: str) -> list[str]:
    if not os.path.exists(filepath):
        print(f"[ERROR] Keywords file '{filepath}' does not exist.")
        return []
    keywords = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            keywords.append(line)
    return keywords

def execute_search(keywords_path: str, limit: int = None):
    if search_sync_playwright is None:
        print("[ERROR] Playwright is not installed. Please run pip install -r requirements.txt to install it.")
        return

    # Load configuration
    config = AppConfig()
    
    # Load keywords
    keywords = load_keywords(keywords_path)
    if not keywords:
        print("[ERROR] No keywords found to search.")
        sys.exit(1)
        
    print(f"[INFO] Loaded {len(keywords)} keywords.")
    
    all_raw_news = []
    for kw in keywords:
        raw_news = search_news(kw, config)
        all_raw_news.extend(raw_news)
        
    # Filter
    filtered_news = [item for item in all_raw_news if is_trillion_news(item, config)]
    print(f"[INFO] {len(filtered_news)} / {len(all_raw_news)} articles passed trillion filter.")
    
    # Deduplicate
    unique_news = deduplicate_news(filtered_news)
    print(f"[INFO] {len(unique_news)} articles remaining after deduplication.")
    
    # Apply limit
    if limit is not None:
        unique_news = unique_news[:limit]
    elif config.max_posts_per_run is not None:
        unique_news = unique_news[:config.max_posts_per_run]
        
    # Save to Excel and rename temp screenshots
    from src.excel_store import save_news_to_excel
    saved_news = save_news_to_excel(unique_news, config)
    
    # Format and print JSON
    dict_news = [item.to_dict() for item in saved_news]
    print(json.dumps(dict_news, indent=2, ensure_ascii=False))

def execute_generate(platform: str = None, limit: int = None):
    config = AppConfig()
    
    # Load openpyxl safely
    try:
        import openpyxl
    except ImportError:
        print("[ERROR] openpyxl is not installed. Please run pip install -r requirements.txt to install it.")
        sys.exit(1)
        
    platform = platform or config.default_platform
    
    filepath = config.excel_file
    if not os.path.exists(filepath):
        print(f"[ERROR] Excel file '{filepath}' does not exist. Please run search first.")
        sys.exit(1)
        
    try:
        wb = openpyxl.load_workbook(filepath)
        ws = wb.active
    except Exception as e:
        print(f"[ERROR] Failed to load Excel workbook: {e}")
        sys.exit(1)
        
    # Read rows with status "new"
    new_items = []
    for r in range(2, ws.max_row + 1):
        status_val = ws.cell(row=r, column=13).value
        if status_val == "new":
            item = NewsItem(
                id=ws.cell(row=r, column=1).value,
                found_date=ws.cell(row=r, column=2).value,
                keyword=ws.cell(row=r, column=3).value,
                title=ws.cell(row=r, column=4).value,
                source=ws.cell(row=r, column=5).value,
                url=ws.cell(row=r, column=6).value,
                snippet=ws.cell(row=r, column=7).value,
                published_text=ws.cell(row=r, column=8).value,
                image_file=ws.cell(row=r, column=9).value,
                platform=platform,
                status="new",
                notes=ws.cell(row=r, column=14).value
            )
            try:
                item.id = int(item.id)
            except (ValueError, TypeError):
                pass
            new_items.append(item)
            
    wb.close()
    
    if not new_items:
        print("[INFO] No new items found in Excel to generate posts for.")
        return
        
    print(f"[INFO] Found {len(new_items)} new articles to process.")
    
    # Apply limit
    if limit is not None:
        new_items = new_items[:limit]
    elif config.max_posts_per_run is not None:
        new_items = new_items[:config.max_posts_per_run]
        
    print(f"[INFO] Processing {len(new_items)} articles...")
    
    from src.ai_writer import generate_ai_post, validate_generated_post
    from src.post_writer import write_post_file, update_excel_row_with_post, extract_top_hashtags
    
    for item in new_items:
        print(f"[INFO] Generating post for ID {item.id}: '{item.title}'")
        try:
            content = generate_ai_post(
                title=item.title,
                source=item.source or "",
                snippet=item.snippet or "",
                url=item.url or "",
                platform=platform,
                config=config
            )
            
            if not validate_generated_post(content, platform):
                print(f"[WARNING] Post format validation failed for ID {item.id}.")
                update_excel_row_with_post(
                    item_id=item.id,
                    post_file_path="",
                    top_hashtags="",
                    status="error",
                    config=config,
                    notes="Validation failed: post format did not match requirements."
                )
                continue
                
            post_file = write_post_file(item, content, config)
            top_tags = extract_top_hashtags(content)
            
            update_excel_row_with_post(
                item_id=item.id,
                post_file_path=post_file,
                top_hashtags=top_tags,
                status="generated",
                config=config
            )
            
        except Exception as e:
            print(f"[ERROR] Failed to generate post for ID {item.id}: {e}")
            update_excel_row_with_post(
                item_id=item.id,
                post_file_path="",
                top_hashtags="",
                status="error",
                config=config,
                notes=f"Generation failed: {e}"
            )

def execute_run(keywords_path: str, platform: str = None, limit: int = None):
    missing_dependencies = []

    if search_sync_playwright is None:
        missing_dependencies.append("Playwright")

    try:
        import openpyxl
    except ImportError:
        missing_dependencies.append("openpyxl")

    if missing_dependencies:
        for dependency in missing_dependencies:
            print(f"[ERROR] {dependency} is not installed. Please run pip install -r requirements.txt to install it.")
        return

    print("=== Starting Full Draft Pipeline ===")
    execute_search(keywords_path, limit)
    execute_generate(platform, limit)
    print("=== Full Draft Pipeline Completed ===")

def execute_post(item_id: int, platform: str = None):
    config = AppConfig()
    
    try:
        import openpyxl
    except ImportError:
        print("[ERROR] openpyxl is not installed. Please run pip install -r requirements.txt to install it.")
        sys.exit(1)
        
    platform = platform or config.default_platform
    
    filepath = config.excel_file
    if not os.path.exists(filepath):
        print(f"[ERROR] Excel file '{filepath}' does not exist. Please run search/generate first.")
        sys.exit(1)
        
    try:
        wb = openpyxl.load_workbook(filepath)
        ws = wb.active
    except Exception as e:
        print(f"[ERROR] Failed to load Excel workbook: {e}")
        sys.exit(1)
        
    item = None
    for r in range(2, ws.max_row + 1):
        id_val = ws.cell(row=r, column=1).value
        try:
            current_id = int(id_val)
        except (ValueError, TypeError):
            current_id = id_val
            
        if current_id == item_id:
            item = NewsItem(
                id=current_id,
                found_date=ws.cell(row=r, column=2).value,
                keyword=ws.cell(row=r, column=3).value,
                title=ws.cell(row=r, column=4).value,
                source=ws.cell(row=r, column=5).value,
                url=ws.cell(row=r, column=6).value,
                snippet=ws.cell(row=r, column=7).value,
                published_text=ws.cell(row=r, column=8).value,
                image_file=ws.cell(row=r, column=9).value,
                platform=platform,
                top_hashtags=ws.cell(row=r, column=11).value,
                generated_post_file=ws.cell(row=r, column=12).value,
                status=ws.cell(row=r, column=13).value,
                notes=ws.cell(row=r, column=14).value
            )
            break
            
    wb.close()
    
    if not item:
        print(f"[ERROR] Article with ID {item_id} not found in Excel.")
        sys.exit(1)
        
    if not item.generated_post_file or not os.path.exists(item.generated_post_file):
        print(f"[ERROR] No generated post file found for ID {item_id}. Please run generate first.")
        sys.exit(1)
        
    from src.assisted_posting import run_assisted_posting
    from src.post_writer import update_excel_row_with_post
    
    print(f"[INFO] Launching assisted posting for ID {item_id}: '{item.title}'")
    success = run_assisted_posting(item, config)
    
    if success:
        update_excel_row_with_post(item_id=item_id, status="posted", config=config)
        print(f"[SUCCESS] Post {item_id} successfully marked as 'posted' in Excel.")
    else:
        print(f"[INFO] Post {item_id} was not marked as posted.")
        ans_skip = input("Do you want to mark this item as skipped? [y/N]: ").strip().lower()
        if ans_skip in ["y", "yes"]:
            update_excel_row_with_post(item_id=item_id, status="skipped", config=config)
            print(f"[SUCCESS] Post {item_id} successfully marked as 'skipped' in Excel.")

def main():
    parser = argparse.ArgumentParser(description="Trillion News Auto Post System CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # init command
    subparsers.add_parser("init", help="Initialize project folders and configuration files")
    
    # search command
    search_parser = subparsers.add_parser("search", help="Search and filter news")
    search_parser.add_argument("--keywords", default="keywords.txt", help="Path to keywords file")
    search_parser.add_argument("--limit", type=int, default=None, help="Max results to return")
    
    # generate command
    generate_parser = subparsers.add_parser("generate", help="Generate AI social posts")
    generate_parser.add_argument("--platform", default=None, help="Target social platform (e.g. linkedin)")
    generate_parser.add_argument("--limit", type=int, default=None, help="Max posts to generate")
    
    # run command
    run_parser = subparsers.add_parser("run", help="Run full search and generation draft pipeline")
    run_parser.add_argument("--keywords", default="keywords.txt", help="Path to keywords file")
    run_parser.add_argument("--platform", default=None, help="Target social platform")
    run_parser.add_argument("--limit", type=int, default=None, help="Max posts to generate/return")
    
    # post command
    post_parser = subparsers.add_parser("post", help="Assisted posting on social platforms")
    post_parser.add_argument("--id", type=int, required=True, help="Row ID from Excel to post")
    post_parser.add_argument("--platform", default=None, help="Target social platform (e.g. linkedin)")

    args = parser.parse_args()
    
    if args.command == "init":
        init_project()
    elif args.command == "search":
        execute_search(args.keywords, args.limit)
    elif args.command == "generate":
        execute_generate(args.platform, args.limit)
    elif args.command == "run":
        execute_run(args.keywords, args.platform, args.limit)
    elif args.command == "post":
        execute_post(args.id, args.platform)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
