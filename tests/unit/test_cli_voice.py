from __future__ import annotations

import asyncio
from unittest.mock import MagicMock, patch

import numpy as np

from jarvis.channels.base import ChannelType, OutboundMessage


class TestCLIVoiceRecord:
    def test_record_audio_returns_bytes(self):
        from jarvis.channels.cli import CLIChannel

        ch = CLIChannel(user_name="Test", voice_enabled=True)

        # Mock sounddevice.rec and sounddevice.wait
        fake_audio = np.zeros((16000, 1), dtype=np.float32)
        with (
            patch("jarvis.channels.cli.sd") as mock_sd,
            patch("jarvis.channels.cli.sf") as mock_sf,
        ):
            mock_sd.rec.return_value = fake_audio
            mock_sd.wait = MagicMock()

            # Mock sf.write to write some bytes
            def fake_write(buf, data, samplerate, format):
                buf.write(b"RIFF" + b"\x00" * 100)

            mock_sf.write.side_effect = fake_write

            result = ch._record_audio()

        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_record_returns_wav_bytes(self):
        from jarvis.channels.cli import CLIChannel

        ch = CLIChannel(user_name="Test", voice_enabled=True)

        fake_audio = np.ones((8000, 1), dtype=np.float32) * 0.5
        with (
            patch("jarvis.channels.cli.sd") as mock_sd,
            patch("jarvis.channels.cli.sf") as mock_sf,
        ):
            mock_sd.rec.return_value = fake_audio
            mock_sd.wait = MagicMock()

            def fake_write(buf, data, samplerate, format):
                buf.write(b"WAV-content")

            mock_sf.write.side_effect = fake_write

            result = ch._record_audio()

        assert isinstance(result, bytes)


class TestCLIVoicePlay:
    def test_play_audio_calls_sounddevice(self):
        from jarvis.channels.cli import CLIChannel

        ch = CLIChannel(user_name="Test", voice_enabled=True)

        with (
            patch("jarvis.channels.cli.sf") as mock_sf,
            patch("jarvis.channels.cli.sd") as mock_sd,
        ):
            mock_sf.read.return_value = (np.zeros((16000,), dtype=np.float32), 16000)

            ch._play_audio(b"fake-mp3-bytes")

            mock_sd.play.assert_called_once()
            mock_sd.wait.assert_called_once()


class TestCLIVoiceSend:
    def test_send_with_audio_plays_audio(self):
        from jarvis.channels.cli import CLIChannel

        ch = CLIChannel(user_name="Test", voice_enabled=True)

        msg = OutboundMessage(
            channel_type=ChannelType.CLI,
            recipient_id="cli-user",
            text="Hello!",
            audio_data=b"mp3-bytes",
            audio_mime="audio/mp3",
        )

        with patch.object(ch, "_play_audio") as mock_play:
            asyncio.run(ch.send(msg))

            mock_play.assert_called_once_with(b"mp3-bytes")

    def test_send_text_only_prints(self, capsys):
        from jarvis.channels.cli import CLIChannel

        ch = CLIChannel(user_name="Test")

        msg = OutboundMessage(
            channel_type=ChannelType.CLI,
            recipient_id="cli-user",
            text="Just text",
        )
        asyncio.run(ch.send(msg))

        captured = capsys.readouterr()
        assert "Just text" in captured.out


class TestCLIVoiceMode:
    def test_voice_enabled_flag(self):
        from jarvis.channels.cli import CLIChannel

        ch = CLIChannel(user_name="Test", voice_enabled=True)
        assert ch._voice_enabled is True

    def test_voice_disabled_by_default(self):
        from jarvis.channels.cli import CLIChannel

        ch = CLIChannel(user_name="Test")
        assert ch._voice_enabled is False
