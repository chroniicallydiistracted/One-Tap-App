"""Logging helper usable both inside and outside Kodi."""
from __future__ import annotations

import logging
try:  # pragma: no cover - depends on Kodi
    import xbmc  # type: ignore
except ImportError:  # pragma: no cover - desktop/dev
    xbmc = None  # type: ignore


class Logger:
    """Small wrapper that mimics :mod:`logging` and ``xbmc.log``."""

    def __init__(self, name: str = "one_tap") -> None:
        self.name = name
        if xbmc:
            self._use_kodi = True
        else:
            self._use_kodi = False
            self._logger = logging.getLogger(name)

    def _log(self, level: int, msg: str) -> None:
        if self._use_kodi:
            xbmc.log(f"[{self.name}] {msg}", level)
        else:
            self._logger.log(level, msg)

    def info(self, msg: str) -> None:
        self._log(logging.INFO, msg)

    def warning(self, msg: str) -> None:
        self._log(logging.WARNING, msg)

    def error(self, msg: str) -> None:
        self._log(logging.ERROR, msg)

    def debug(self, msg: str) -> None:
        self._log(logging.DEBUG, msg)


def get_logger(name: str = "one_tap") -> Logger:
    return Logger(name)
