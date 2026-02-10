#!/usr/bin/env python3
"""One-time interactive OAuth2 setup for Gmail + Google Calendar.

Usage:
    uv run python scripts/setup_google_oauth.py

This will open a browser window for Google account authorization.
The resulting token is saved to google_token.json (gitignored).
"""
from __future__ import annotations

import sys
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/presentations",
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/spreadsheets",
]

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CLIENT_SECRETS = PROJECT_ROOT / "gcp_oauth_client_id.json"
TOKEN_PATH = PROJECT_ROOT / "google_token.json"


def main() -> None:
    if not CLIENT_SECRETS.exists():
        print(f"ERROR: Client secrets file not found: {CLIENT_SECRETS}")
        print("Place your GCP OAuth desktop client JSON at the project root.")
        sys.exit(1)

    if TOKEN_PATH.exists():
        print(f"Token file already exists: {TOKEN_PATH}")
        answer = input("Overwrite? [y/N] ").strip().lower()
        if answer != "y":
            print("Aborted.")
            sys.exit(0)

    print("Opening browser for Google authorization...")
    flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRETS), SCOPES)
    creds = flow.run_local_server(port=0)

    TOKEN_PATH.write_text(creds.to_json())
    print(f"Token saved to {TOKEN_PATH}")
    print("You can now run Jarvis with Gmail + Calendar support.")


if __name__ == "__main__":
    main()
