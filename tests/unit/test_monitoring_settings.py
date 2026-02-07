from __future__ import annotations

from pathlib import Path

import yaml


class TestMonitoringSettings:
    def test_default_metrics_enabled(self, minimal_config: Path) -> None:
        """Monitoring metrics are enabled by default."""
        from jarvis.settings import load_settings

        settings = load_settings(minimal_config)
        assert settings.monitoring.metrics_enabled is True

    def test_default_log_format_console(self, minimal_config: Path) -> None:
        """Default log format is 'console'."""
        from jarvis.settings import load_settings

        settings = load_settings(minimal_config)
        assert settings.monitoring.log_format == "console"

    def test_loads_monitoring_from_yaml(self, tmp_path: Path) -> None:
        """Monitoring section is loaded from YAML config."""
        from jarvis.settings import load_settings

        config = {
            "letta": {},
            "agent": {},
            "user": {},
            "monitoring": {
                "metrics_enabled": False,
                "log_format": "json",
            },
        }
        config_path = tmp_path / "jarvis.yaml"
        config_path.write_text(yaml.dump(config))

        settings = load_settings(config_path)
        assert settings.monitoring.metrics_enabled is False
        assert settings.monitoring.log_format == "json"

    def test_json_log_format_uses_json_renderer(self) -> None:
        """setup_logging('json') configures JSONRenderer."""
        import structlog

        from jarvis.utils.logging import setup_logging

        setup_logging(log_format="json")

        config = structlog.get_config()
        renderer = config["processors"][-1]
        assert isinstance(renderer, structlog.processors.JSONRenderer)

    def test_console_log_format_uses_console_renderer(self) -> None:
        """setup_logging('console') configures ConsoleRenderer."""
        import structlog

        from jarvis.utils.logging import setup_logging

        setup_logging(log_format="console")

        config = structlog.get_config()
        renderer = config["processors"][-1]
        assert isinstance(renderer, structlog.dev.ConsoleRenderer)
