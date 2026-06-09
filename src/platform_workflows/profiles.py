from dataclasses import dataclass
from typing import List


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
            "button[aria-label*='Start a post']",
            "button[aria-label*='Bắt đầu']",
            "div[role='button'] div[aria-label*='Bắt đầu']",
            "div[role='button'] div[aria-label*='Start a post']",
            "[aria-label*='Bắt đầu bài đăng']",
            "[aria-label*='Start a post']",
            "div[role='button']:has-text('Bắt đầu bài đăng')",
            "div[role='button']:has-text('Start a post')",
            "div.share-box-feed-entry__closed-share-box",
            "div.share-box-feed-entry__top-bar button",
            "[data-view-name*='share'] button",
            "div.share-box-feed-entry",
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
            "button[aria-label='Thêm phương tiện truyền thông']",
            "button[aria-label*='phương tiện']",
            "button[aria-label*='truyền thông']",
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