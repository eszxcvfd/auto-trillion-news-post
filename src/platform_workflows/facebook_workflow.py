"""Facebook-owned posting workflow. Selector and composer logic stays isolated here."""

import os
import time
from typing import Callable, Optional, Tuple

from src.platform_workflows.browser_common import (
    open_editor,
    paste_post_content_generic,
    run_assisted_flow,
    validate_session_for_profile,
)
from src.platform_workflows.profiles import PLATFORM_PROFILES, PlatformPostingProfile
from src.posting_core import PLATFORM_CANONICAL

try:
    from playwright.sync_api import Page
except ImportError:
    Page = object  # type: ignore

WORKFLOW_ID = "workflow.facebook.v1"
PLATFORM_KEY = "facebook"


def _facebook_composer_dialog(page: Page):
    return page.locator("div[role='dialog']").last


def _wait_for_facebook_image_attached(page: Page, timeout_ms: int = 20000) -> bool:
    dialog = _facebook_composer_dialog(page)
    deadline = time.time() + (timeout_ms / 1000)
    while time.time() < deadline:
        try:
            if dialog.locator("img[src*='blob:']").count() > 0:
                return True
            if dialog.locator("img[src*='scontent']").count() > 0:
                return True
            if page.locator("[aria-label*='Remove']").count() > 0:
                return True
            if page.locator("[aria-label*='Xóa']").count() > 0:
                return True
            if dialog.locator("[aria-label*='Edit']").count() > 0:
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


def _upload_facebook_image(page: Page, image_path: str) -> bool:
    abs_image_path = os.path.abspath(image_path)
    if not os.path.isfile(abs_image_path):
        print(f"[ERROR] Facebook image file does not exist: {abs_image_path}")
        return False

    print(f"[INFO] Facebook: uploading image from {abs_image_path}")
    dialog = _facebook_composer_dialog(page)
    try:
        dialog.wait_for(state="visible", timeout=10000)
    except Exception as e:
        print(f"[WARNING] Facebook composer dialog not visible: {e}")
        return False

    page.wait_for_timeout(800)

    for btn_sel in PLATFORM_PROFILES["facebook"].media_button_selectors:
        try:
            btn = dialog.locator(btn_sel).first
            if btn.count() == 0:
                continue
            btn.wait_for(state="visible", timeout=2000)
            with page.expect_file_chooser(timeout=10000) as fc_info:
                btn.click(force=True, timeout=3000)
            fc_info.value.set_files(abs_image_path)
            if _wait_for_facebook_image_attached(page):
                print("[SUCCESS] Facebook image attached via photo/video button.")
                return True
        except Exception as e:
            print(f"[DEBUG] Facebook photo button '{btn_sel}' failed: {e}")

    file_input = dialog.locator("input[type='file']")
    for idx in range(file_input.count()):
        if _set_files_on_locator(file_input.nth(idx), abs_image_path):
            if _wait_for_facebook_image_attached(page):
                print(f"[SUCCESS] Facebook image attached via dialog file input #{idx}.")
                return True

    page_inputs = page.locator("input[type='file']")
    for idx in range(page_inputs.count()):
        if _set_files_on_locator(page_inputs.nth(idx), abs_image_path):
            if _wait_for_facebook_image_attached(page):
                print(f"[SUCCESS] Facebook image attached via page file input #{idx}.")
                return True

    print("[WARNING] Facebook image upload could not be verified in the composer.")
    return False


def _facebook_dialog_locators(page: Page):
    roots = [
        page.locator("div[role='dialog']").filter(
            has=page.locator(
                "span:has-text('Create post'), span:has-text('Tạo bài viết'), "
                "div[aria-label='Create post'], div[aria-label='Tạo bài viết']"
            )
        ),
        page.locator("div[role='dialog']"),
    ]
    seen = set()
    for root in roots:
        count = root.count()
        for idx in range(count):
            candidate = root.nth(idx)
            try:
                handle_id = candidate.evaluate("el => el.outerHTML.slice(0, 120)")
            except Exception:
                handle_id = f"{count}-{idx}"
            if handle_id in seen:
                continue
            seen.add(handle_id)
            yield candidate


def _facebook_caption_editor(page: Page):
    editor_selectors = [
        "div[data-lexical-editor='true'][contenteditable='true'][role='textbox']",
        "div[role='textbox'][contenteditable='true']",
    ]
    preferred_tokens = ("mind", "nghĩ", "bài viết", "điều gì", "what's on")

    for dialog in _facebook_dialog_locators(page):
        for editor_sel in editor_selectors:
            candidates = dialog.locator(editor_sel)
            matched = []
            for idx in range(candidates.count()):
                editor = candidates.nth(idx)
                try:
                    placeholder = (editor.get_attribute("aria-placeholder") or "").lower()
                except Exception:
                    placeholder = ""
                matched.append((editor, placeholder))

            for editor, placeholder in matched:
                if any(token in placeholder for token in preferred_tokens):
                    return editor

            if matched:
                return matched[-1][0]

    for editor_sel in editor_selectors:
        candidates = page.locator(editor_sel)
        matched = []
        for idx in range(candidates.count()):
            editor = candidates.nth(idx)
            try:
                placeholder = (editor.get_attribute("aria-placeholder") or "").lower()
            except Exception:
                placeholder = ""
            matched.append((editor, placeholder))

        for editor, placeholder in matched:
            if any(token in placeholder for token in preferred_tokens):
                return editor

        if matched:
            return matched[-1][0]

    return None


def _insert_facebook_caption_via_js(page: Page, post_content: str) -> bool:
    try:
        return bool(
            page.evaluate(
                """
                (text) => {
                    const dialogs = Array.from(document.querySelectorAll("div[role='dialog']"));
                    const roots = dialogs.length ? dialogs : [document.body];
                    const preferred = /mind|nghĩ|điều gì|bài viết/i;

                    for (const root of roots) {
                        const editors = Array.from(
                            root.querySelectorAll(
                                "div[role='textbox'][contenteditable='true'], div[data-lexical-editor='true']"
                            )
                        );
                        if (!editors.length) continue;

                        let target = editors.find((el) =>
                            preferred.test(el.getAttribute("aria-placeholder") || "")
                        );
                        if (!target) target = editors[editors.length - 1];

                        target.focus();
                        target.click();

                        const selection = window.getSelection();
                        const range = document.createRange();
                        range.selectNodeContents(target);
                        range.collapse(false);
                        selection.removeAllRanges();
                        selection.addRange(range);

                        let inserted = false;
                        if (document.queryCommandSupported("insertText")) {
                            inserted = document.execCommand("insertText", false, text);
                        }
                        if (!inserted) {
                            try {
                                const data = new DataTransfer();
                                data.setData("text/plain", text);
                                const pasteEvent = new ClipboardEvent("paste", {
                                    clipboardData: data,
                                    bubbles: true,
                                    cancelable: true,
                                });
                                inserted = target.dispatchEvent(pasteEvent);
                            } catch (err) {
                                inserted = false;
                            }
                        }
                        if (!inserted) {
                            const paragraph = target.querySelector("p[dir='auto']") || target;
                            paragraph.textContent = text;
                        }
                        target.dispatchEvent(
                            new InputEvent("input", {
                                bubbles: true,
                                cancelable: true,
                                inputType: "insertText",
                                data: text,
                            })
                        );
                        return (target.innerText || target.textContent || "").trim().length > 0;
                    }
                    return false;
                }
                """,
                post_content,
            )
        )
    except Exception as e:
        print(f"[DEBUG] Facebook JS caption insert failed: {e}")
        return False


def _paste_facebook_caption(page: Page, post_content: str) -> None:
    page.wait_for_timeout(1200)
    print("[INFO] Pasting Facebook caption into Lexical editor...")

    if _insert_facebook_caption_via_js(page, post_content):
        page.wait_for_timeout(800)
        return

    for snippet in ("What's on your mind", "on your mind", "Bạn đang nghĩ", "Tạo bài viết"):
        try:
            placeholder = page.get_by_text(snippet, exact=False).first
            if placeholder.count() > 0:
                placeholder.click(force=True, timeout=5000)
                page.wait_for_timeout(300)
                page.keyboard.insert_text(post_content)
                page.wait_for_timeout(800)
                return
        except Exception as e:
            print(f"[DEBUG] Facebook placeholder click '{snippet}' failed: {e}")

    editor = _facebook_caption_editor(page)
    if editor is not None:
        try:
            editor.focus(timeout=10000)
        except Exception as focus_error:
            print(f"[DEBUG] Facebook editor focus failed, retrying with force click: {focus_error}")
            editor.click(force=True, timeout=10000)
        page.wait_for_timeout(400)
        page.keyboard.insert_text(post_content)
        page.wait_for_timeout(800)
        return

    raise RuntimeError("Facebook caption editor was not found in the composer dialog.")


def _composer_scope(page: Page, profile: PlatformPostingProfile):
    dialog = page.query_selector("div[role='dialog']")
    if dialog:
        return dialog
    return page


def _fill_facebook_composer(
    page: Page,
    profile: PlatformPostingProfile,
    editor_selector: str,
    post_content: str,
    image_path: Optional[str],
) -> None:
    scope = _composer_scope(page, profile)

    if image_path:
        print("[INFO] Facebook: attaching image before caption so both stay in one post...")
        uploaded = _upload_facebook_image(page, image_path)
        if uploaded:
            page.wait_for_timeout(1500)
            scope = _composer_scope(page, profile)
        else:
            print("[WARNING] Pre-caption image upload failed. Trying caption-first fallback...")
            _paste_facebook_caption(page, post_content)
            uploaded = _upload_facebook_image(page, image_path)
            if uploaded:
                page.wait_for_timeout(1500)
                return
            print("[WARNING] Could not upload image automatically. Please upload it manually.")
            print(f"Image to upload: {os.path.abspath(image_path)}")
            return

        _paste_facebook_caption(page, post_content)
        return

    paste_post_content_generic(page, profile, editor_selector, post_content, scope=scope)


def run_facebook_posting(
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
        open_editor_fn=open_editor,
        fill_composer_fn=_fill_facebook_composer,
    )


def validate_facebook_session(page: Page) -> bool:
    return validate_session_for_profile(page, PLATFORM_PROFILES[PLATFORM_KEY])