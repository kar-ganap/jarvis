#!/usr/bin/env python3
"""Check if the Letta server is reachable."""
from __future__ import annotations

import sys

from letta_client import Letta

from jarvis.settings import load_settings
from jarvis.utils.logging import setup_logging


def main() -> None:
    setup_logging()
    settings = load_settings()
    url = settings.letta.base_url

    print(f"Checking Letta server at {url} ...")
    try:
        client = Letta(base_url=url, timeout=10)
        page = client.agents.list(limit=1)
        print(f"OK — server reachable, {len(page.items)} agent(s) found.")
    except Exception as exc:
        print(f"FAIL — could not reach server: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
