"""Entry point for the One-Tap playback controller.

The script expects ``show_id`` to be provided as a query parameter.  The
configured tile for the show is looked up and the next episode is selected
according to the global configuration.
"""
from __future__ import annotations

import os
import sys
import urllib.parse
from typing import Dict, List

from one_tap import config, db, selection
from one_tap.logging import get_logger

try:  # pragma: no cover - depends on Kodi
    import xbmc  # type: ignore
    import xbmcvfs  # type: ignore
except ImportError:  # pragma: no cover - desktop/dev
    xbmc = None  # type: ignore
    xbmcvfs = None  # type: ignore

logger = get_logger("plugin.one_tap.play")


def _list_episodes(path: str) -> List[str]:
    """Return a sorted list of episode files within ``path``."""

    exts = {".mkv", ".mp4", ".avi"}
    if xbmcvfs:
        dirs, files = xbmcvfs.listdir(path)
        episodes = [os.path.join(path, f) for f in files if os.path.splitext(f)[1].lower() in exts]
    else:
        episodes = [os.path.join(path, f) for f in os.listdir(path) if os.path.splitext(f)[1].lower() in exts]
    episodes.sort()
    return episodes


def _get_params() -> Dict[str, str]:
    if len(sys.argv) < 3:
        return {}
    qs = sys.argv[2][1:]
    return {k: v[0] for k, v in urllib.parse.parse_qs(qs).items()}


class AutoAdvancePlayer(xbmc.Player if xbmc else object):
    """Player that auto-advances episodes and tracks failures."""

    def __init__(self, show_id: str, episodes: List[str], cfg: dict) -> None:
        if xbmc:
            super().__init__()
        self.show_id = show_id
        self.episodes = episodes
        self.cfg = cfg
        self.failure_count = 0
        self.active = True
        self.play_next()

    def play_next(self) -> None:
        if not xbmc:
            logger.info("Kodi not available; cannot play episodes")
            self.active = False
            return

        candidates = selection.episode_candidates(
            self.show_id, self.episodes, self.cfg.get("mode", "order"), self.cfg.get("random", {})
        )
        for episode in candidates:
            if self.failure_count >= 3:
                break
            try:
                logger.info("Attempting to play %s", episode)
                super().play(episode)
            except Exception as exc:  # pragma: no cover - runtime only
                logger.error("Playback start failed for %s: %s", episode, exc)
                self.failure_count += 1
                continue
            db.update_history(self.show_id, episode)
            self.failure_count = 0
            logger.info("Playing %s", episode)
            return

        logger.error("Unable to start playback after %d failures", self.failure_count)
        self.active = False
        xbmc.executebuiltin("ActivateWindow(Home)")

    # Player callbacks
    def onPlayBackEnded(self) -> None:  # pragma: no cover - depends on Kodi
        logger.info("Playback ended; advancing")
        self.play_next()

    def onPlayBackStopped(self) -> None:  # pragma: no cover - depends on Kodi
        logger.info("Playback stopped by user")
        self.active = False

    def onPlayBackError(self) -> None:  # pragma: no cover - depends on Kodi
        logger.error("Playback error encountered")
        self.failure_count += 1
        if self.failure_count >= 3:
            self.active = False
            xbmc.executebuiltin("ActivateWindow(Home)")
        else:
            self.play_next()


def main() -> None:
    params = _get_params()
    show_id = params.get("show_id")
    if not show_id:
        logger.error("show_id parameter required")
        return

    cfg = config.load_config()
    tile = next((t for t in cfg.get("tiles", []) if t.get("show_id") == show_id), None)
    if not tile:
        logger.error("show_id %s not found in config", show_id)
        return

    episodes = _list_episodes(tile["path"])
    if not episodes:
        logger.error("No episodes found for %s", tile["path"])
        return

    player = AutoAdvancePlayer(show_id, episodes, cfg)
    if xbmc:
        monitor = xbmc.Monitor()
        while player.active and not monitor.abortRequested():
            if monitor.waitForAbort(1):
                break
    else:
        logger.info("Auto-advance requires Kodi; exiting")


if __name__ == "__main__":
    main()
