"""Playback history storage using SQLite for One-Tap TV Launcher."""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import List

from . import config

# Path inside the add-on's profile directory where playback history is stored
DB_PATH = "special://profile/addon_data/plugin.one_tap.play/one_tap.db"


def _path() -> Path:
    return config._resolve(DB_PATH)


def _connect() -> sqlite3.Connection:
    path = _path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS history (
            show_id TEXT NOT NULL,
            episode TEXT NOT NULL,
            played_at REAL DEFAULT (strftime('%s','now'))
        )
        """
    )
    return conn


def get_history(show_id: str) -> List[str]:
    """Return playback history list for ``show_id``."""

    with _connect() as conn:
        rows = conn.execute(
            "SELECT episode FROM history WHERE show_id=? ORDER BY rowid",
            (show_id,),
        ).fetchall()
    return [r[0] for r in rows]


def update_history(show_id: str, episode: str, max_history: int = 50) -> None:
    """Append ``episode`` to the history for ``show_id`` keeping ``max_history`` entries."""

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

