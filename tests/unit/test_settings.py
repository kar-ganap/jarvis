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
