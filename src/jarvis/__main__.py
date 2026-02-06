"""Entry point: python -m jarvis"""
from __future__ import annotations

import asyncio

from jarvis.app import JarvisApp
from jarvis.settings import load_settings
from jarvis.utils.logging import setup_logging


def main() -> None:
    setup_logging()
    settings = load_settings()
    app = JarvisApp(settings)
    try:
        asyncio.run(app.start())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
