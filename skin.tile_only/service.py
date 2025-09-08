from __future__ import annotations

"""Startup service for the tile-only skin.

Loads the caregiver configuration and exposes tile metadata as window
properties for the Home screen.  This allows the skin's XML to remain
simple and only display the configured tiles.
"""

from typing import Any, Dict

try:  # Kodi runtime
    import xbmc  # type: ignore
    import xbmcgui  # type: ignore
except ImportError:  # pragma: no cover - outside Kodi
    xbmc = None  # type: ignore
    xbmcgui = None  # type: ignore

from one_tap import config

MAX_TILES = 12


def main() -> None:
    """Populate Window(Home) properties for each configured tile."""
    if xbmcgui is None:
        # Running outside Kodi; nothing to do
        return

    cfg: Dict[str, Any] = config.load_config()
    tiles = cfg.get("tiles", [])
    window = xbmcgui.Window(10000)  # Home window

    for i in range(1, MAX_TILES + 1):
        window.clearProperty(f"tile.{i}.label")
        window.clearProperty(f"tile.{i}.show_id")

    for idx, tile in enumerate(tiles[:MAX_TILES], start=1):
        window.setProperty(f"tile.{idx}.label", tile.get("label", ""))
        window.setProperty(f"tile.{idx}.show_id", tile.get("show_id", ""))

    window.setProperty("tile.count", str(len(tiles)))
    if xbmc:
        xbmc.log("One-Tap skin properties initialized", xbmc.LOGINFO)


if __name__ == "__main__":
    main()
