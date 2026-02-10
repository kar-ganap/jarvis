from __future__ import annotations

import os
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

_DEFAULT_TOKEN_PATH = str(
    Path(__file__).resolve().parent.parent.parent.parent / "google_token.json"
)

SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/presentations",
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/spreadsheets",
]


def get_credentials() -> Credentials:
    """Load Google OAuth2 credentials from the token file.

    Auto-refreshes if the token is expired but has a valid refresh token.
    Reads token path from GOOGLE_TOKEN_PATH env var.
    """
    token_path = os.environ.get("GOOGLE_TOKEN_PATH", _DEFAULT_TOKEN_PATH)

    if not Path(token_path).exists():
        raise FileNotFoundError(
            f"Google token file not found: {token_path}. "
            f"Run 'uv run python scripts/setup_google_oauth.py' to authenticate."
        )

    creds = Credentials.from_authorized_user_file(token_path, scopes=None)

    if not creds.valid:
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            # Save refreshed token
            Path(token_path).write_text(creds.to_json())

    return creds
