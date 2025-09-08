"""Entry point for the One-Tap playback controller.

The script expects ``show_id`` to be provided as a query parameter.  The
configured tile for the show is looked up and the next episode is selected
according to the global configuration."""
from __future__ import annotations

import os
import sys
import urllib.parse
from typing import Dict, List, Iterator

from one_tap import config, db, jsonrpc, random_state, selection
from one_tap.logging import get_logger

try:  # pragma: no cover - depends on Kodi
    import xbmc  # type: ignore
    import xbmcvfs  # type: ignore
except ImportError:  # pragma: no cover - desktop/dev
    xbmc = None  # type: ignore
    xbmcvfs = None  # type: ignore

logger = get_logger("plugin.one_tap.play")


class EpisodePlayer(xbmc.Player if xbmc else object):
    """Player that automatically queues the next episode."""

    def __init__(self, show_id: str, candidates: List[str]):
        if not xbmc:  # pragma: no cover - desktop/dev
            raise RuntimeError("xbmc module not available")
        super().__init__()
        self.show_id = show_id
        self._candidates: Iterator[str] = iter(candidates)
        self.failures = 0
        self.active = True

    def _return_home(self) -> None:
        if xbmc:
            xbmc.executebuiltin("ActivateWindow(home)")
        self.active = False

    def play_next(self) -> None:
        while True:
            try:
                episode = next(self._candidates)
            except StopIteration:
                self._return_home()
                return
            logger.info("Attempting to play %s", episode)
            try:
                result = jsonrpc.play_file(episode)
            except Exception as exc:  # pragma: no cover - runtime
                logger.error("JSON-RPC failed for %s: %s", episode, exc)
                self.failures += 1
                if self.failures >= 3:
                    self._return_home()
                    return
                continue
            if result.get("error"):
                logger.error("Kodi reported error for %s: %s", episode, result["error"])
                self.failures += 1
                if self.failures >= 3:
                    self._return_home()
                    return
                continue
            db.update_history(self.show_id, episode)
            logger.info("Playing %s", episode)
            self.failures = 0
            return

    def onPlayBackEnded(self) -> None:  # pragma: no cover - depends on Kodi
        self.play_next()


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


    candidates = selection.episode_candidates(
        show_id, episodes, cfg.get("mode", "order"), cfg.get("random", {})
    )
    if not xbmc:
        logger.error("xbmc module not available")

        return

    player = EpisodePlayer(show_id, candidates)
    player.play_next()

    monitor = xbmc.Monitor()
    while player.active and not monitor.abortRequested():  # pragma: no cover - runtime
        monitor.waitForAbort(1)


if __name__ == "__main__":
    main()
