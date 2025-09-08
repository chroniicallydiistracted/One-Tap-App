"""Caregiver configuration management entry point.

This script presents a very small dialog driven user interface for managing
the caregiver configuration.  The UI is intentionally minimal so it can run
both inside and outside of Kodi during development.  When executed inside the
Kodi runtime we utilise ``xbmcgui`` for dialogs; otherwise simple ``input`` and
``print`` based fallbacks are used.

Features implemented:

* PIN gated access – the user must enter the PIN stored in ``config.json``.
* Tile curation – add or remove tiles (``show_id``, ``label`` and ``path``).
* Playback mode toggle – switch between ``order`` and ``random`` playback.
* Export / import – write the current configuration to a user supplied path or
  load configuration from a JSON file.

All changes are persisted using :mod:`one_tap.config` helpers.
"""
from __future__ import annotations

import json
from typing import Any, Dict, List

from one_tap import config
from one_tap.logging import get_logger

try:  # pragma: no cover - depends on Kodi
    import xbmc  # type: ignore
    import xbmcgui  # type: ignore
    import xbmcvfs  # type: ignore
except ImportError:  # pragma: no cover - desktop/dev
    xbmc = None  # type: ignore
    xbmcgui = None  # type: ignore
    xbmcvfs = None  # type: ignore

logger = get_logger("script.one_tap.caregiver")


# ---------------------------------------------------------------------------
# Dialog helpers

def _input_dialog(prompt: str, password: bool = False) -> str:
    """Return text entered by the user.

    A wrapper around :class:`xbmcgui.Dialog` with a console fallback.  When
    ``password`` is ``True`` the input is hidden in the Kodi UI.
    """

    if xbmcgui:  # pragma: no branch - runtime check
        dlg = xbmcgui.Dialog()  # type: ignore[unreachable]
        option = xbmcgui.ALPHANUM_HIDE_INPUT if password else 0
        return dlg.input(prompt, option=option)

    # Console fallback
    return input(f"{prompt}: ")


def _select_dialog(title: str, options: List[str]) -> int:
    """Return index of the selected option or ``-1`` if cancelled."""

    if xbmcgui:  # pragma: no branch - runtime check
        return xbmcgui.Dialog().select(title, options)  # type: ignore[unreachable]

    print(title)
    for i, opt in enumerate(options):
        print(f"{i}: {opt}")
    try:
        choice = int(input("Select option: "))
    except Exception:
        return -1
    return choice if 0 <= choice < len(options) else -1


def _yesno_dialog(title: str, message: str) -> bool:
    """Return ``True`` when user selects yes."""

    if xbmcgui:  # pragma: no branch - runtime check
        return xbmcgui.Dialog().yesno(title, message)  # type: ignore[unreachable]

    resp = input(f"{title}: {message} (y/n): ")
    return resp.strip().lower().startswith("y")


def _ok_dialog(title: str, message: str) -> None:
    """Display an informational dialog."""

    if xbmcgui:  # pragma: no branch - runtime check
        xbmcgui.Dialog().ok(title, message)  # type: ignore[unreachable]
    else:
        print(f"{title}: {message}")


# ---------------------------------------------------------------------------
# Menu actions

def _curate_tiles(cfg: Dict[str, Any]) -> None:
    """Allow the user to add or remove tiles."""

    tiles: List[Dict[str, Any]] = cfg.setdefault("tiles", [])
    while True:
        choice = _select_dialog("Tile Curation", ["Add tile", "Remove tile", "Back"])
        if choice == 0:  # Add tile
            show_id = _input_dialog("Show ID")
            label = _input_dialog("Label")
            path = _input_dialog("Path")
            if show_id and label and path:
                if any(t.get("show_id") == show_id for t in tiles):
                    _ok_dialog("Add Tile", "Show ID already exists")
                else:
                    tiles.append({"show_id": show_id, "label": label, "path": path})
                    config.save_config(cfg)
        elif choice == 1:  # Remove tile
            if not tiles:
                _ok_dialog("Remove Tile", "No tiles configured")
                continue
            labels = [t.get("label", "") for t in tiles]
            idx = _select_dialog("Remove which tile?", labels)
            if 0 <= idx < len(tiles) and _yesno_dialog("Confirm", f"Remove {labels[idx]}?"):
                del tiles[idx]
                config.save_config(cfg)
        else:  # Back or cancelled
            return


def _toggle_mode(cfg: Dict[str, Any]) -> None:
    """Toggle global playback mode between 'order' and 'random'."""

    mode = cfg.get("mode", "order")
    new_mode = "random" if mode != "random" else "order"
    if _yesno_dialog("Playback Mode", f"Switch to {new_mode} mode?"):
        cfg["mode"] = new_mode
        config.save_config(cfg)


def _export_config(cfg: Dict[str, Any]) -> None:
    """Write current configuration to a user supplied path."""

    dest = _input_dialog("Export path")
    if not dest:
        return

    try:
        # xbmcvfs handles special paths inside Kodi; fall back to open()
        if xbmcvfs:  # pragma: no branch - runtime check
            with xbmcvfs.File(dest, "w") as f:  # type: ignore[unreachable]
                f.write(json.dumps(cfg, indent=2, sort_keys=True))
        else:
            with open(dest, "w", encoding="utf-8") as f:
                json.dump(cfg, f, indent=2, sort_keys=True)
        _ok_dialog("Export", f"Config exported to {dest}")
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("Export failed: %s", exc)
        _ok_dialog("Export", "Failed to export config")


def _import_config(cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Load configuration from the given path and persist it."""

    src = _input_dialog("Import path")
    if not src:
        return cfg

    try:
        data: Dict[str, Any]
        if xbmcvfs:  # pragma: no branch - runtime check
            with xbmcvfs.File(src) as f:  # type: ignore[unreachable]
                raw = f.read()
            data = json.loads(raw)
        else:
            with open(src, "r", encoding="utf-8") as f:
                data = json.load(f)
        cfg.clear()
        cfg.update(data)
        config.save_config(cfg)
        _ok_dialog("Import", "Configuration imported")
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("Import failed: %s", exc)
        _ok_dialog("Import", "Failed to import config")
    return cfg


# ---------------------------------------------------------------------------
# Main

def _check_pin(cfg: Dict[str, Any]) -> bool:
    """Prompt for the caregiver PIN if one is set."""

    pin = cfg.get("pin", "")
    if not pin:
        return True

    attempt = _input_dialog("Enter PIN", password=True)
    if attempt != pin:
        _ok_dialog("PIN", "Incorrect PIN")
        return False
    return True


def main() -> None:
    cfg = config.load_config()
    logger.debug("Loaded config: %s", cfg)

    if not _check_pin(cfg):
        return

    actions = [
        "Curate tiles",
        "Toggle playback mode",
        "Export config",
        "Import config",
        "Exit",
    ]

    while True:
        choice = _select_dialog("Caregiver Menu", actions)
        if choice == 0:
            _curate_tiles(cfg)
        elif choice == 1:
            _toggle_mode(cfg)
        elif choice == 2:
            _export_config(cfg)
        elif choice == 3:
            cfg = _import_config(cfg)
        else:
            break


if __name__ == "__main__":
    main()

