from __future__ import annotations

import os
from pathlib import Path

import yaml
from pydantic import BaseModel

_DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "jarvis.yaml"


class LettaSettings(BaseModel):
    base_url: str = "http://localhost:8283"


class AgentSettings(BaseModel):
    name: str = "jarvis"
    model: str = "openai/gpt-5.2"
    embedding: str = "openai/text-embedding-3-small"
    context_window_limit: int = 30000


class UserSettings(BaseModel):
    name: str = "User"
    preferred_channel: str = "cli"


class SlackSettings(BaseModel):
    enabled: bool = False
    bot_token: str = ""
    app_token: str = ""


class HttpSettings(BaseModel):
    port: int = 9100
    host: str = "0.0.0.0"


class WhatsAppSettings(BaseModel):
    enabled: bool = False
    bridge_url: str = "http://localhost:9120"
    allow_groups: bool = False


class GoogleSettings(BaseModel):
    client_secrets_path: str = "gcp_oauth_client_id.json"
    token_path: str = "google_token.json"


class TodoistSettings(BaseModel):
    enabled: bool = False
    api_key: str = ""


class NotionSettings(BaseModel):
    enabled: bool = False


class BrowserSettings(BaseModel):
    enabled: bool = True
    headless: bool = True
    timeout_ms: int = 30000


class MemorySettings(BaseModel):
    learning_enabled: bool = True
    learning_interval_hours: int = 24


class MonitoringSettings(BaseModel):
    metrics_enabled: bool = True
    log_format: str = "console"


class JarvisSettings(BaseModel):
    letta: LettaSettings = LettaSettings()
    agent: AgentSettings = AgentSettings()
    user: UserSettings = UserSettings()
    slack: SlackSettings = SlackSettings()
    http: HttpSettings = HttpSettings()
    whatsapp: WhatsAppSettings = WhatsAppSettings()
    google: GoogleSettings = GoogleSettings()
    todoist: TodoistSettings = TodoistSettings()
    notion: NotionSettings = NotionSettings()
    browser: BrowserSettings = BrowserSettings()
    memory: MemorySettings = MemorySettings()
    monitoring: MonitoringSettings = MonitoringSettings()


def load_settings(config_path: Path | None = None) -> JarvisSettings:
    """Load settings from a YAML config file.

    Resolution order for config path:
    1. Explicit ``config_path`` argument
    2. ``JARVIS_CONFIG`` environment variable
    3. Default ``config/jarvis.yaml`` relative to project root
    """
    if config_path is None:
        env_path = os.environ.get("JARVIS_CONFIG")
        config_path = Path(env_path) if env_path else _DEFAULT_CONFIG_PATH

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    raw = yaml.safe_load(config_path.read_text()) or {}

    slack_raw = raw.get("slack") or {}
    slack = SlackSettings(**slack_raw)
    # Fall back to env vars for tokens if not set in YAML
    if not slack.bot_token:
        slack.bot_token = os.environ.get("SLACK_BOT_TOKEN", "")
    if not slack.app_token:
        slack.app_token = os.environ.get("SLACK_APP_TOKEN", "")

    todoist_raw = raw.get("todoist") or {}
    todoist = TodoistSettings(**todoist_raw)
    if not todoist.api_key:
        todoist.api_key = os.environ.get("TODOIST_API_KEY", "")

    return JarvisSettings(
        letta=LettaSettings(**(raw.get("letta") or {})),
        agent=AgentSettings(**(raw.get("agent") or {})),
        user=UserSettings(**(raw.get("user") or {})),
        slack=slack,
        http=HttpSettings(**(raw.get("http") or {})),
        whatsapp=WhatsAppSettings(**(raw.get("whatsapp") or {})),
        google=GoogleSettings(**(raw.get("google") or {})),
        todoist=todoist,
        notion=NotionSettings(**(raw.get("notion") or {})),
        browser=BrowserSettings(**(raw.get("browser") or {})),
        memory=MemorySettings(**(raw.get("memory") or {})),
        monitoring=MonitoringSettings(**(raw.get("monitoring") or {})),
    )
