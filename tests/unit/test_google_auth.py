from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestGetCredentials:
    def test_loads_token_from_file(self, tmp_path: Path, monkeypatch):
        """Loads valid credentials from a token file."""
        from jarvis.google.auth import get_credentials

        token_path = tmp_path / "google_token.json"
        token_path.write_text("{}")
        monkeypatch.setenv("GOOGLE_TOKEN_PATH", str(token_path))

        mock_creds = MagicMock()
        mock_creds.valid = True

        with patch(
            "jarvis.google.auth.Credentials.from_authorized_user_file",
            return_value=mock_creds,
        ) as mock_load:
            creds = get_credentials()

        mock_load.assert_called_once_with(str(token_path), scopes=pytest.approx(None))
        assert creds is mock_creds

    def test_refreshes_expired_token(self, tmp_path: Path, monkeypatch):
        """Refreshes credentials when token is expired but has refresh token."""
        from jarvis.google.auth import get_credentials

        token_path = tmp_path / "google_token.json"
        token_path.write_text("{}")
        monkeypatch.setenv("GOOGLE_TOKEN_PATH", str(token_path))

        mock_creds = MagicMock()
        mock_creds.valid = False
        mock_creds.expired = True
        mock_creds.refresh_token = "refresh-tok"
        mock_creds.to_json.return_value = '{"token": "refreshed"}'

        with (
            patch(
                "jarvis.google.auth.Credentials.from_authorized_user_file",
                return_value=mock_creds,
            ),
            patch("jarvis.google.auth.Request") as mock_request_cls,
        ):
            creds = get_credentials()

        mock_creds.refresh.assert_called_once_with(mock_request_cls())
        assert creds is mock_creds

    def test_raises_when_no_token_file(self, tmp_path: Path, monkeypatch):
        """Raises FileNotFoundError when token file does not exist."""
        from jarvis.google.auth import get_credentials

        monkeypatch.setenv("GOOGLE_TOKEN_PATH", str(tmp_path / "missing.json"))

        with pytest.raises(FileNotFoundError):
            get_credentials()
