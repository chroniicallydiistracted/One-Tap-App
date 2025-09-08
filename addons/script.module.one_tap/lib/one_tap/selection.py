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
    mode the configuration in ``random_cfg`` supports ``exclude_last_n`` and
    ``use_comfort_weights``.

    History is **not** updated here; the caller is responsible for recording
    the successfully played episode."""

    eps: List[str] = list(episodes)
    if not eps:
        raise ValueError("No episodes available")

    history = db.get_history(show_id)
    if mode == "random":
        random_cfg = random_cfg or {}
        exclude_n = int(random_cfg.get("exclude_last_n", 0))
        use_weights = bool(random_cfg.get("use_comfort_weights"))
        recent = set(history[-exclude_n:])
        candidates = [e for e in eps if e not in recent]
        if not candidates:
            candidates = eps.copy()
        if use_weights and len(candidates) > 1:
            last = history[-1] if history else None
            last_idx = eps.index(last) if last in eps else 0
            weights = []
            for e in candidates:
                idx = eps.index(e)
                distance = abs(idx - last_idx)
                weights.append(1 / (1 + distance))
            first = random.choices(candidates, weights=weights, k=1)[0]
            remaining = [e for e in candidates if e != first]
            random.shuffle(remaining)
            return [first] + remaining
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
