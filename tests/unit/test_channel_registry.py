from __future__ import annotations


class TestChannelRegistry:
    def test_always_includes_cli(self, test_settings):
        from jarvis.channels.base import ChannelType
        from jarvis.channels.registry import ChannelRegistry

        channels = ChannelRegistry.build(test_settings)
        assert ChannelType.CLI in channels

    def test_includes_slack_when_enabled(self, tmp_path):
        import yaml

        from jarvis.channels.base import ChannelType
        from jarvis.channels.registry import ChannelRegistry
        from jarvis.settings import load_settings

        config = {
            "letta": {},
            "agent": {},
            "user": {"name": "Test"},
            "slack": {
                "enabled": True,
                "bot_token": "xoxb-test",
                "app_token": "xapp-test",
            },
        }
        config_path = tmp_path / "jarvis.yaml"
        config_path.write_text(yaml.dump(config))

        settings = load_settings(config_path)
        channels = ChannelRegistry.build(settings)

        assert ChannelType.SLACK in channels

    def test_excludes_slack_when_disabled(self, test_settings):
        from jarvis.channels.base import ChannelType
        from jarvis.channels.registry import ChannelRegistry

        # Default settings have slack.enabled=False
        channels = ChannelRegistry.build(test_settings)
        assert ChannelType.SLACK not in channels

    def test_includes_whatsapp_when_enabled(self, tmp_path):
        import yaml

        from jarvis.channels.base import ChannelType
        from jarvis.channels.registry import ChannelRegistry
        from jarvis.settings import load_settings

        config = {
            "letta": {},
            "agent": {},
            "user": {"name": "Test"},
            "whatsapp": {
                "enabled": True,
                "bridge_url": "http://localhost:9120",
            },
        }
        config_path = tmp_path / "jarvis.yaml"
        config_path.write_text(yaml.dump(config))

        settings = load_settings(config_path)
        channels = ChannelRegistry.build(settings)

        assert ChannelType.WHATSAPP in channels

    def test_excludes_whatsapp_when_disabled(self, test_settings):
        from jarvis.channels.base import ChannelType
        from jarvis.channels.registry import ChannelRegistry

        # Default settings have whatsapp.enabled=False
        channels = ChannelRegistry.build(test_settings)
        assert ChannelType.WHATSAPP not in channels
