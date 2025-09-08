"""Background service stub for the One-Tap randomizer."""
from __future__ import annotations

from one_tap.logging import get_logger

logger = get_logger("service.one_tap.random")

try:  # pragma: no cover - depends on Kodi
    import xbmc  # type: ignore
except ImportError:  # pragma: no cover - desktop/dev
    xbmc = None  # type: ignore


def run() -> None:
    logger.info("Randomizer service starting")
    if xbmc:
        monitor = xbmc.Monitor()
        while not monitor.abortRequested():
            if monitor.waitForAbort(60):
                break
    logger.info("Randomizer service stopped")


if __name__ == "__main__":
    run()
