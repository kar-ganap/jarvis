"""Entry point: python -m jarvis"""
from __future__ import annotations

import asyncio
import signal

from jarvis.app import JarvisApp
from jarvis.settings import load_settings
from jarvis.utils.logging import setup_logging


def main() -> None:
    settings = load_settings()
    setup_logging(log_format=settings.monitoring.log_format)
    app = JarvisApp(settings)

    loop = asyncio.new_event_loop()

    def _shutdown(sig: int, frame: object) -> None:
        loop.call_soon_threadsafe(loop.create_task, app.stop())

    signal.signal(signal.SIGTERM, _shutdown)

    try:
        loop.run_until_complete(app.start())
    except KeyboardInterrupt:
        loop.run_until_complete(app.stop())
    finally:
        loop.close()


if __name__ == "__main__":
    main()
