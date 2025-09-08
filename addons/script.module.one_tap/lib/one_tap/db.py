"""Playback history storage using SQLite for One-Tap TV Launcher."""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import List, Optional

import logging

from . import config

# Path inside the add-on's profile directory where playback history is stored
DB_PATH = "special://profile/addon_data/plugin.one_tap.play/one_tap.db"
DEFAULT_MAX_HISTORY = 50

logger = logging.getLogger(__name__)


def _path() -> Path:
    return config._resolve(DB_PATH)


def _connect() -> sqlite3.Connection:
    path = _path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS history (
            show_id TEXT NOT NULL,
            episode TEXT NOT NULL,
            played_at REAL DEFAULT (strftime('%s','now'))
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_history_show ON history(show_id)")
    return conn


def get_history(show_id: str) -> List[str]:
    """Return playback history list for ``show_id``."""

    try:
        with _connect() as conn:
            rows = conn.execute(
                "SELECT episode FROM history WHERE show_id=? ORDER BY rowid",
                (show_id,),
            ).fetchall()
    except sqlite3.DatabaseError as exc:  # pragma: no cover - defensive
        logger.error("Failed to read history for %s: %s", show_id, exc)
        return []
    return [r[0] for r in rows]


def update_history(
    show_id: str, episode: str, max_history: int = DEFAULT_MAX_HISTORY
) -> None:
    """Append ``episode`` to the history for ``show_id`` keeping ``max_history`` entries."""
    try:
        with _connect() as conn:
            conn.execute(
                "INSERT INTO history(show_id, episode) VALUES (?, ?)",
                (show_id, episode),
            )
            conn.execute(
                """
                DELETE FROM history
                WHERE show_id=?
                  AND rowid NOT IN (
                    SELECT rowid FROM history WHERE show_id=? ORDER BY rowid DESC LIMIT ?
                  )
                """,
                (show_id, show_id, max_history),
            )
    except sqlite3.DatabaseError as exc:  # pragma: no cover - defensive
        logger.error("Failed to update history for %s: %s", show_id, exc)


def remove_last_history(show_id: str) -> None:
    """Remove the most recent history entry for ``show_id``."""

    try:
        with _connect() as conn:
            conn.execute(
                "DELETE FROM history WHERE rowid = (SELECT MAX(rowid) FROM history WHERE show_id=?)",
                (show_id,),
            )
    except sqlite3.DatabaseError as exc:  # pragma: no cover - defensive
        logger.error("Failed to remove last history for %s: %s", show_id, exc)


def purge_history(show_id: Optional[str] = None) -> None:
    """Remove history for ``show_id`` or all shows when ``show_id`` is ``None``."""

    try:
        with _connect() as conn:
            if show_id is None:
                conn.execute("DELETE FROM history")
            else:
                conn.execute("DELETE FROM history WHERE show_id=?", (show_id,))
    except sqlite3.DatabaseError as exc:  # pragma: no cover - defensive
        logger.error("Failed to purge history: %s", exc)

