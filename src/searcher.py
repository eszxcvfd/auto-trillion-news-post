import os
import urllib.parse
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None
from src.models import NewsItem
from src.config import AppConfig

def is_captcha_present(page) -> bool:
    # Check for common captcha indicators
    captcha_selectors = [
        "iframe[src*='captcha']",
        "div#captcha-container",
        "form[action*='captcha']",
        "div.g-recaptcha",
        "iframe[src*='recaptcha']",
        "div#challenge-stage" # Cloudflare challenge
    ]
    for selector in captcha_selectors:
        try:
            if page.query_selector(selector):
                return True
        except Exception:
            pass
    # Also check if title or heading mentions captcha or verification
    try:
        title = page.title().lower()
        if "captcha" in title or "robot" in title or "verification" in title:
            return True
    except Exception:
        pass
    return False

def hide_cookie_banners(page) -> None:
    try:
        page.evaluate("""() => {
            const style = document.createElement('style');
            style.innerHTML = `
                #bnp_cookie_banner,
                #ad-cookie-banner,
                #cookie-banner,
                .cookie-banner,
                .cookie-consent,
                #cookie-consent,
                div[class*="cookie-banner"],
                div[id*="cookie-banner"],
                div[class*="cookie_banner"],
                div[id*="cookie_banner"],
                div[class*="consent"],
                div[id*="consent"],
                #bnp_container,
                .bnp_container,
                #onetrust-banner-sdk,
                .onetrust-pc-dark-filter,
                #privacy-consent,
                .privacy-consent {
                    display: none !important;
                    visibility: hidden !important;
                    opacity: 0 !important;
                    pointer-events: none !important;
                }
            `;
            document.head.appendChild(style);
        }""")
    except Exception as e:
        print(f"[WARNING] Failed to inject hide cookie banner styles: {e}")

def search_news(keyword: str, config: AppConfig) -> list[NewsItem]:
    results = []

    if sync_playwright is None:
        print("[ERROR] Playwright is not installed. Please run pip install -r requirements.txt to install it.")
        return []

    encoded_keyword = urllib.parse.quote_plus(keyword)
    provider = config.search_provider.lower().strip()
    use_google = "google" in provider

    if use_google:
        url = f"https://www.google.com/search?q={encoded_keyword}&tbm=nws"
    else:
        url = f"https://www.bing.com/news/search?q={encoded_keyword}"

    print(f"[INFO] Searching {config.search_provider} for keyword: '{keyword}'")

    launch_kwargs = {
        "headless": config.headless,
        "args": ["--disable-extensions"]
    }
    if getattr(config, "playwright_chromium_executable_path", None):
        launch_kwargs["executable_path"] = config.playwright_chromium_executable_path

    with sync_playwright() as p:
        browser = p.chromium.launch(**launch_kwargs)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800},
            locale="en-US",
        )
        page = context.new_page()

        # Block known third-party tracking/ad domains to prevent console errors
        try:
            blocked_domains = [
                "ns1p.net", "doubleclick.net", "google-analytics.com", 
                "sentry.io", "adnxs.com", "rubiconproject.com", 
                "pubmatic.com", "casalemedia.com", "quantserve.com", 
                "scorecardresearch.com"
            ]
            def handle_route(route):
                url = route.request.url.lower()
                if any(domain in url for domain in blocked_domains):
                    route.abort()
                else:
                    route.continue_()
            page.route("**/*", handle_route)
        except Exception as e:
            print(f"[WARNING] Failed to set up tracking request filter: {e}")

        # Suppress chrome-extension fetch errors by returning a 404 response mock
        try:
            page.add_init_script("""
                const originalFetch = window.fetch;
                window.fetch = function(input, init) {
                    const url = typeof input === 'string' ? input : (input && input.url ? input.url : '');
                    if (url.startsWith('chrome-extension://')) {
                        return Promise.resolve(new Response('', { status: 404, statusText: 'Not Found' }));
                    }
                    return originalFetch.apply(this, arguments);
                };
            """)
        except Exception as e:
            print(f"[WARNING] Failed to add chrome-extension bypass init script: {e}")

        try:
            page.goto(url, timeout=30000)
            page.wait_for_timeout(2000)
            hide_cookie_banners(page)

            if is_captcha_present(page):
                print(f"[WARNING] Search blocked by captcha or verification screen on {config.search_provider}.")
                print("[INFO] Try switching SEARCH_PROVIDER or run in non-headless mode (HEADLESS=false) to solve the verification.")
                return []

            if use_google:
                cards = page.query_selector_all('div.g, div.SoR10e, div.n05aGc, div.card-section, div[role="listitem"]')
                for card in cards:
                    link_elem = card.query_selector("a")
                    if not link_elem:
                        continue
                    href = link_elem.get_attribute("href")
                    if not href or not href.startswith("http"):
                        continue

                    title_elem = card.query_selector('div[role="heading"], h3, div.n05aGc')
                    title = title_elem.inner_text().strip() if title_elem else link_elem.inner_text().strip()
                    if not title:
                        continue

                    snippet_elem = card.query_selector('div.GI74Re, div.Y8vN0b, div.b1562c, div.description')
                    snippet = snippet_elem.inner_text().strip() if snippet_elem else None

                    source_elem = card.query_selector('span.NUnG9b, div.mCBkyc, div.source')
                    source = source_elem.inner_text().strip() if source_elem else None

                    date_elem = card.query_selector('span.OSrXXb, span.LfZsrd, span.date')
                    date_str = date_elem.inner_text().strip() if date_elem else None

                    item = NewsItem(
                        keyword=keyword,
                        title=title,
                        url=href,
                        source=source,
                        snippet=snippet,
                        published_text=date_str,
                    )

                    from src.filter import is_trillion_news
                    from src.image_capture import capture_card_screenshot, save_error_placeholder

                    if is_trillion_news(item, config):
                        import uuid

                        temp_name = f"temp_{uuid.uuid4().hex}.png"
                        temp_path = os.path.join(config.image_dir, temp_name)

                        if sync_playwright is not None:
                            hide_cookie_banners(page)
                            capture_card_screenshot(card, temp_path)
                        else:
                            save_error_placeholder(temp_path, "Playwright not installed")

                        if not os.path.exists(temp_path) and os.path.exists(temp_path.replace(".png", ".txt")):
                            item.image_file = temp_name.replace(".png", ".txt")
                        else:
                            item.image_file = temp_name

                    results.append(item)
            else:
                cards = page.query_selector_all('div.news-card, div.news-card-body, div.card-with-image')
                if not cards:
                    cards = page.query_selector_all('div[class*="news-card"], div[class*="card"]')

                for card in cards:
                    title_elem = card.query_selector('a.title, a[class*="title"]')
                    if not title_elem:
                        continue
                    href = title_elem.get_attribute("href")
                    if not href or not href.startswith("http"):
                        continue
                    title = title_elem.inner_text().strip()
                    if not title:
                        continue

                    snippet_elem = card.query_selector('div.snippet, p.snippet, div[class*="snippet"]')
                    snippet = snippet_elem.inner_text().strip() if snippet_elem else None

                    source_elem = card.query_selector('a.source, span.source, div.source, a[class*="source"]')
                    source = source_elem.inner_text().strip() if source_elem else None

                    date_elem = card.query_selector('span.time, span[class*="time"]')
                    date_str = date_elem.inner_text().strip() if date_elem else None

                    item = NewsItem(
                        keyword=keyword,
                        title=title,
                        url=href,
                        source=source,
                        snippet=snippet,
                        published_text=date_str,
                    )

                    from src.filter import is_trillion_news
                    from src.image_capture import capture_card_screenshot, save_error_placeholder

                    if is_trillion_news(item, config):
                        import uuid

                        temp_name = f"temp_{uuid.uuid4().hex}.png"
                        temp_path = os.path.join(config.image_dir, temp_name)

                        if sync_playwright is not None:
                            hide_cookie_banners(page)
                            capture_card_screenshot(card, temp_path)
                        else:
                            save_error_placeholder(temp_path, "Playwright not installed")

                        if not os.path.exists(temp_path) and os.path.exists(temp_path.replace(".png", ".txt")):
                            item.image_file = temp_name.replace(".png", ".txt")
                        else:
                            item.image_file = temp_name

                    results.append(item)

        except Exception as e:
            print(f"[ERROR] Exception during scraping of '{keyword}': {e}")
        finally:
            browser.close()

    print(f"[INFO] Retrieved {len(results)} raw search results for '{keyword}'")
    return results[:config.max_results_per_keyword]
