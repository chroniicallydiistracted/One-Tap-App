"""Minimal JSON-RPC helper for communicating with Kodi."""
from __future__ import annotations

import json
from typing import Any, Dict, Optional

try:  # pragma: no cover - depends on Kodi
    import xbmc  # type: ignore
except ImportError:  # pragma: no cover - desktop/dev
    xbmc = None  # type: ignore


class KodiNotAvailable(RuntimeError):
    """Raised when JSON-RPC is invoked outside the Kodi environment."""


def call(method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Invoke a JSON-RPC ``method`` with optional ``params``."""

    if not xbmc:
        raise KodiNotAvailable("xbmc module not available")

    request = {"jsonrpc": "2.0", "id": 1, "method": method}
    if params:
        request["params"] = params
    response = xbmc.executeJSONRPC(json.dumps(request))
    try:
        return json.loads(response) if response else {}
    except Exception:  # pragma: no cover - defensive
        return {}


def play_file(path: str) -> Dict[str, Any]:
    """Open ``path`` in Kodi's active player."""

    return call("Player.Open", {"item": {"file": path}})
