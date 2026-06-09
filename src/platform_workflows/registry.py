import os
from typing import Callable, Dict, Optional, Tuple

from src.config import AppConfig
from src.models import NewsItem
from src.platform_capabilities import is_posting_supported
from src.platform_workflows.facebook_workflow import (
    WORKFLOW_ID as FACEBOOK_WORKFLOW_ID,
    run_facebook_posting,
    validate_facebook_session,
)
from src.platform_workflows.linkedin_workflow import (
    WORKFLOW_ID as LINKEDIN_WORKFLOW_ID,
    run_linkedin_posting,
    validate_linkedin_session,
)
from src.platform_workflows.observability import log_workflow_result, log_workflow_start
from src.platform_workflows.profile_workflow import (
    PROFILE_WORKFLOW_PLATFORMS,
    build_profile_workflow_registry,
    run_profile_posting,
    validate_profile_session,
)
from src.platform_workflows.types import PostingWorkflowContext, PostingWorkflowResult
from src.posting_core import PLATFORM_CANONICAL, canonicalize_platform

WorkflowRunner = Callable[
    [object, str, Optional[str], Optional[Callable]],
    Tuple[bool, Optional[str]],
]
SessionValidator = Callable[[object], bool]


class PlatformWorkflowRegistration:
    def __init__(
        self,
        platform_key: str,
        workflow_id: str,
        run: WorkflowRunner,
        validate_session: SessionValidator,
    ):
        self.platform_key = platform_key
        self.workflow_id = workflow_id
        self.run = run
        self.validate_session = validate_session


def _build_registry() -> Dict[str, PlatformWorkflowRegistration]:
    entries = {
        "linkedin": PlatformWorkflowRegistration(
            "linkedin",
            LINKEDIN_WORKFLOW_ID,
            run_linkedin_posting,
            validate_linkedin_session,
        ),
        "facebook": PlatformWorkflowRegistration(
            "facebook",
            FACEBOOK_WORKFLOW_ID,
            run_facebook_posting,
            validate_facebook_session,
        ),
    }

    for platform_key in PROFILE_WORKFLOW_PLATFORMS:
        entries[platform_key] = PlatformWorkflowRegistration(
            platform_key,
            f"workflow.{platform_key}.profile.v1",
            lambda page, content, image, cb, key=platform_key: run_profile_posting(
                key, page, content, image, cb
            ),
            lambda page, key=platform_key: validate_profile_session(key, page),
        )
    return entries


WORKFLOW_REGISTRY: Dict[str, PlatformWorkflowRegistration] = _build_registry()


def get_platform_workflow(platform_key: str) -> PlatformWorkflowRegistration:
    normalized = canonicalize_platform(platform_key)
    if normalized not in WORKFLOW_REGISTRY:
        raise ValueError(f"No posting workflow registered for platform '{platform_key}'")
    return WORKFLOW_REGISTRY[normalized]


def get_workflow_id(platform_key: str) -> str:
    return get_platform_workflow(platform_key).workflow_id


def list_registered_workflows() -> Dict[str, str]:
    return {key: entry.workflow_id for key, entry in WORKFLOW_REGISTRY.items()}


def validate_platform_session(page, platform_key: str) -> bool:
    return get_platform_workflow(platform_key).validate_session(page)


def run_platform_posting(
    context: PostingWorkflowContext,
    config: AppConfig,
) -> PostingWorkflowResult:
    """Execute one platform-owned posting workflow inside a browser session."""
    from playwright.sync_api import sync_playwright

    try:
        platform_key = canonicalize_platform(context.platform_key)
    except ValueError as e:
        return PostingWorkflowResult(success=False, failure_reason=str(e))

    if not is_posting_supported(platform_key):
        display = PLATFORM_CANONICAL[platform_key]
        return PostingWorkflowResult(
            success=False,
            failure_reason=(
                f"Assisted posting for '{display}' is not supported in the current release slice."
            ),
        )

    workflow = get_platform_workflow(platform_key)
    log_workflow_start(
        workflow.workflow_id,
        PLATFORM_CANONICAL[platform_key],
        row_id=context.row_id,
        sheet_name=context.sheet_name,
    )

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

    try:
        with sync_playwright() as p:
            browser_context = p.chromium.launch_persistent_context(**launch_kwargs)
            page = browser_context.new_page() if not browser_context.pages else browser_context.pages[0]
            try:
                success, post_url = workflow.run(
                    page,
                    context.post_content,
                    context.image_path,
                    context.confirm_callback,
                )
                log_workflow_result(
                    workflow.workflow_id,
                    PLATFORM_CANONICAL[platform_key],
                    success,
                    row_id=context.row_id,
                    sheet_name=context.sheet_name,
                )
                return PostingWorkflowResult(
                    success=success,
                    post_url=post_url,
                    workflow_id=workflow.workflow_id,
                )
            except Exception as e:
                print(f"\n[ERROR] Assisted posting failed ({workflow.workflow_id}): {e}")
                print("[INFO] Fallback: Copy and paste the post content below manually:")
                print("=" * 60)
                print(context.post_content)
                print("=" * 60)
                if context.image_path:
                    print(f"Image Path: {context.image_path}")
                if context.confirm_callback:
                    context.confirm_callback()
                else:
                    input("Press Enter to close browser and return...")
                log_workflow_result(
                    workflow.workflow_id,
                    PLATFORM_CANONICAL[platform_key],
                    False,
                    failure_reason=str(e),
                    row_id=context.row_id,
                    sheet_name=context.sheet_name,
                )
                return PostingWorkflowResult(
                    success=False,
                    failure_reason=str(e),
                    workflow_id=workflow.workflow_id,
                )
            finally:
                browser_context.close()
    except Exception as e:
        return PostingWorkflowResult(
            success=False,
            failure_reason=str(e),
            workflow_id=workflow.workflow_id,
        )


def run_platform_posting_for_item(
    item: NewsItem,
    config: AppConfig,
    post_content: str,
    image_path: Optional[str],
    confirm_callback: Optional[Callable] = None,
    sheet_name: Optional[str] = None,
) -> bool:
    """Backward-compatible wrapper used by CLI, Web UI, and scheduler surfaces."""
    platform_name = item.platform or "linkedin"
    context = PostingWorkflowContext(
        platform_key=platform_name,
        post_content=post_content,
        image_path=image_path,
        row_id=getattr(item, "id", None),
        sheet_name=sheet_name,
        title=getattr(item, "title", None),
        confirm_callback=confirm_callback,
    )
    result = run_platform_posting(context, config)
    if result.success and result.post_url is not None:
        item.post_url = result.post_url or ""
    elif result.success:
        item.post_url = getattr(item, "post_url", "") or ""
    return result.success