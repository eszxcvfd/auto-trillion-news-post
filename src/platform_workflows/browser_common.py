import os
import time
from typing import Callable, List, Optional, Tuple

from src.platform_capabilities import (
    get_platform_mvp_mode,
    is_best_effort_posting,
    platform_requires_image,
)
from src.platform_workflows.profiles import PLATFORM_PROFILES, PlatformPostingProfile
from src.posting_core import PLATFORM_CANONICAL

try:
    from playwright.sync_api import Page
except ImportError:
    Page = object  # type: ignore


def first_visible(page: Page, selectors: List[str]):
    for selector in selectors:
        try:
            elem = page.query_selector(selector)
            if elem and elem.is_visible():
                return elem, selector
        except Exception:
            pass
    return None, None


def wait_for_login(page: Page, profile: PlatformPostingProfile, timeout_attempts: int = 60) -> bool:
    print(f"[INFO] Checking login status for {PLATFORM_CANONICAL[profile.key]}...")
    for _ in range(timeout_attempts):
        elem, _ = first_visible(page, profile.start_post_selectors)
        if elem:
            return True

        try:
            if any(marker in page.url for marker in profile.logged_in_url_markers):
                if not any(page.query_selector(sel) for sel in profile.logged_out_selectors):
                    return True
        except Exception:
            pass

        for sel in profile.logged_out_selectors:
            try:
                if page.query_selector(sel):
                    print(
                        f"[INFO] Please log in to {PLATFORM_CANONICAL[profile.key]} in the browser window...",
                        end="\r",
                    )
                    break
            except Exception:
                pass
        page.wait_for_timeout(1000)
    return False


def open_editor(page: Page, profile: PlatformPostingProfile) -> Optional[str]:
    editor, selector = first_visible(page, profile.editor_selectors)
    if editor:
        print(f"[INFO] Editor already open: {selector}")
        return selector

    print("[INFO] Attempting to open post composer...")
    start_elem, start_selector = first_visible(page, profile.start_post_selectors)
    if not start_elem:
        return None

    print(f"[INFO] Clicking start post element: {start_selector}")
    try:
        start_elem.click(timeout=3000)
    except Exception:
        try:
            start_elem.click(force=True, timeout=3000)
        except Exception:
            page.evaluate("el => el.click()", start_elem)

    for _ in range(20):
        page.wait_for_timeout(500)
        editor, selector = first_visible(page, profile.editor_selectors)
        if editor:
            return selector
    return None


def composer_scope(page: Page, profile: PlatformPostingProfile):
    return page


def find_visible_editor(page: Page, profile: PlatformPostingProfile, scope=None):
    search_root = scope or page
    for sel in profile.editor_selectors:
        try:
            if search_root is page:
                candidate = page.query_selector(sel)
            else:
                candidate = search_root.query_selector(sel)
            if candidate and candidate.is_visible():
                return candidate, sel
        except Exception:
            pass
    return None, None


def set_files_on_locator(file_locator, image_path: str) -> bool:
    try:
        file_locator.set_input_files(image_path, timeout=5000)
        return True
    except Exception:
        return False


def upload_image_generic(
    page: Page,
    profile: PlatformPostingProfile,
    image_path: str,
    scope=None,
) -> bool:
    print("[INFO] Attempting to upload image...")
    search_roots = []
    if scope is not None and scope is not page:
        search_roots.append(scope)
    if not search_roots:
        search_roots.append(page)

    for search_root in search_roots:
        for btn_sel in profile.media_button_selectors:
            try:
                btn = search_root.query_selector(btn_sel)
                if not btn:
                    continue
                if btn_sel.startswith("input[type='file']"):
                    btn.set_input_files(image_path)
                    print("[SUCCESS] Image uploaded via direct file input!")
                    return True
                if btn.is_visible():
                    with page.expect_file_chooser(timeout=5000) as fc_info:
                        btn.click()
                    file_chooser = fc_info.value
                    file_chooser.set_files(image_path)
                    print("[SUCCESS] Image uploaded via file chooser!")
                    return True
            except Exception:
                pass

        try:
            file_input = search_root.query_selector("input[type='file'][accept*='image']")
            if not file_input:
                file_input = search_root.query_selector("input[type='file']")
            if file_input:
                file_input.set_input_files(image_path)
                print("[SUCCESS] Image uploaded via scoped file input!")
                return True
        except Exception as e:
            print(f"[WARNING] Direct image upload failed: {e}")
    return False


def paste_post_content_generic(
    page: Page,
    profile: PlatformPostingProfile,
    editor_selector: str,
    post_content: str,
    scope=None,
) -> None:
    print("[INFO] Pasting post content into editor...")
    editor, resolved_selector = find_visible_editor(page, profile, scope=scope)
    target_selector = resolved_selector or editor_selector

    page.click(target_selector)
    page.fill(target_selector, post_content)
    page.keyboard.press("End")
    page.wait_for_timeout(500)


def fill_composer_generic(
    page: Page,
    profile: PlatformPostingProfile,
    editor_selector: str,
    post_content: str,
    image_path: Optional[str],
) -> None:
    scope = composer_scope(page, profile)
    paste_post_content_generic(page, profile, editor_selector, post_content, scope=scope)

    if image_path:
        uploaded = upload_image_generic(page, profile, image_path, scope=scope)
        if not uploaded:
            print("[WARNING] Could not upload image automatically. Please upload it manually.")
            print(f"Image to upload: {image_path}")
    elif platform_requires_image(profile.key):
        print(
            f"[WARNING] {PLATFORM_CANONICAL[profile.key]} expects media, but no image path was resolved."
        )


def run_assisted_flow(
    page: Page,
    profile: PlatformPostingProfile,
    post_content: str,
    image_path: Optional[str],
    confirm_callback: Optional[Callable],
    *,
    open_editor_fn,
    fill_composer_fn,
    wait_for_login_fn=None,
    prepare_feed_fn=None,
) -> Tuple[bool, Optional[str]]:
    display_name = PLATFORM_CANONICAL[profile.key]
    if is_best_effort_posting(profile.key):
        mvp_mode = get_platform_mvp_mode(profile.key)
        print(f"[INFO] Best-effort MVP mode for {display_name}: {mvp_mode}")
        print(
            "[INFO] This adapter does not support full video upload pipelines. "
            "Use the browser UI to finish posting if automation cannot complete every step."
        )

    print(f"[INFO] Navigating to {display_name} feed...")
    page.goto(profile.feed_url, timeout=45000, wait_until="domcontentloaded")
    try:
        page.wait_for_load_state("networkidle", timeout=15000)
    except Exception:
        page.wait_for_timeout(2000)

    if prepare_feed_fn:
        prepare_feed_fn(page, profile)

    login_check = wait_for_login_fn or wait_for_login
    if not login_check(page, profile):
        print(f"\n[ERROR] Login timeout for {display_name}.")
        print("[INFO] Fallback: Printing post content so you can paste manually:")
        print("=" * 60)
        print(post_content)
        print("=" * 60)
        if image_path:
            print(f"Image Path: {image_path}")
        if confirm_callback:
            confirm_callback()
        else:
            input("Press Enter to close browser and return...")
        return False, None

    print(f"\n[SUCCESS] Logged in to {display_name}!")
    editor_selector = open_editor_fn(page, profile)
    if not editor_selector:
        raise RuntimeError(f"{display_name} post composer editor was not found.")

    fill_composer_fn(page, profile, editor_selector, post_content, image_path)

    print("\n" + "=" * 50)
    print("[SUCCESS] Post content successfully prepared in browser!")
    print("Please review the post draft in the browser window.")
    print("DO NOT close the browser window yourself.")
    print("Make any edits if needed and click 'Post' in the browser when ready.")
    print("=" * 50 + "\n")

    time.sleep(1)
    post_url = None
    if confirm_callback:
        success, post_url = confirm_callback()
    else:
        ans = input("Did you successfully publish the post? [y/N]: ").strip().lower()
        success = ans in ["y", "yes"]
        if success:
            post_url = input(
                "Enter the post URL (optional, press Enter to use '[posted-no-link]'): "
            ).strip()
    return success, post_url


def validate_session_for_profile(page: Page, profile: PlatformPostingProfile) -> bool:
    page.goto(profile.feed_url, timeout=15000)
    if first_visible(page, profile.start_post_selectors)[0]:
        return True
    try:
        if any(marker in page.url for marker in profile.logged_in_url_markers):
            if not any(page.query_selector(sel) for sel in profile.logged_out_selectors):
                return True
    except Exception:
        pass
    return False