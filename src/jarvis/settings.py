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


class JarvisSettings(BaseModel):
    letta: LettaSettings = LettaSettings()
    agent: AgentSettings = AgentSettings()
    user: UserSettings = UserSettings()


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

    return JarvisSettings(
        letta=LettaSettings(**(raw.get("letta") or {})),
        agent=AgentSettings(**(raw.get("agent") or {})),
        user=UserSettings(**(raw.get("user") or {})),
    )
