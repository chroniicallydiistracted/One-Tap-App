"""Caregiver helper script providing basic configuration management."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Callable, Dict, List

from one_tap import config, db
from one_tap.logging import get_logger

logger = get_logger("script.one_tap.caregiver")

try:  # pragma: no cover - depends on Kodi
    import xbmcgui  # type: ignore
except ImportError:  # pragma: no cover - desktop/dev
    xbmcgui = None  # type: ignore


def _prompt_pin(message: str) -> str:
    """Request a PIN from the user, falling back to ``input`` in tests."""

    if xbmcgui:  # pragma: no cover - requires Kodi
        dialog = xbmcgui.Dialog()
        return dialog.numeric(0, message) or ""
    return input(f"{message}: ")


def _prompt(message: str) -> str:
    """Return user input via GUI or ``input`` for tests."""

    if xbmcgui:  # pragma: no cover - requires Kodi
        dialog = xbmcgui.Dialog()
        return dialog.input(message) or ""
    return input(f"{message}: ")


def _select(title: str, options: List[str], get_input: Callable[[str], str]) -> int:
    """Return index of selected option or ``-1`` if cancelled."""

    if xbmcgui:  # pragma: no cover - requires Kodi
        dialog = xbmcgui.Dialog()
        return dialog.select(title, options)

    while True:  # pragma: no cover - CLI fallback for tests/dev
        for i, opt in enumerate(options, 1):
            print(f"{i}. {opt}")
        resp = get_input(
            f"{title} (1-{len(options)} or Enter to cancel): "
        ).strip()
        if not resp:
            return -1
        try:
            choice = int(resp) - 1
        except ValueError:
            continue
        if 0 <= choice < len(options):
            return choice


def verify_pin(get_pin: Callable[[str], str] = _prompt_pin) -> bool:
    """Return ``True`` if the caregiver PIN is valid or not set."""

    cfg = config.load_config()
    expected = cfg.get("pin", "")
    if not expected:
        return True
    attempt = get_pin("Enter caregiver PIN")
    if attempt != expected:
        logger.error("Incorrect PIN entered")
        return False
    return True

def _manage_tiles(cfg: Dict, get_input: Callable[[str], str]) -> None:
    """Allow caregivers to add, remove, edit, or reorder tiles."""

    tiles: List[Dict] = cfg.setdefault("tiles", [])
    while True:
        action = (
            get_input("Tile action [add/remove/edit/reorder/done]: ")
            .strip()
            .lower()
        )
        if action.startswith("a"):
            show_id = get_input("Show ID: ").strip()
            path = get_input("Path: ").strip()
            if show_id and path:
                tile: Dict[str, object] = {"show_id": show_id, "path": path}
                label = get_input("Label (optional): ").strip()
                if label:
                    tile["label"] = label
                weight = get_input("Weight (default 1): ").strip()
                if weight:
                    try:
                        tile["weight"] = float(weight)
                    except ValueError:
                        logger.error("Invalid weight for %s: %s", show_id, weight)
                tiles.append(tile)
        elif action.startswith("remove"):
            show_id = get_input("Show ID to remove: ").strip()
            tiles[:] = [t for t in tiles if t.get("show_id") != show_id]
        elif action.startswith("edit"):
            show_id = get_input("Show ID to edit: ").strip()
            tile = next((t for t in tiles if t.get("show_id") == show_id), None)
            if not tile:
                continue
            label = get_input(f"Label ({tile.get('label', '')}): ").strip()
            if label:
                tile["label"] = label
            path = get_input(f"Path ({tile.get('path', '')}): ").strip()
            if path:
                tile["path"] = path
            weight = get_input(f"Weight ({tile.get('weight', 1)}): ").strip()
            if weight:
                try:
                    tile["weight"] = float(weight)
                except ValueError:
                    logger.error("Invalid weight for %s: %s", show_id, weight)
        elif action.startswith("reorder"):
            show_id = get_input("Show ID to move: ").strip()
            try:
                new_pos = int(get_input("New position (0-based): ").strip())
            except ValueError:
                logger.error("Invalid position for %s", show_id)
                continue
            idx = next((i for i, t in enumerate(tiles) if t.get("show_id") == show_id), None)
            if idx is None:
                continue
            tile = tiles.pop(idx)
            if new_pos < 0:
                new_pos = 0
            if new_pos > len(tiles):
                new_pos = len(tiles)
            tiles.insert(new_pos, tile)
        else:
            break


def configure(get_input: Callable[[str], str] = _prompt) -> None:
    """Interactively update caregiver configuration settings."""

    cfg = config.load_config()

    manage = get_input(
        f"Manage tiles? [y/n] (current {len(cfg.get('tiles', []))}): "
    ).strip().lower()
    if manage.startswith("y"):
        _manage_tiles(cfg, get_input)

    mode = get_input(
        f"Playback mode [order/random] (current {cfg.get('mode', 'order')}): "
    ).strip().lower()
    if mode in {"order", "random"}:
        cfg["mode"] = mode

    if cfg.get("mode") == "random":
        rand_cfg = cfg.setdefault("random", {})
        cur_ex = int(rand_cfg.get("exclude_last_n", 0))
        resp = get_input(
            f"Exclude last N episodes (current {cur_ex}): "
        ).strip()
        if resp:
            try:
                rand_cfg["exclude_last_n"] = int(resp)
            except ValueError:
                logger.error("Invalid exclude_last_n: %s", resp)

        cur = "y" if rand_cfg.get("use_comfort_weights") else "n"
        use_weights = (
            get_input(f"Use comfort weights? [y/n] (current {cur}): ")
            .strip()
            .lower()
            or cur
        )
        rand_cfg["use_comfort_weights"] = use_weights.startswith("y")
        if rand_cfg["use_comfort_weights"]:
            for tile in cfg.get("tiles", []):
                show_id = tile.get("show_id")
                if not show_id:
                    continue
                current = float(tile.get("weight", 1))
                resp = (
                    get_input(
                        f"Weight for {show_id} (current {current}): "
                    )
                    .strip()
                )
                if resp:
                    try:
                        tile["weight"] = float(resp)
                    except ValueError:
                        logger.error("Invalid weight for %s: %s", show_id, resp)

    history_cfg = cfg.setdefault("history", {})
    cur_limit = int(history_cfg.get("max", 50))
    resp = get_input(
        f"History limit (current {cur_limit}): "
    ).strip()
    if resp:
        try:
            history_cfg["max"] = int(resp)
        except ValueError:
            logger.error("Invalid history limit: %s", resp)

    config.save_config(cfg)
    logger.info("Configuration updated")


def export_config(path: str) -> None:
    """Export current configuration to ``path``."""

    dest = Path(path).expanduser()
    cfg = config.load_config()
    try:
        with dest.open("w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, sort_keys=True)
    except OSError as exc:  # pragma: no cover - depends on fs
        logger.error(f"Failed to export configuration to {dest}: {exc}")
    else:
        logger.info(f"Configuration exported to {dest}")


def import_config(path: str) -> bool:
    """Import configuration from ``path`` and persist it."""

    src = Path(path).expanduser()
    try:
        with src.open("r", encoding="utf-8") as f:
            cfg = json.load(f)
    except (OSError, ValueError) as exc:  # pragma: no cover - depends on fs
        logger.error(f"Failed to import configuration from {src}: {exc}")
        return False
    config.save_config(cfg)
    logger.info(f"Configuration imported from {src}")
    return True


def menu(get_input: Callable[[str], str] = _prompt) -> None:
    """Display a simple graphical caregiver menu."""

    while True:
        choice = _select(
            "Caregiver Menu",
            [
                "Configure settings",
                "Purge playback history",
                "Export configuration",
                "Import configuration",
                "Exit",
            ],
            get_input,
        )
        if choice == 0:
            configure(get_input)
        elif choice == 1:
            show_id = get_input("Show ID to purge (blank for all): ").strip()
            db.purge_history(show_id or None)
            logger.info("Playback history purged")
        elif choice == 2:
            path = get_input("Export path: ").strip()
            if path:
                export_config(path)
        elif choice == 3:
            path = get_input("Import path: ").strip()
            if path:
                import_config(path)
        else:
            break


def main() -> None:
    """Launch the caregiver menu after validating the PIN."""

    if not verify_pin():
        return
    menu()

if __name__ == "__main__":
    main()
