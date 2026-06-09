import os
import time
from dataclasses import dataclass
from typing import Callable, List, Optional, Tuple

from src.config import AppConfig
from src.models import NewsItem
from src.platform_capabilities import (
    get_platform_mvp_mode,
    is_best_effort_posting,
    is_posting_supported,
    platform_requires_image,
    resolve_local_image_path,
)
from src.posting_core import canonicalize_platform, PLATFORM_CANONICAL

try:
    from playwright.sync_api import Page
except ImportError:
    Page = object  # type: ignore


@dataclass(frozen=True)
class PlatformPostingProfile:
    key: str
    feed_url: str
    start_post_selectors: List[str]
    editor_selectors: List[str]
    media_button_selectors: List[str]
    logged_in_url_markers: List[str]
    logged_out_selectors: List[str]


PLATFORM_PROFILES = {
    "linkedin": PlatformPostingProfile(
        key="linkedin",
        feed_url="https://www.linkedin.com/feed/",
        start_post_selectors=[
            "button.share-box-feed-entry__trigger",
            "span.share-box-feed-entry__trigger-span",
            "button:has-text('Start a post')",
            "button:has-text('Đăng bài viết')",
            "button:has-text('Viết bài')",
            "div.share-box-feed-entry__trigger",
            "button[aria-haspopup='dialog']",
        ],
        editor_selectors=[
            "div.share-create-post__modal div.ql-editor[contenteditable='true']",
            "div.artdeco-modal div.ql-editor[contenteditable='true']",
            "div[role='dialog'] div.ql-editor[contenteditable='true']",
            "div.ql-editor[role='textbox']",
            "div.ql-editor[contenteditable='true']",
            "div[role='textbox'][aria-label*='editor']",
            "div[role='textbox'][aria-label*='post']",
        ],
        media_button_selectors=[
            "button[aria-label='Add media']",
            "button[aria-label='Add a photo']",
            "button[aria-label='Thêm phương tiện']",
            "button.share-promoted-detour-button",
            "button[aria-label*='photo']",
            "button[aria-label*='Media']",
            "button[aria-label*='Ảnh']",
            "button:has-text('Media')",
            "input[type='file'][accept*='image']",
        ],
        logged_in_url_markers=["feed"],
        logged_out_selectors=["input#username"],
    ),
    "facebook": PlatformPostingProfile(
        key="facebook",
        feed_url="https://www.facebook.com/",
        start_post_selectors=[
            "div[role='button']:has-text('on your mind')",
            "span:has-text('on your mind')",
            "div[aria-label='Create a post']",
            "div[aria-label='Tạo bài viết']",
            "div[role='button'][tabindex='0']",
        ],
        editor_selectors=[
            "div[role='textbox'][contenteditable='true']",
            "div[data-lexical-editor='true']",
            "div[contenteditable='true'][role='textbox']",
            "div[contenteditable='true']",
        ],
        media_button_selectors=[
            "div[aria-label='Photo/video']",
            "div[aria-label='Ảnh/video']",
            "div[aria-label='Add photos']",
            "div[aria-label='Thêm ảnh']",
            "div[aria-label='Photo/video'][role='button']",
            "div[aria-label='Ảnh/video'][role='button']",
            "span:has-text('Photo/video')",
            "span:has-text('Ảnh/video')",
        ],
        logged_in_url_markers=["facebook.com"],
        logged_out_selectors=["input[name='email']", "input#email"],
    ),
    "x": PlatformPostingProfile(
        key="x",
        feed_url="https://x.com/compose/tweet",
        start_post_selectors=[
            "div[data-testid='tweetTextarea_0']",
            "a[href='/compose/tweet']",
            "a[data-testid='SideNav_NewTweet_Button']",
        ],
        editor_selectors=[
            "div[data-testid='tweetTextarea_0']",
            "div[role='textbox'][data-testid='tweetTextarea_0']",
            "div[contenteditable='true'][role='textbox']",
            "div[contenteditable='true']",
        ],
        media_button_selectors=[
            "input[type='file'][accept*='image']",
            "button[data-testid='attachments']",
            "div[data-testid='toolBar'] input[type='file']",
        ],
        logged_in_url_markers=["x.com", "twitter.com"],
        logged_out_selectors=["[data-testid='loginButton']", "input[autocomplete='username']"],
    ),
    "instagram": PlatformPostingProfile(
        key="instagram",
        feed_url="https://www.instagram.com/",
        start_post_selectors=[
            "svg[aria-label='New post']",
            "a[href='#create']",
            "div[role='menuitem']:has-text('Post')",
            "span:has-text('Create')",
        ],
        editor_selectors=[
            "textarea[aria-label*='caption']",
            "textarea[aria-label*='Write a caption']",
            "div[contenteditable='true'][role='textbox']",
            "div[contenteditable='true']",
        ],
        media_button_selectors=[
            "input[type='file'][accept*='image']",
            "button:has-text('Select from computer')",
            "button:has-text('Select from Computer')",
        ],
        logged_in_url_markers=["instagram.com"],
        logged_out_selectors=["input[name='username']", "input[aria-label='Phone number, username, or email']"],
    ),
    "pinterest": PlatformPostingProfile(
        key="pinterest",
        feed_url="https://www.pinterest.com/",
        start_post_selectors=[
            "div[data-test-id='create-button']",
            "button:has-text('Create')",
            "a[aria-label='Create']",
            "div[role='button']:has-text('Create')",
        ],
        editor_selectors=[
            "div[contenteditable='true']",
            "textarea",
            "input[placeholder*='description']",
        ],
        media_button_selectors=[
            "input[type='file'][accept*='image']",
            "button:has-text('Upload')",
            "button:has-text('Save from device')",
        ],
        logged_in_url_markers=["pinterest.com"],
        logged_out_selectors=["input[name='id']", "input[type='email']"],
    ),
    "threads": PlatformPostingProfile(
        key="threads",
        feed_url="https://www.threads.net/",
        start_post_selectors=[
            "div[role='button']:has-text('Post')",
            "svg[aria-label='Create']",
            "a[href='/compose']",
            "div:has-text('New thread')",
        ],
        editor_selectors=[
            "div[contenteditable='true'][role='textbox']",
            "div[contenteditable='true']",
            "textarea",
        ],
        media_button_selectors=[
            "input[type='file'][accept*='image']",
            "svg[aria-label='Attach media']",
            "button[aria-label*='media']",
        ],
        logged_in_url_markers=["threads.net"],
        logged_out_selectors=["input[name='username']", "input[autocomplete='username']"],
    ),
    "tiktok": PlatformPostingProfile(
        key="tiktok",
        feed_url="https://www.tiktok.com/upload",
        start_post_selectors=[
            "button:has-text('Select video')",
            "button:has-text('Select files')",
            "div:has-text('Upload')",
            "a[href*='/upload']",
            "button:has-text('Create')",
        ],
        editor_selectors=[
            "div[contenteditable='true']",
            "textarea",
            "div.public-DraftEditor-content",
            "div[role='textbox']",
        ],
        media_button_selectors=[
            "input[type='file'][accept*='image']",
            "input[type='file']",
            "button:has-text('Upload')",
            "button:has-text('Select files')",
        ],
        logged_in_url_markers=["tiktok.com"],
        logged_out_selectors=["input[name='username']", "a[href*='/login']"],
    ),
    "youtube": PlatformPostingProfile(
        key="youtube",
        feed_url="https://www.youtube.com/",
        start_post_selectors=[
            "button:has-text('Create')",
            "ytcp-button:has-text('Create')",
            "a[href*='post']",
            "tp-yt-paper-button:has-text('Create')",
            "button[aria-label='Create']",
        ],
        editor_selectors=[
            "div#contenteditable-root",
            "div[contenteditable='true']",
            "textarea",
            "div[role='textbox']",
        ],
        media_button_selectors=[
            "input[type='file'][accept*='image']",
            "input[type='file']",
            "button:has-text('Image')",
            "button[aria-label*='image']",
        ],
        logged_in_url_markers=["youtube.com"],
        logged_out_selectors=["input[type='email']", "a[href*='ServiceLogin']"],
    ),
}


def _first_visible(page: Page, selectors: List[str]):
    for selector in selectors:
        try:
            elem = page.query_selector(selector)
            if elem and elem.is_visible():
                return elem, selector
        except Exception:
            pass
    return None, None


def _wait_for_login(page: Page, profile: PlatformPostingProfile, timeout_attempts: int = 60) -> bool:
    print(f"[INFO] Checking login status for {PLATFORM_CANONICAL[profile.key]}...")
    for _ in range(timeout_attempts):
        elem, _ = _first_visible(page, profile.start_post_selectors)
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


def _open_editor(page: Page, profile: PlatformPostingProfile) -> Optional[str]:
    if profile.key == "linkedin":
        return _open_linkedin_editor(page)

    editor, selector = _first_visible(page, profile.editor_selectors)
    if editor:
        print(f"[INFO] Editor already open: {selector}")
        return selector

    print("[INFO] Attempting to open post composer...")
    start_elem, start_selector = _first_visible(page, profile.start_post_selectors)
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
        editor, selector = _first_visible(page, profile.editor_selectors)
        if editor:
            return selector
    return None


def _open_linkedin_editor(page: Page) -> Optional[str]:
    existing = _linkedin_caption_editor(page)
    if existing is not None and existing.count() > 0:
        print("[INFO] LinkedIn share modal editor already open.")
        return "div.ql-editor[contenteditable='true']"

    print("[INFO] Attempting to open LinkedIn share modal...")
    start_elem, start_selector = _first_visible(
        page, PLATFORM_PROFILES["linkedin"].start_post_selectors
    )
    if not start_elem:
        return None

    print(f"[INFO] Clicking LinkedIn start post element: {start_selector}")
    try:
        start_elem.click(timeout=3000)
    except Exception:
        try:
            start_elem.click(force=True, timeout=3000)
        except Exception:
            page.evaluate("el => el.click()", start_elem)

    for _ in range(20):
        page.wait_for_timeout(500)
        editor = _linkedin_caption_editor(page)
        if editor is not None and editor.count() > 0:
            return "div.ql-editor[contenteditable='true']"
    return None


def _composer_scope(page: Page, profile: PlatformPostingProfile):
    if profile.key == "facebook":
        dialog = page.query_selector("div[role='dialog']")
        if dialog:
            return dialog
    if profile.key == "linkedin":
        for sel in (
            "div.share-create-post__modal",
            "div.artdeco-modal",
            "div[role='dialog']",
        ):
            dialog = page.query_selector(sel)
            if dialog:
                return dialog
    return page


def _linkedin_share_modal(page: Page):
    modal_selectors = [
        "div.share-create-post__modal",
        "div.artdeco-modal",
        "div[role='dialog']",
    ]
    for sel in modal_selectors:
        loc = page.locator(sel)
        for idx in range(loc.count()):
            candidate = loc.nth(idx)
            try:
                if candidate.locator(".ql-editor, div.ql-editor").count() > 0:
                    return candidate
            except Exception:
                continue
    return page.locator("div[role='dialog']").last


def _linkedin_caption_editor(page: Page):
    modal = _linkedin_share_modal(page)
    editor_selectors = [
        "div.ql-editor[contenteditable='true']",
        "div.ql-editor[role='textbox']",
        "div.ql-editor",
        "div[role='textbox'][contenteditable='true']",
    ]
    for sel in editor_selectors:
        editor = modal.locator(sel).first
        if editor.count() > 0:
            return editor
    return None


def _insert_linkedin_caption_via_js(page: Page, post_content: str) -> bool:
    try:
        return bool(
            page.evaluate(
                """
                (text) => {
                    const roots = [
                        document.querySelector(".share-create-post__modal"),
                        document.querySelector("div.artdeco-modal"),
                        ...Array.from(document.querySelectorAll("div[role='dialog']")),
                    ].filter(Boolean);
                    const searchRoots = roots.length ? roots : [document.body];

                    for (const root of searchRoots) {
                        const editor = root.querySelector(
                            ".ql-editor[contenteditable='true'], .ql-editor"
                        );
                        if (!editor) continue;

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
                    return false;
                }
                """,
                post_content,
            )
        )
    except Exception as e:
        print(f"[DEBUG] LinkedIn JS caption insert failed: {e}")
        return False


def _paste_linkedin_caption(page: Page, post_content: str) -> None:
    page.wait_for_timeout(800)
    print("[INFO] Pasting LinkedIn caption into Quill editor...")

    if _insert_linkedin_caption_via_js(page, post_content):
        page.wait_for_timeout(800)
        return

    editor = _linkedin_caption_editor(page)
    if editor is not None:
        try:
            editor.click(force=True, timeout=10000)
        except Exception as click_error:
            print(f"[DEBUG] LinkedIn editor click failed, trying focus: {click_error}")
            editor.focus(timeout=10000)
        page.wait_for_timeout(400)
        page.keyboard.insert_text(post_content)
        page.wait_for_timeout(800)
        return

    raise RuntimeError("LinkedIn caption editor was not found in the share modal.")


def _wait_for_linkedin_image_attached(page: Page, timeout_ms: int = 20000) -> bool:
    modal = _linkedin_share_modal(page)
    deadline = time.time() + (timeout_ms / 1000)
    while time.time() < deadline:
        try:
            if modal.locator("img[src*='blob:']").count() > 0:
                return True
            if modal.locator("img.share-create-post__image").count() > 0:
                return True
            if modal.locator("button[aria-label*='Remove']").count() > 0:
                return True
            if modal.locator("button[aria-label*='Xóa']").count() > 0:
                return True
        except Exception:
            pass
        page.wait_for_timeout(500)
    return False


def _upload_linkedin_image(page: Page, image_path: str) -> bool:
    abs_image_path = os.path.abspath(image_path)
    if not os.path.isfile(abs_image_path):
        print(f"[ERROR] LinkedIn image file does not exist: {abs_image_path}")
        return False

    print(f"[INFO] LinkedIn: uploading image from {abs_image_path}")
    modal = _linkedin_share_modal(page)
    try:
        modal.wait_for(state="visible", timeout=10000)
    except Exception as e:
        print(f"[WARNING] LinkedIn share modal not visible: {e}")
        return False

    page.wait_for_timeout(600)
    profile = PLATFORM_PROFILES["linkedin"]

    for btn_sel in profile.media_button_selectors:
        try:
            btn = modal.locator(btn_sel).first
            if btn.count() == 0:
                continue
            if btn_sel.startswith("input[type='file']"):
                btn.set_input_files(abs_image_path, timeout=5000)
                if _wait_for_linkedin_image_attached(page):
                    print("[SUCCESS] LinkedIn image attached via file input.")
                    return True
                continue
            btn.wait_for(state="visible", timeout=2000)
            with page.expect_file_chooser(timeout=10000) as fc_info:
                btn.click(force=True, timeout=3000)
            fc_info.value.set_files(abs_image_path)
            if _wait_for_linkedin_image_attached(page):
                print("[SUCCESS] LinkedIn image attached via media button.")
                return True
        except Exception as e:
            print(f"[DEBUG] LinkedIn media button '{btn_sel}' failed: {e}")

    file_inputs = modal.locator("input[type='file']")
    for idx in range(file_inputs.count()):
        if _set_files_on_locator(file_inputs.nth(idx), abs_image_path):
            if _wait_for_linkedin_image_attached(page):
                print(f"[SUCCESS] LinkedIn image attached via modal file input #{idx}.")
                return True

    print("[WARNING] LinkedIn image upload could not be verified in the share modal.")
    return False


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


def _upload_image(
    page: Page,
    profile: PlatformPostingProfile,
    image_path: str,
    scope=None,
) -> bool:
    if profile.key == "linkedin":
        return _upload_linkedin_image(page, image_path)
    if profile.key == "facebook":
        return _upload_facebook_image(page, image_path)

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


def _find_visible_editor(page: Page, profile: PlatformPostingProfile, scope=None):
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
    """Return the main Facebook caption editor, not link-preview textboxes."""
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


def _paste_post_content(
    page: Page,
    profile: PlatformPostingProfile,
    editor_selector: str,
    post_content: str,
    scope=None,
) -> None:
    print("[INFO] Pasting post content into editor...")
    if profile.key == "facebook":
        _paste_facebook_caption(page, post_content)
        return
    if profile.key == "linkedin":
        _paste_linkedin_caption(page, post_content)
        return

    editor, resolved_selector = _find_visible_editor(page, profile, scope=scope)
    target_selector = resolved_selector or editor_selector

    page.click(target_selector)
    page.fill(target_selector, post_content)
    page.keyboard.press("End")
    page.wait_for_timeout(500)


def _fill_composer_content(
    page: Page,
    profile: PlatformPostingProfile,
    editor_selector: str,
    post_content: str,
    image_path: Optional[str],
) -> None:
    scope = _composer_scope(page, profile)

    if profile.key == "linkedin":
        _paste_linkedin_caption(page, post_content)
        if image_path:
            uploaded = _upload_linkedin_image(page, image_path)
            if not uploaded:
                print("[WARNING] Could not upload LinkedIn image automatically. Please upload manually.")
                print(f"Image to upload: {os.path.abspath(image_path)}")
        return

    if profile.key == "facebook" and image_path:
        print("[INFO] Facebook: attaching image before caption so both stay in one post...")
        uploaded = _upload_facebook_image(page, image_path)
        if uploaded:
            page.wait_for_timeout(1500)
            scope = _composer_scope(page, profile)
        else:
            print("[WARNING] Pre-caption image upload failed. Trying caption-first fallback...")
            _paste_post_content(page, profile, editor_selector, post_content, scope=scope)
            uploaded = _upload_facebook_image(page, image_path)
            if uploaded:
                page.wait_for_timeout(1500)
                return
            print("[WARNING] Could not upload image automatically. Please upload it manually.")
            print(f"Image to upload: {os.path.abspath(image_path)}")
            return

        _paste_post_content(page, profile, editor_selector, post_content, scope=scope)
        return

    _paste_post_content(page, profile, editor_selector, post_content, scope=scope)

    if image_path:
        uploaded = _upload_image(page, profile, image_path, scope=scope)
        if not uploaded:
            print("[WARNING] Could not upload image automatically. Please upload it manually.")
            print(f"Image to upload: {image_path}")
    elif platform_requires_image(profile.key):
        print(
            f"[WARNING] {PLATFORM_CANONICAL[profile.key]} expects media, but no image path was resolved."
        )


def _run_profile_flow(
    page: Page,
    profile: PlatformPostingProfile,
    post_content: str,
    image_path: Optional[str],
    confirm_callback: Optional[Callable],
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
    page.goto(profile.feed_url, timeout=45000)

    if not _wait_for_login(page, profile):
        print(f"\n[ERROR] Login timeout for {PLATFORM_CANONICAL[profile.key]}.")
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

    print(f"\n[SUCCESS] Logged in to {PLATFORM_CANONICAL[profile.key]}!")
    editor_selector = _open_editor(page, profile)
    if not editor_selector:
        raise RuntimeError(
            f"{PLATFORM_CANONICAL[profile.key]} post composer editor was not found."
        )

    _fill_composer_content(page, profile, editor_selector, post_content, image_path)

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


def validate_platform_session(page: Page, platform_key: str) -> bool:
    profile = PLATFORM_PROFILES.get(platform_key)
    if not profile:
        return False
    page.goto(profile.feed_url, timeout=15000)
    if _first_visible(page, profile.start_post_selectors)[0]:
        return True
    try:
        if any(marker in page.url for marker in profile.logged_in_url_markers):
            if not any(page.query_selector(sel) for sel in profile.logged_out_selectors):
                return True
    except Exception:
        pass
    return False


def run_platform_assisted_posting(
    item: NewsItem,
    config: AppConfig,
    post_content: str,
    image_path: Optional[str],
    confirm_callback: Optional[Callable] = None,
) -> bool:
    from playwright.sync_api import sync_playwright

    platform_name = item.platform or "linkedin"
    try:
        platform_key = canonicalize_platform(platform_name)
    except ValueError as e:
        print(f"[ERROR] {e}")
        return False

    if not is_posting_supported(platform_key):
        print(
            f"[ERROR] Assisted posting for '{PLATFORM_CANONICAL[platform_key]}' "
            "is not supported in the current release slice."
        )
        return False

    profile = PLATFORM_PROFILES[platform_key]
    browser_context_dir = os.path.abspath(
        os.path.join(config.output_dir, ".browser_context")
    )
    print(f"[INFO] Using persistent browser context: {browser_context_dir}")
    print("[INFO] Launching Chromium in non-headless mode...")

    launch_kwargs = {
        "user_data_dir": browser_context_dir,
        "headless": False,
        "user_agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "viewport": {"width": 1280, "height": 800},
        "args": ["--disable-extensions"],
        "locale": "en-US",
    }
    if getattr(config, "playwright_chromium_executable_path", None):
        launch_kwargs["executable_path"] = config.playwright_chromium_executable_path

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(**launch_kwargs)
        page = context.new_page() if not context.pages else context.pages[0]
        try:
            success, post_url = _run_profile_flow(
                page, profile, post_content, image_path, confirm_callback
            )
            if success:
                item.post_url = post_url or ""
            return success
        except Exception as e:
            print(f"\n[ERROR] Assisted posting failed: {e}")
            print("[INFO] Fallback: Copy and paste the post content below manually:")
            print("=" * 60)
            print(post_content)
            print("=" * 60)
            if image_path:
                print(f"Image Path: {image_path}")
            if confirm_callback:
                confirm_callback()
            else:
                input("Press Enter to close browser and return...")
            return False
        finally:
            context.close()


def prepare_posting_assets(
    item: NewsItem,
    config: AppConfig,
    post_content: str,
    workbook_path: Optional[str] = None,
) -> Tuple[Optional[str], Optional[str]]:
    """
    Validate posting support and resolve image path.
    Returns (image_path, error_message).
    """
    platform_name = item.platform or "linkedin"
    try:
        platform_key = canonicalize_platform(platform_name)
    except ValueError as e:
        return None, str(e)

    if not is_posting_supported(platform_key):
        return None, (
            f"Assisted posting for '{PLATFORM_CANONICAL[platform_key]}' "
            "is not supported in the current release slice."
        )

    if platform_requires_image(platform_key):
        image_path = resolve_local_image_path(item.image_file, config, workbook_path)
        if not image_path:
            return None, (
                f"Platform '{PLATFORM_CANONICAL[platform_key]}' requires a local image file, "
                "but none was found for this row."
            )
    else:
        image_path = resolve_local_image_path(item.image_file, config, workbook_path)

    if not post_content:
        return None, f"Empty post content for ID {item.id}."
    return image_path, None