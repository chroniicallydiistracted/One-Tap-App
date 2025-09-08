import sys
import types
from pathlib import Path

repo_root = Path(__file__).resolve().parents[1]
sys.path.append(str(repo_root / "addons" / "script.module.one_tap" / "lib"))


def test_auto_advance_error(monkeypatch, tmp_path):
    commands = []

    class DummyPlayer:
        def __init__(self, *args, **kwargs):
            pass

        def getPlayingFile(self):
            return str(tmp_path / "show" / "ep1.mkv")

    class DummyMonitor:
        def abortRequested(self):
            return True

        def waitForAbort(self, t):
            return True

    xbmc_stub = types.SimpleNamespace(
        Player=DummyPlayer,
        Monitor=DummyMonitor,
        executebuiltin=lambda cmd: commands.append(cmd),
        log=lambda msg, level: None,
    )

    monkeypatch.setitem(sys.modules, "xbmc", xbmc_stub)
    sys.path.append(str(repo_root / "addons" / "service.one_tap.random"))
    import importlib

    service = importlib.import_module("service")
    monkeypatch.setattr(
        service.config,
        "load_config",
        lambda: {"tiles": [{"show_id": "show", "path": str(tmp_path / "show")}]},
    )
    monkeypatch.setattr(
        service.db, "remove_last_history", lambda s: commands.append(f"remove:{s}")
    )

    player = service.AutoAdvancePlayer()
    player.onPlayBackError()

    assert commands == [
        "remove:show",
        'RunPlugin("plugin://plugin.one_tap.play?show_id=show")',
    ]
