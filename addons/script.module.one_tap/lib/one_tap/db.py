"""Simple JSON based progress database for One-Tap TV Launcher."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from . import config

# Path inside the add-on's profile directory where playback history is stored
PROGRESS_PATH = "special://profile/addon_data/plugin.one_tap.play/progress.json"


def _path() -> Path:
    return config._resolve(PROGRESS_PATH)


def _load() -> Dict[str, List[str]]:
    path = _path()
    if path.exists():
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save(data: Dict[str, List[str]]) -> None:
    path = _path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def get_history(show_id: str) -> List[str]:
    """Return playback history list for ``show_id``."""

    return _load().get(show_id, [])


def update_history(show_id: str, episode: str, max_history: int = 50) -> None:
    """Append ``episode`` to the history for ``show_id`` keeping ``max_history`` entries."""

    data = _load()
    history = data.get(show_id, [])
    history.append(episode)
    history = history[-max_history:]
    data[show_id] = history
    _save(data)
