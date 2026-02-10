from pathlib import Path

import pytest


class TestLoadSettings:
    def test_load_settings_from_yaml(self, tmp_config: Path) -> None:
        from jarvis.settings import load_settings

        settings = load_settings(tmp_config)

        assert settings.letta.base_url == "http://localhost:8283"
        assert settings.agent.name == "test-jarvis"
        assert settings.agent.model == "openai/gpt-5.2"
        assert settings.agent.embedding == "openai/text-embedding-3-small"
        assert settings.agent.context_window_limit == 30000
        assert settings.user.name == "TestUser"
        assert settings.user.preferred_channel == "cli"

    def test_load_settings_defaults(self, minimal_config: Path) -> None:
        from jarvis.settings import load_settings

        settings = load_settings(minimal_config)

        assert settings.letta.base_url == "http://localhost:8283"
        assert settings.agent.name == "jarvis"
        assert settings.user.name == "User"
        assert settings.user.preferred_channel == "cli"

    def test_load_settings_missing_file(self) -> None:
        from jarvis.settings import load_settings

        with pytest.raises(FileNotFoundError):
            load_settings(Path("/nonexistent/path/jarvis.yaml"))

    def test_load_settings_env_override(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """JARVIS_CONFIG env var is used when no explicit path given."""
        import yaml

        from jarvis.settings import load_settings

        config = {"letta": {}, "agent": {"name": "env-agent"}, "user": {}}
        config_path = tmp_path / "custom.yaml"
        config_path.write_text(yaml.dump(config))

        monkeypatch.setenv("JARVIS_CONFIG", str(config_path))

        settings = load_settings()
        assert settings.agent.name == "env-agent"

    def test_loads_whatsapp_settings(self, tmp_path: Path) -> None:
        """WhatsApp settings are loaded from YAML config."""
        import yaml

        from jarvis.settings import load_settings

        config = {
            "letta": {},
            "agent": {},
            "user": {},
            "whatsapp": {
                "enabled": True,
                "bridge_url": "http://mybridge:9120",
                "allow_groups": True,
            },
        }
        config_path = tmp_path / "jarvis.yaml"
        config_path.write_text(yaml.dump(config))

        settings = load_settings(config_path)
        assert settings.whatsapp.enabled is True
        assert settings.whatsapp.bridge_url == "http://mybridge:9120"
        assert settings.whatsapp.allow_groups is True

    def test_loads_google_settings(self, tmp_path: Path) -> None:
        """Google settings are loaded from YAML config."""
        import yaml

        from jarvis.settings import load_settings

        config = {
            "letta": {},
            "agent": {},
            "user": {},
            "google": {
                "client_secrets_path": "my_secrets.json",
                "token_path": "my_token.json",
            },
        }
        config_path = tmp_path / "jarvis.yaml"
        config_path.write_text(yaml.dump(config))

        settings = load_settings(config_path)
        assert settings.google.client_secrets_path == "my_secrets.json"
        assert settings.google.token_path == "my_token.json"

    def test_loads_browser_settings(self, tmp_path: Path) -> None:
        """Browser settings are loaded from YAML config."""
        import yaml

        from jarvis.settings import load_settings

        config = {
            "letta": {},
            "agent": {},
            "user": {},
            "browser": {
                "enabled": True,
                "headless": False,
                "timeout_ms": 60000,
            },
        }
        config_path = tmp_path / "jarvis.yaml"
        config_path.write_text(yaml.dump(config))

        settings = load_settings(config_path)
        assert settings.browser.enabled is True
        assert settings.browser.headless is False
        assert settings.browser.timeout_ms == 60000

    def test_loads_notion_settings(self, tmp_path: Path) -> None:
        """Notion settings are loaded from YAML config."""
        import yaml

        from jarvis.settings import load_settings

        config = {
            "letta": {},
            "agent": {},
            "user": {},
            "notion": {"enabled": True},
        }
        config_path = tmp_path / "jarvis.yaml"
        config_path.write_text(yaml.dump(config))

        settings = load_settings(config_path)
        assert settings.notion.enabled is True

    def test_loads_todoist_settings(self, tmp_path: Path) -> None:
        """Todoist settings are loaded from YAML config."""
        import yaml

        from jarvis.settings import load_settings

        config = {
            "letta": {},
            "agent": {},
            "user": {},
            "todoist": {
                "enabled": True,
            },
        }
        config_path = tmp_path / "jarvis.yaml"
        config_path.write_text(yaml.dump(config))

        settings = load_settings(config_path)
        assert settings.todoist.enabled is True

    def test_loads_memory_settings(self, tmp_path: Path) -> None:
        """Memory settings are loaded from YAML config."""
        import yaml

        from jarvis.settings import load_settings

        config = {
            "letta": {},
            "agent": {},
            "user": {},
            "memory": {
                "learning_enabled": False,
                "learning_interval_hours": 12,
            },
        }
        config_path = tmp_path / "jarvis.yaml"
        config_path.write_text(yaml.dump(config))

        settings = load_settings(config_path)
        assert settings.memory.learning_enabled is False
        assert settings.memory.learning_interval_hours == 12
