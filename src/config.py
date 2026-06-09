import os
import shutil
import yaml

from src.env_settings_store import resolve_env_path

def load_dotenv(path=".env"):
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or not line.strip():
                continue
            if "=" in line:
                key, val = line.split("=", 1)
                os.environ[key.strip()] = val.strip()

class AppConfig:
    def __init__(self, env_path=None, yaml_path="config.yaml"):
        # Load environment variables first
        resolved_env_path = env_path or resolve_env_path()
        load_dotenv(resolved_env_path)
        
        self.yaml_config = {}
        if os.path.exists(yaml_path):
            with open(yaml_path, "r", encoding="utf-8") as f:
                loaded = yaml.safe_load(f)
                if isinstance(loaded, dict):
                    self.yaml_config = loaded

        # AI Configuration
        self.ai_provider = os.getenv("AI_PROVIDER", self.yaml_config.get("ai_provider", "gemini"))
        self.ai_api_key = os.getenv("GEMINI_API_KEY", "")
        self.ai_model = os.getenv("AI_MODEL", self.yaml_config.get("ai_model", "gemini-1.5-flash"))

        # Search Configuration
        search_cfg = self.yaml_config.get("search", {})
        self.search_provider = os.getenv("SEARCH_PROVIDER", search_cfg.get("provider", "bing"))
        self.playwright_chromium_executable_path = self._detect_browser_executable()
        
        # Parse headless mode safely
        headless_val = os.getenv("HEADLESS")
        if headless_val is not None:
            self.headless = headless_val.lower() == "true"
        else:
            self.headless = search_cfg.get("headless", False)
            if isinstance(self.headless, str):
                self.headless = self.headless.lower() == "true"

        # Limits
        self.max_results_per_keyword = int(os.getenv("MAX_RESULTS_PER_KEYWORD", str(search_cfg.get("max_results_per_keyword", 10))))
        self.require_terms = search_cfg.get("require_terms", ["trillion", "trillion-dollar", "$ trillion", "USD"])
        self.exclude_domains = search_cfg.get("exclude_domains", [])

        # Directories
        self.output_dir = os.getenv("OUTPUT_DIR", "./output")
        from src.writeback import resolve_workbook_path

        self.excel_file = resolve_workbook_path(
            self.output_dir,
            os.getenv(
                "EXCEL_FILE",
                os.path.join(self.output_dir, "Trillion $ news.xlsx"),
            ),
        )
        self.image_dir = os.getenv("IMAGE_DIR", os.path.join(self.output_dir, "Ảnh Trillion $ news"))
        self.post_dir = os.getenv("POST_DIR", os.path.join(self.output_dir, "posts"))
        self.log_dir = os.getenv("LOG_DIR", os.path.join(self.output_dir, "logs"))

        # Posting preferences
        self.default_platform = "linkedin"
        self.platform_locked = True
        self.supported_platforms = ("linkedin",)
        self.default_language = os.getenv("DEFAULT_LANGUAGE", self.yaml_config.get("language", "en"))
        self.max_posts_per_run = int(os.getenv("MAX_POSTS_PER_RUN", 5))

        # Hashtags
        hashtags_cfg = self.yaml_config.get("hashtags", {})
        self.fixed_bottom_hashtags = hashtags_cfg.get("fixed_bottom", ["TAHKFoundation", "HenryUniverses", "USIran", "USTariffs", "Trump"])

        posting_cfg = self.yaml_config.get("posting", {})
        self.posting_mode = posting_cfg.get("mode", "draft_only")
        self.human_confirm_before_post = posting_cfg.get("human_confirm_before_post", True)
        
        # Backup configuration
        backup_val = os.getenv("BACKUP_ENABLED")
        if backup_val is not None:
            self.backup_enabled = backup_val.lower() == "true"
        else:
            self.backup_enabled = posting_cfg.get("backup_enabled", False)
            if isinstance(self.backup_enabled, str):
                self.backup_enabled = self.backup_enabled.lower() == "true"


    def _detect_browser_executable(self) -> str | None:
        configured_path = os.getenv("PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH", "").strip()
        if configured_path:
            return configured_path

        for candidate in (
            "google-chrome-stable",
            "google-chrome",
            "chromium",
            "chromium-browser",
        ):
            resolved = shutil.which(candidate)
            if resolved:
                return resolved

        for candidate in (
            "/opt/google/chrome/google-chrome",
            "/usr/bin/google-chrome",
            "/usr/bin/google-chrome-stable",
            "/usr/bin/chromium",
            "/usr/bin/chromium-browser",
        ):
            if os.path.exists(candidate):
                return candidate

        return None
