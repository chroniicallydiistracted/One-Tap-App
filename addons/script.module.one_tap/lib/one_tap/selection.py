"""Episode selection logic for One-Tap TV Launcher."""
from __future__ import annotations

import random
from typing import Iterable, List

from . import db

def episode_candidates(
    show_id: str,
    episodes: Iterable[str],
    mode: str = "order",
    random_cfg: dict | None = None,
) -> List[str]:
    """Return an ordered list of candidate episodes for playback.

    ``episodes`` should be an iterable of episode file paths sorted in the
    desired order. ``mode`` can be ``"order"`` or ``"random"``. For random
    mode the configuration in ``random_cfg`` is consulted which currently
    supports ``exclude_last_n``.

    History is **not** updated here; the caller is responsible for recording
    the successfully played episode."""

    eps: List[str] = list(episodes)
    if not eps:
        raise ValueError("No episodes available")

    history = db.get_history(show_id)
    if mode == "random":
        random_cfg = random_cfg or {}
        exclude_n = int(random_cfg.get("exclude_last_n", 0))
        recent = set(history[-exclude_n:])
        candidates = [e for e in eps if e not in recent]
        if not candidates:
            candidates = eps
        random.shuffle(candidates)
        return candidates

    # Ordered mode: start from the episode after the last one in history and
    # wrap around at the end of the list.
    last = history[-1] if history else None
    if last in eps:
        idx = eps.index(last) + 1
    else:
        idx = 0
    if idx >= len(eps):
        idx = 0
    return eps[idx:] + eps[:idx]
