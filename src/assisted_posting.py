import os
import sys
import time

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None

from src.models import NewsItem
from src.config import AppConfig

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
        # Fallback to reading the entire file if marker is not found
        return content.strip()
        
    post_body = content[idx + len(marker):].strip()
    return post_body

def run_assisted_posting(item: NewsItem, config: AppConfig, post_content: str = None) -> bool:
    """
    Launches Playwright in non-headless mode, opens LinkedIn,
    pastes the post draft, uploads the screenshot (if exists),
    and waits for manual user review.
    """
    if sync_playwright is None:
        print("[ERROR] Playwright is not installed. Please run pip install -r requirements.txt to install it.")
        return False

    # 1. Parse post content
    if post_content is None:
        if not item.generated_post_file:
            print(f"[ERROR] No generated post file path found for ID {item.id}.")
            return False
            
        post_content = parse_post_markdown(item.generated_post_file)
        
    if not post_content:
        print(f"[ERROR] Empty post content for ID {item.id}.")
        return False

    # 2. Check screenshot
    image_path = None
    if item.image_file:
        test_path = os.path.join(config.image_dir, item.image_file)
        if os.path.exists(test_path):
            image_path = os.path.abspath(test_path)
            print(f"[INFO] Found image to upload: {image_path}")
        else:
            print(f"[WARNING] Image file not found at path: {test_path}")

    # 3. Define persistent browser context directory
    browser_context_dir = os.path.abspath(os.path.join(config.output_dir, ".browser_context"))
    print(f"[INFO] Using persistent browser context: {browser_context_dir}")
    
    print("[INFO] Launching Chromium in non-headless mode...")

    launch_kwargs = {
        "user_data_dir": browser_context_dir,
        "headless": False,
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "viewport": {"width": 1280, "height": 800},
        "args": ["--disable-extensions"],
        "locale": "en-US",
    }
    if getattr(config, "playwright_chromium_executable_path", None):
        launch_kwargs["executable_path"] = config.playwright_chromium_executable_path
    
    with sync_playwright() as p:
        # Launch persistent context
        context = p.chromium.launch_persistent_context(**launch_kwargs)
        
        page = context.new_page() if not context.pages else context.pages[0]
        
        # Proceed directly without blocking telemetry or overriding fetch to prevent triggering LinkedIn's anti-bot detection
        
        try:
            print("[INFO] Navigating to LinkedIn feed...")
            page.goto("https://www.linkedin.com/feed/", timeout=45000)
            
            start_post_selectors = [
                "button.share-box-feed-entry__trigger",
                "span.share-box-feed-entry__trigger-span",
                "button:has-text('Start a post')",
                "button:has-text('Đăng bài viết')",
                "button:has-text('Viết bài')",
                "button:has-text('Bắt đầu bài viết')",
                "button:has-text('Bắt đầu một bài viết')",
                "button:has-text('Tạo bài viết')",
                "button:has-text('Bắt đầu bài đăng')",
                "span:has-text('Start a post')",
                "span:has-text('Viết bài')",
                "span:has-text('Bắt đầu bài viết')",
                "span:has-text('Bắt đầu một bài viết')",
                "span:has-text('Tạo bài viết')",
                "span:has-text('Bắt đầu bài đăng')",
                "div[role='button']:has-text('Bắt đầu bài đăng')",
                "div[role='button']:has-text('Start a post')",
                "div[role='button']:has-text('Đăng bài viết')",
                "div[role='button']:has-text('Viết bài')",
                "div[role='button']:has-text('Bắt đầu bài viết')",
                "div.share-box-feed-entry__trigger",
                "button[aria-haspopup='dialog']",
                ".share-box-feed-entry__trigger"
            ]
            
            logged_in = False
            # Wait up to 180 seconds for login (user input)
            print("[INFO] Checking login status...")
            for attempt in range(60):
                # Check if any start post selector is present and visible
                for sel in start_post_selectors:
                    try:
                        elem = page.query_selector(sel)
                        if elem and elem.is_visible():
                            logged_in = True
                            break
                    except Exception:
                        pass
                if logged_in:
                    break
                
                # Fallback: check if we are obviously logged in by checking the URL or global navigation
                try:
                    if "feed" in page.url or page.query_selector("#global-nav") or page.query_selector(".global-nav") or page.query_selector(".global-nav__me"):
                        logged_in = True
                        break
                except Exception:
                    pass
                
                # Check if we are obviously on a login page
                if "login" in page.url or page.query_selector("input#username"):
                    print("[INFO] Please log in to LinkedIn in the browser window...", end="\r")
                
            if logged_in:
                # Wait for feed elements to fully render
                feed_loaded = False
                for _ in range(30):
                    for sel in start_post_selectors:
                        try:
                            elem = page.query_selector(sel)
                            if elem and elem.is_visible():
                                feed_loaded = True
                                break
                        except Exception:
                            pass
                    if feed_loaded:
                        break
                    page.wait_for_timeout(500)
                    
            if not logged_in:
                print("\n[ERROR] Login timeout or 'Start a post' button not found.")
                print("[INFO] Fallback: Printing post content so you can paste manually:")
                print("="*60)
                print(post_content)
                print("="*60)
                if image_path:
                    print(f"Image Path: {image_path}")
                input("Press Enter to close browser and return...")
                return False
                
            print("\n[SUCCESS] Logged in successfully!")
            
            # Click "Start a post" and wait for editor
            editor_selectors = [
                "div.ql-editor[role='textbox']",
                "div[role='textbox'][aria-label*='editor']",
                "div[role='textbox'][aria-label*='bài viết']",
                "div[role='textbox'][aria-label*='bài đăng']",
                "div[role='textbox'][aria-label*='đăng']",
                "div[role='textbox'][aria-label*='nội dung']",
                "div[role='textbox'][aria-label*='content']",
                "div[role='textbox'][aria-label*='post']",
                "div[role='textbox']",
                ".editor-container div[contenteditable='true']",
                "div[contenteditable='true']"
            ]

            editor_found = False
            active_editor_selector = None

            # First, check if the composer editor is already open
            for ed_sel in editor_selectors:
                try:
                    ed_elem = page.query_selector(ed_sel)
                    if ed_elem and ed_elem.is_visible():
                        active_editor_selector = ed_sel
                        editor_found = True
                        print(f"[INFO] Editor already open: {ed_sel}")
                        break
                except Exception:
                    pass

            if not editor_found:
                print("[INFO] Attempting to open post composer...")
                for sel in start_post_selectors:
                    try:
                        elem = page.query_selector(sel)
                        if elem and elem.is_visible():
                            print(f"[INFO] Clicking start post element: {sel}")
                            # Try normal click
                            try:
                                elem.click(timeout=3000)
                            except Exception:
                                # Try forced click
                                try:
                                    elem.click(force=True, timeout=3000)
                                except Exception:
                                    # Try JS click
                                    page.evaluate("el => el.click()", elem)

                            # Wait a moment for click animation / modal load to start
                            page.wait_for_timeout(1000)

                            # Poll for editor to appear (up to 10 seconds)
                            for _ in range(20):
                                page.wait_for_timeout(500)
                                for ed_sel in editor_selectors:
                                    try:
                                        ed_elem = page.query_selector(ed_sel)
                                        if ed_elem and ed_elem.is_visible():
                                            active_editor_selector = ed_sel
                                            editor_found = True
                                            break
                                    except Exception:
                                        pass
                                if editor_found:
                                    break
                        if editor_found:
                            break
                    except Exception as e:
                        print(f"[WARNING] Error attempting click on {sel}: {e}")

            if not editor_found:
                raise Exception("LinkedIn post composer editor textbox not found. Both start post click and editor detection failed.")
                
            # Paste post content
            print("[INFO] Pasting post content into editor...")
            page.click(active_editor_selector)
            page.fill(active_editor_selector, post_content)
            # Send End key to trigger focus/change events
            page.keyboard.press("End")
            page.wait_for_timeout(1000)
            
            # Upload image
            if image_path:
                print("[INFO] Attempting to upload image...")
                media_btn_selectors = [
                    "button[aria-label='Add media']",
                    "button.share-promoted-detour-button",
                    ".share-promoted-detour-button",
                    "button[aria-label='Thêm phương tiện truyền thông']",
                    "button[aria-label='Thêm ảnh']",
                    "button.share-promoted-detour-button[aria-label*='photo']",
                    "button.share-promoted-detour-button[aria-label*='ảnh']",
                    "button[aria-label*='Ảnh']",
                    "button[aria-label*='ảnh']",
                    "button[aria-label*='phương tiện']",
                    "button[aria-label*='Media']",
                    "button[aria-label*='media']",
                    "button:has-text('Media')",
                    "button:has-text('Ảnh')",
                    "div[role='button']:has-text('Ảnh')",
                    "div[role='button']:has-text('Media')",
                    "div[role='button']:has-text('Thêm ảnh')",
                    "div[role='button'][aria-label*='ảnh']",
                    "div[role='button'][aria-label*='Ảnh']",
                    "div[role='button'][aria-label*='media']",
                    "div[role='button'][aria-label*='Media']"
                ]
                
                uploaded = False
                for btn_sel in media_btn_selectors:
                    try:
                        btn = page.query_selector(btn_sel)
                        if btn and btn.is_visible():
                            # standard way using expect_file_chooser
                            with page.expect_file_chooser(timeout=5000) as fc_info:
                                btn.click()
                            file_chooser = fc_info.value
                            file_chooser.set_files(image_path)
                            uploaded = True
                            print("[SUCCESS] Image uploaded via file chooser!")
                            break
                    except Exception:
                        pass
                
                if not uploaded:
                    # Fallback to direct input selection
                    try:
                        file_input = page.query_selector("input[type='file']")
                        if file_input:
                            file_input.set_input_files(image_path)
                            uploaded = True
                            print("[SUCCESS] Image uploaded via direct input[type='file']!")
                    except Exception as e:
                        print(f"[WARNING] Direct image upload failed: {e}")
                        
                if not uploaded:
                    print(f"[WARNING] Could not upload image automatically. Please upload it manually.")
                    print(f"Image to upload: {image_path}")
            
            print("\n" + "="*50)
            print("[SUCCESS] Post content successfully prepared in browser!")
            print("Please review the post draft in the browser window.")
            print("DO NOT close the browser window yourself.")
            print("Make any edits if needed and click 'Post' in the browser when ready.")
            print("="*50 + "\n")
            
            # CLI prompt
            time.sleep(1) # Let stdout print cleanly
            ans = input("Did you successfully publish the post? [y/N]: ").strip().lower()
            success = ans in ["y", "yes"]
            
            return success
            
        except Exception as e:
            print(f"\n[ERROR] Assisted posting failed: {e}")
            print("[INFO] Fallback: Copy and paste the post content below manually:")
            print("="*60)
            print(post_content)
            print("="*60)
            if image_path:
                print(f"Image Path: {image_path}")
            print("\n")
            input("Press Enter to close browser and return...")
            return False
            
        finally:
            context.close()
