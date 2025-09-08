"""Caregiver helper script providing basic configuration management."""
from __future__ import annotations

from typing import Callable

from one_tap import config
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

def configure(get_input: Callable[[str], str] = _prompt) -> None:
    """Interactively update caregiver configuration settings."""

    cfg = config.load_config()
    mode = get_input(
        f"Playback mode [order/random] (current {cfg.get('mode', 'order')}): "
    ).strip().lower()
    if mode in {"order", "random"}:
        cfg["mode"] = mode

    if cfg.get("mode") == "random":
        rand_cfg = cfg.setdefault("random", {})
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

    config.save_config(cfg)
    logger.info("Configuration updated")


def main() -> None:
    """Launch the caregiver menu after validating the PIN."""

    if not verify_pin():
        return
    configure()

    if not verify_pin():
        return
    logger.info("Caregiver menu not yet implemented")

if __name__ == "__main__":
    main()
