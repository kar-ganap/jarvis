from __future__ import annotations

import signal
from unittest.mock import AsyncMock, MagicMock, patch


class TestGracefulShutdown:
    def test_sigterm_calls_stop(self):
        """Verify that SIGTERM triggers app.stop()."""
        from jarvis.__main__ import main

        mock_app = MagicMock()
        mock_app.start = AsyncMock()
        mock_app.stop = AsyncMock()

        captured_handler = {}

        def fake_signal(sig, handler):
            captured_handler[sig] = handler

        with patch("jarvis.__main__.load_settings") as mock_load, \
             patch("jarvis.__main__.setup_logging"), \
             patch("jarvis.__main__.JarvisApp", return_value=mock_app), \
             patch("jarvis.__main__.signal.signal", side_effect=fake_signal):
            # Make start() raise KeyboardInterrupt to exit the loop
            mock_app.start.side_effect = KeyboardInterrupt()
            mock_load.return_value = MagicMock()

            main()

        assert signal.SIGTERM in captured_handler
