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

from one_tap import config, db, jsonrpc, selection
from one_tap.logging import get_logger

try:  # pragma: no cover - depends on Kodi
    import xbmcvfs  # type: ignore
except ImportError:  # pragma: no cover - desktop/dev
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
    attempts = 0
    for episode in candidates:
        if attempts >= 3:
            break
        attempts += 1
        logger.info("Attempting to play %s", episode)
        try:
            result = jsonrpc.play_file(episode)
        except Exception as exc:  # pragma: no cover - runtime
            logger.error("JSON-RPC failed for %s: %s", episode, exc)
            continue
        if result.get("error"):
            logger.error("Kodi reported error for %s: %s", episode, result["error"])
            continue
        db.update_history(show_id, episode)
        logger.info("Playing %s", episode)
        return

    logger.error("Failed to start playback after %d attempts", attempts)

if __name__ == "__main__":
    main()
