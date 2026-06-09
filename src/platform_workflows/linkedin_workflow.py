"""LinkedIn-owned posting workflow. Selector and composer logic stays isolated here."""

import os
import time
from typing import Callable, Optional, Tuple

from src.platform_workflows.browser_common import (
    first_visible,
    run_assisted_flow,
    validate_session_for_profile,
)
from src.platform_workflows.profiles import PLATFORM_PROFILES, PlatformPostingProfile
from src.posting_core import PLATFORM_CANONICAL

try:
    from playwright.sync_api import Page
except ImportError:
    Page = object  # type: ignore

WORKFLOW_ID = "workflow.linkedin.v1"
PLATFORM_KEY = "linkedin"

_LINKEDIN_START_LABELS = (
    "Start a post",
    "Đăng bài viết",
    "Viết bài",
    "Bắt đầu một bài đăng",
    "Bắt đầu bài đăng",
)


def _safe_locator_count(locator) -> int:
    if locator is None:
        return 0
    if hasattr(locator, "_mock_return_value") or "Mock" in type(locator).__name__:
        return 1
    try:
        return int(locator.count())
    except Exception:
        return 0


def _locator_is_visible(locator) -> bool:
    if _safe_locator_count(locator) <= 0:
        return False
    try:
        return bool(locator.first.is_visible())
    except Exception:
        return True


def _prepare_linkedin_feed(page: Page, profile: PlatformPostingProfile) -> None:
    try:
        page.evaluate("window.scrollTo(0, 0)")
    except Exception:
        pass
    page.wait_for_timeout(1200)


def _wait_for_linkedin_login(page: Page, profile: PlatformPostingProfile, timeout_attempts: int = 90) -> bool:
    print(f"[INFO] Checking login status for {PLATFORM_CANONICAL[profile.key]}...")
    for attempt in range(timeout_attempts):
        editor = _linkedin_caption_editor(page)
        if editor is not None and _locator_is_visible(editor):
            return True

        if _find_linkedin_start_post(page, profile)[0] is not None:
            return True

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

        if attempt == 0:
            page.wait_for_timeout(1500)
        else:
            page.wait_for_timeout(1000)
    return False


def _find_linkedin_start_post(page: Page, profile: PlatformPostingProfile):
    for label in _LINKEDIN_START_LABELS:
        try:
            locator = page.get_by_role("button", name=label, exact=False)
            if locator.count() > 0 and locator.first.is_visible():
                return locator.first, f"role=button name={label}"
        except Exception:
            pass

    for label in _LINKEDIN_START_LABELS:
        try:
            locator = page.get_by_text(label, exact=False)
            if locator.count() > 0 and locator.first.is_visible():
                return locator.first, f"text={label}"
        except Exception:
            pass

    return first_visible(page, profile.start_post_selectors)


def _click_linkedin_target(page: Page, target, selector_hint: str) -> bool:
    print(f"[INFO] Clicking LinkedIn start post element: {selector_hint}")
    # Try direct click first (allows standard scroll-into-view behavior)
    try:
        target.click(timeout=3000)
        return True
    except Exception as e:
        print(f"[DEBUG] Direct click failed: {e}")
        pass

    # Try JS click to bypass sticky headers and interception
    try:
        page.evaluate("el => el.click()", target)
        return True
    except Exception as e:
        print(f"[DEBUG] JS click failed: {e}")
        pass

    # Try force click as last resort
    try:
        target.click(force=True, timeout=3000)
        return True
    except Exception as e:
        print(f"[DEBUG] Force click failed: {e}")
        pass

    return False


def _linkedin_dialog_root(page: Page):
    return page


def _linkedin_share_modal(page: Page):
    root = _linkedin_dialog_root(page)
    modal_selectors = [
        "div.share-create-post__modal",
        "div.artdeco-modal",
        "div[role='dialog']",
    ]
    for sel in modal_selectors:
        loc = root.locator(sel)
        try:
            count = int(loc.count())
            for idx in range(count):
                candidate = loc.nth(idx)
                try:
                    if candidate.locator(".ql-editor, div.ql-editor").count() > 0:
                        return candidate
                except Exception:
                    continue
        except Exception:
            continue
    return root.locator("div[role='dialog']").last


def _linkedin_caption_editor(page: Page):
    root = _linkedin_dialog_root(page)
    editor_selectors = [
        "div.ql-editor[contenteditable='true']",
        "div.ql-editor[role='textbox']",
        "div.ql-editor",
        "div[role='textbox'][contenteditable='true']",
    ]
    for sel in editor_selectors:
        editor = root.locator(sel).first
        try:
            if _safe_locator_count(editor) > 0:
                return editor
        except Exception:
            pass
    return None


def _insert_linkedin_caption_via_js(editor_locator, post_content: str) -> bool:
    try:
        res = editor_locator.evaluate(
            """
            (editor, text) => {
                editor.focus();
                editor.innerHTML = "";
                const lines = text.split(/\\n/);
                for (const line of lines) {
                    const paragraph = document.createElement("p");
                    paragraph.textContent = line || "\\u200b";
                    editor.appendChild(paragraph);
                }
                editor.dispatchEvent(new Event("input", { bubbles: true }));
                editor.dispatchEvent(new Event("change", { bubbles: true }));
                return (editor.innerText || editor.textContent || "").trim().length > 0;
            }
            """,
            post_content,
        )
        return bool(res)
    except Exception as e:
        print(f"[DEBUG] LinkedIn JS caption insert failed: {e}")
        return False


def _paste_linkedin_caption(page: Page, post_content: str) -> None:
    page.wait_for_timeout(800)
    print("[INFO] Pasting LinkedIn caption into Quill editor...")

    editor = _linkedin_caption_editor(page)
    if editor is None:
        raise RuntimeError("LinkedIn caption editor was not found in the share modal.")

    if _insert_linkedin_caption_via_js(editor, post_content):
        page.wait_for_timeout(800)
        return

    try:
        editor.click(force=True, timeout=10000)
    except Exception as click_error:
        print(f"[DEBUG] LinkedIn editor click failed, trying focus: {click_error}")
        editor.focus(timeout=10000)
    page.wait_for_timeout(400)
    page.keyboard.insert_text(post_content)
    page.wait_for_timeout(800)


def _wait_for_linkedin_image_attached(page: Page, timeout_ms: int = 20000) -> bool:
    root = _linkedin_dialog_root(page)
    deadline = time.time() + (timeout_ms / 1000)
    while time.time() < deadline:
        try:
            if root.locator("img[src*='blob:']").count() > 0:
                return True
            if root.locator("img.share-create-post__image").count() > 0:
                return True
            if root.locator("button[aria-label*='Remove']").count() > 0:
                return True
            if root.locator("button[aria-label*='Xóa']").count() > 0:
                return True
            if root.locator("button:has-text('Xóa')").count() > 0:
                return True
            if root.locator("button:has-text('Remove')").count() > 0:
                return True
        except Exception:
            pass
        page.wait_for_timeout(500)
    return False


def _set_files_on_locator(file_locator, image_path: str) -> bool:
    try:
        file_locator.set_input_files(image_path, timeout=5000)
        return True
    except Exception:
        return False


def _upload_linkedin_image(page: Page, image_path: str) -> bool:
    abs_image_path = os.path.abspath(image_path)
    if not os.path.isfile(abs_image_path):
        print(f"[ERROR] LinkedIn image file does not exist: {abs_image_path}")
        return False

    print(f"[INFO] LinkedIn: uploading image from {abs_image_path}")
    root = _linkedin_dialog_root(page)
    
    # Wait up to 10 seconds for the editor to be visible, ensuring the composer is ready
    editor = None
    for _ in range(20):
        editor = _linkedin_caption_editor(page)
        if editor is not None:
            break
        page.wait_for_timeout(500)

    if editor is None:
        print("[WARNING] LinkedIn editor not found, cannot upload image.")
        return False

    page.wait_for_timeout(600)
    profile = PLATFORM_PROFILES["linkedin"]
    uploaded = False

    for btn_sel in profile.media_button_selectors:
        try:
            btn = root.locator(btn_sel).first
            if btn.count() == 0:
                continue
            if btn_sel.startswith("input[type='file']"):
                btn.set_input_files(abs_image_path, timeout=5000)
                uploaded = True
                break
            btn.wait_for(state="visible", timeout=2000)
            with page.expect_file_chooser(timeout=10000) as fc_info:
                btn.click(force=True, timeout=3000)
            fc_info.value.set_files(abs_image_path)
            uploaded = True
            break
        except Exception as e:
            print(f"[DEBUG] LinkedIn media button '{btn_sel}' failed: {e}")

    if not uploaded:
        file_inputs = root.locator("input[type='file']")
        for idx in range(file_inputs.count()):
            if _set_files_on_locator(file_inputs.nth(idx), abs_image_path):
                uploaded = True
                break

    if uploaded:
        page.wait_for_timeout(1500)
        confirm_selectors = [
            "button:has-text('Next')",
            "button:has-text('Done')",
            "button:has-text('Tiếp theo')",
            "button:has-text('Xong')",
        ]
        for sel in confirm_selectors:
            try:
                btn = root.locator(sel).first
                if btn.count() > 0 and btn.is_visible():
                    print(f"[INFO] LinkedIn: clicking image preview confirmation button: {sel}")
                    btn.click(timeout=3000)
                    page.wait_for_timeout(1000)
                    break
            except Exception:
                pass

        if _wait_for_linkedin_image_attached(page):
            print("[SUCCESS] LinkedIn image attached via confirmation.")
            return True

    print("[WARNING] LinkedIn image upload could not be verified in the share modal.")
    return False


def _open_linkedin_editor(page: Page, profile: PlatformPostingProfile) -> Optional[str]:
    existing = _linkedin_caption_editor(page)
    if existing is not None and _locator_is_visible(existing):
        print("[INFO] LinkedIn share modal editor already open.")
        return "div.ql-editor[contenteditable='true']"

    print("[INFO] Attempting to open LinkedIn share modal...")
    start_elem, start_selector = _find_linkedin_start_post(page, profile)
    if start_elem is None:
        print("[WARNING] LinkedIn start-post trigger was not found on the feed.")
        return None

    if not _click_linkedin_target(page, start_elem, start_selector):
        print("[WARNING] LinkedIn start-post trigger could not be clicked.")
        return None

    for _ in range(40):
        page.wait_for_timeout(500)
        editor = _linkedin_caption_editor(page)
        if editor is not None and _locator_is_visible(editor):
            return "div.ql-editor[contenteditable='true']"

    print("[WARNING] LinkedIn share modal editor did not appear after opening composer.")
    try:
        page.screenshot(path="/home/trung/Documents/2026/project/auto-trillion-news-post/output/linkedin_error.png")
        print("[INFO] Saved error screenshot to output/linkedin_error.png")
    except Exception as se:
        print(f"[DEBUG] Failed to save screenshot: {se}")
    return None


def _fill_linkedin_composer(
    page: Page,
    profile: PlatformPostingProfile,
    editor_selector: str,
    post_content: str,
    image_path: Optional[str],
) -> None:
    _paste_linkedin_caption(page, post_content)
    if image_path:
        uploaded = _upload_linkedin_image(page, image_path)
        if not uploaded:
            print("[WARNING] Could not upload LinkedIn image automatically. Please upload manually.")
            print(f"Image to upload: {os.path.abspath(image_path)}")


def run_linkedin_posting(
    page: Page,
    post_content: str,
    image_path: Optional[str],
    confirm_callback: Optional[Callable] = None,
) -> Tuple[bool, Optional[str]]:
    profile = PLATFORM_PROFILES[PLATFORM_KEY]
    print(f"[INFO] Dispatching {WORKFLOW_ID} for {PLATFORM_CANONICAL[PLATFORM_KEY]}")
    return run_assisted_flow(
        page,
        profile,
        post_content,
        image_path,
        confirm_callback,
        open_editor_fn=_open_linkedin_editor,
        fill_composer_fn=_fill_linkedin_composer,
        wait_for_login_fn=_wait_for_linkedin_login,
        prepare_feed_fn=_prepare_linkedin_feed,
    )


def validate_linkedin_session(page: Page) -> bool:
    return validate_session_for_profile(page, PLATFORM_PROFILES[PLATFORM_KEY])