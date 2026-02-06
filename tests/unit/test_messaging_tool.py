from __future__ import annotations

from unittest.mock import MagicMock, patch


class TestSendMessageToUser:
    def test_posts_to_bridge(self, monkeypatch):
        from jarvis.tools.messaging import send_message_to_user

        monkeypatch.setenv("JARVIS_HTTP_HOST", "localhost")
        monkeypatch.setenv("JARVIS_HTTP_PORT", "9100")

        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()

        with patch("requests.post", return_value=mock_resp) as mock_post:
            result = send_message_to_user("slack", "C123", "Hello!")

        assert "OK" in result
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args
        assert call_kwargs[1]["json"]["channel"] == "slack"
        assert call_kwargs[1]["json"]["text"] == "Hello!"
