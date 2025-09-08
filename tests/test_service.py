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
    importlib.reload(service)
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


def test_weighted_selection(monkeypatch, tmp_path):
    commands = []

    class DummyPlayer:
        def __init__(self, *args, **kwargs):
            pass

        def getPlayingFile(self):
            return str(tmp_path / "A" / "ep1.mkv")

    xbmc_stub = types.SimpleNamespace(
        Player=DummyPlayer,
        Monitor=lambda: None,
        executebuiltin=lambda cmd: commands.append(cmd),
        log=lambda msg, level: None,
    )

    monkeypatch.setitem(sys.modules, "xbmc", xbmc_stub)
    sys.path.append(str(repo_root / "addons" / "service.one_tap.random"))
    import importlib

    service = importlib.import_module("service")
    importlib.reload(service)
    monkeypatch.setattr(
        service.config,
        "load_config",
        lambda: {
            "tiles": [
                {"show_id": "A", "path": str(tmp_path / "A"), "weight": 1},
                {"show_id": "B", "path": str(tmp_path / "B"), "weight": 3},
            ],
            "random": {"use_comfort_weights": True},
        },
    )
    monkeypatch.setattr(service.random, "choices", lambda ids, weights, k: [ids[0]])

    player = service.AutoAdvancePlayer()
    player._play_next()

    assert commands == [
        'RunPlugin("plugin://plugin.one_tap.play?show_id=B")',
    ]