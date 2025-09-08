"""Caregiver helper script with basic PIN verification."""
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


def main() -> None:
    """Launch the caregiver menu after validating the PIN."""

    if not verify_pin():
        return
    logger.info("Caregiver menu not yet implemented")

if __name__ == "__main__":
    main()
