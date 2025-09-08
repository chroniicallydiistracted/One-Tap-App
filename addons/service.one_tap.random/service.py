"""Background service providing auto-advance and playback error handling."""
from __future__ import annotations

import random
import urllib.parse

from one_tap import config, db
from one_tap.logging import get_logger

logger = get_logger("service.one_tap.random")

try:  # pragma: no cover - depends on Kodi
    import xbmc  # type: ignore
except ImportError:  # pragma: no cover - desktop/dev
    xbmc = None  # type: ignore


if xbmc:  # pragma: no cover - depends on Kodi
    class AutoAdvancePlayer(xbmc.Player):
        """Player monitoring playback to auto-advance on completion or error."""

        def _current_show(self) -> str | None:
            current = self.getPlayingFile()
            if not current:
                return None
            cfg = config.load_config()
            for tile in cfg.get("tiles", []):
                path = tile.get("path")
                if path and current.startswith(path):
                    return tile.get("show_id")
            return None

        def _next_show(self) -> str | None:
            cfg = config.load_config()
            tiles = [t for t in cfg.get("tiles", []) if t.get("show_id")]
            if not tiles:
                return None
            current = self._current_show()
            if current and len(tiles) > 1:
                tiles = [t for t in tiles if t.get("show_id") != current]
            if not tiles:
                return None
            rand_cfg = cfg.get("random", {})
            if rand_cfg.get("use_comfort_weights"):
                show_ids = [t["show_id"] for t in tiles]
                weights = [float(t.get("weight", 1)) for t in tiles]
                return random.choices(show_ids, weights=weights, k=1)[0]
            return random.choice([t["show_id"] for t in tiles])

        def _play_next(self) -> None:
            show_id = self._next_show()
            if not show_id:
                return
            xbmc.executebuiltin(
                f'RunPlugin("plugin://plugin.one_tap.play?show_id={urllib.parse.quote_plus(show_id)}")'
            )

        def onPlayBackEnded(self) -> None:  # type: ignore[override]
            logger.info("Playback ended; starting next episode")
            self._play_next()

        def onPlayBackError(self) -> None:  # type: ignore[override]
            logger.error("Playback error encountered; skipping to next")
            show_id = self._current_show()
            if show_id:
                db.remove_last_history(show_id)
            self._play_next()


def run() -> None:
    logger.info("Randomizer service starting")
    if xbmc:
        player = AutoAdvancePlayer()
        monitor = xbmc.Monitor()
        while not monitor.abortRequested():
            if monitor.waitForAbort(60):
                break
        del player  # Keep player alive for callbacks
    else:
        logger.info("Kodi environment not available; service idle")
    logger.info("Randomizer service stopped")


if __name__ == "__main__":
    run()
