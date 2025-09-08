"""Background service for the One-Tap randomizer."""
from __future__ import annotations

import os
from typing import Dict, List

from one_tap import config, jsonrpc, random_state, selection
from one_tap.logging import get_logger

try:  # pragma: no cover - depends on Kodi
    import xbmc  # type: ignore
    import xbmcvfs  # type: ignore
except ImportError:  # pragma: no cover - desktop/dev
    xbmc = None  # type: ignore
    xbmcvfs = None  # type: ignore

logger = get_logger("service.one_tap.random")


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


def _update() -> None:
    cfg = config.load_config()
    if cfg.get("mode") != "random":
        return
    random_cfg = cfg.get("random", {})
    data: Dict[str, List[str]] = {}
    for tile in cfg.get("tiles", []):
        show_id = tile.get("show_id")
        path = tile.get("path")
        if not show_id or not path:
            continue
        episodes = _list_episodes(path)
        if not episodes:
            continue
        candidates = selection.episode_candidates(show_id, episodes, "random", random_cfg)
        data[show_id] = candidates
    if data:
        random_state.save(data)
        try:  # Best effort notification
            jsonrpc.call(
                "JSONRPC.NotifyAll", {"sender": "service.one_tap.random", "message": "updated"}
            )
        except Exception:  # pragma: no cover - environment dependent
            logger.debug("JSON-RPC notification failed")


def run() -> None:
    logger.info("Randomizer service starting")
    _update()
    if xbmc:
        monitor = xbmc.Monitor()
        while not monitor.abortRequested():
            if monitor.waitForAbort(300):
                break
            _update()
    logger.info("Randomizer service stopped")


if __name__ == "__main__":
    run()
