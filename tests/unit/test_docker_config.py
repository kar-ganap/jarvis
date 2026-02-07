from __future__ import annotations

from pathlib import Path

_DOCKER_CONFIG = Path(__file__).resolve().parent.parent.parent / "config" / "jarvis-docker.yaml"


class TestDockerConfig:
    def test_docker_config_exists(self) -> None:
        """jarvis-docker.yaml exists in config directory."""
        assert _DOCKER_CONFIG.exists(), f"Missing {_DOCKER_CONFIG}"

    def test_docker_config_loads(self) -> None:
        """jarvis-docker.yaml is a valid config that loads via load_settings."""
        from jarvis.settings import load_settings

        settings = load_settings(_DOCKER_CONFIG)
        assert settings.letta.base_url is not None

    def test_docker_config_uses_service_names(self) -> None:
        """Docker config uses Docker service names for discovery."""
        from jarvis.settings import load_settings

        settings = load_settings(_DOCKER_CONFIG)
        assert "letta_server" in settings.letta.base_url
        assert "whatsapp_bridge" in settings.whatsapp.bridge_url

    def test_docker_config_uses_json_logging(self) -> None:
        """Docker config sets log_format to 'json' for structured container logs."""
        from jarvis.settings import load_settings

        settings = load_settings(_DOCKER_CONFIG)
        assert settings.monitoring.log_format == "json"
