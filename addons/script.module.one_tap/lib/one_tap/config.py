"""Configuration loading and saving for One-Tap TV Launcher.

This module reads the caregiver configuration JSON which defines the
available tiles, playback mode, and other settings. It falls back to a
reasonable default configuration if the file does not yet exist so that
the add-ons can operate during early development.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

try:  # Kodi runtime
    import xbmc  # type: ignore
    import xbmcvfs  # type: ignore
except ImportError:  # Desktop/dev fallback
    xbmc = None  # type: ignore
    xbmcvfs = None  # type: ignore

# Default location for the caregiver configuration file.  Kodi's
# ``special://`` paths are translated to an absolute filesystem path when
# running inside Kodi.  During development we resolve the path relative to
# the current working directory which mirrors the runtime layout.
CONFIG_PATH = "special://profile/addon_data/plugin.one_tap.play/config.json"


def _resolve(path: str) -> Path:
    """Resolve ``special://`` paths both inside and outside Kodi.

    When executed inside Kodi the ``xbmcvfs`` module knows how to translate
    ``special://`` URIs.  In a normal Python environment we simply treat the
    string as a regular file system path.
    """

    if xbmcvfs:  # pragma: no branch - runtime check
        return Path(xbmcvfs.translatePath(path))
    return Path(path).expanduser().resolve()


def load_config() -> Dict[str, Any]:
    """Return the caregiver configuration as a dictionary.

    If the configuration file does not exist a minimal default structure is
    returned.  Callers can modify the structure and persist it with
    :func:`save_config`.
    """

    path = _resolve(CONFIG_PATH)
    if not path.exists():
        return {"tiles": [], "mode": "order", "random": {}, "ui": {}, "pin": ""}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_config(cfg: Dict[str, Any]) -> None:
    """Persist configuration ``cfg`` to :data:`CONFIG_PATH`."""

    path = _resolve(CONFIG_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, sort_keys=True)
