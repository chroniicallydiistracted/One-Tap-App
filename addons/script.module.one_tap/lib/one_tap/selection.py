"""Episode selection logic for One-Tap TV Launcher."""
from __future__ import annotations

import random
from typing import Iterable, List

from . import db


def choose_episode(
    show_id: str,
    episodes: Iterable[str],
    mode: str = "order",
    random_cfg: dict | None = None,
) -> str:
    """Return the next episode path according to ``mode``.

    ``episodes`` should be an iterable of episode file paths sorted in the
    desired order.  ``mode`` can be ``"order"`` or ``"random"``.  For random
    mode the configuration in ``random_cfg`` is consulted which currently
    supports ``exclude_last_n``.
    """

    eps: List[str] = list(episodes)
    if not eps:
        raise ValueError("No episodes available")

    history = db.get_history(show_id)
    if mode == "random":
        random_cfg = random_cfg or {}
        exclude_n = int(random_cfg.get("exclude_last_n", 0))
        candidates = [e for e in eps if e not in history[-exclude_n:]]
        if not candidates:
            candidates = eps
        episode = random.choice(candidates)
    else:  # order
        last = history[-1] if history else None
        if last in eps:
            idx = eps.index(last) + 1
        else:
            idx = 0
        if idx >= len(eps):
            idx = 0
        episode = eps[idx]

    db.update_history(show_id, episode)
    return episode
