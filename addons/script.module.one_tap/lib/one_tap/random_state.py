"""Shared storage for pre-selected random episodes."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from . import config

# Location for pre-selected episode candidates
PRESELECT_PATH = "special://profile/addon_data/service.one_tap.random/preselected.json"


def _path() -> Path:
    return config._resolve(PRESELECT_PATH)


def load() -> Dict[str, List[str]]:
    path = _path()
    if path.exists():
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save(data: Dict[str, List[str]]) -> None:
    path = _path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def get(show_id: str) -> List[str]:
    return load().get(show_id, [])


def set(show_id: str, candidates: List[str]) -> None:
    data = load()
    data[show_id] = candidates
    save(data)


def consume_first(show_id: str) -> None:
    data = load()
    items = data.get(show_id)
    if items:
        items = items[1:]
        if items:
            data[show_id] = items
        else:
            data.pop(show_id, None)
        save(data)
