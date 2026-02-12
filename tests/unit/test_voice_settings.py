from __future__ import annotations

import os
from unittest.mock import patch


class TestVoiceSettings:
    def test_defaults(self):
        from jarvis.settings import VoiceSettings

        s = VoiceSettings()
        assert s.enabled is False
        assert s.openai_api_key == ""
        assert s.stt_model == "whisper-1"
        assert s.tts_model == "tts-1"
        assert s.tts_voice == "nova"
        assert s.tts_mode == "auto"

    def test_disabled_by_default_in_settings(self):
        from jarvis.settings import JarvisSettings

        settings = JarvisSettings()
        assert settings.voice.enabled is False

    def test_tts_mode_values(self):
        from jarvis.settings import VoiceSettings

        for mode in ("auto", "always", "never"):
            s = VoiceSettings(tts_mode=mode)
            assert s.tts_mode == mode

    def test_openai_api_key_from_env(self, tmp_path):
        from jarvis.settings import load_settings

        config = tmp_path / "jarvis.yaml"
        config.write_text("voice:\n  enabled: true\n")

        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-from-env"}, clear=False):
            settings = load_settings(config)

        assert settings.voice.enabled is True
        assert settings.voice.openai_api_key == "sk-from-env"
