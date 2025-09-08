import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parents[1]
sys.path.append(str(repo_root / "addons" / "script.module.one_tap" / "lib"))
sys.path.append(str(repo_root / "addons" / "script.one_tap.caregiver"))


def test_verify_pin(monkeypatch):
    import default as caregiver

    monkeypatch.setattr(caregiver.config, "load_config", lambda: {"pin": "1234"})
    assert caregiver.verify_pin(lambda _prompt: "1234") is True
    assert caregiver.verify_pin(lambda _prompt: "9999") is False


def test_verify_pin_not_set(monkeypatch):
    import default as caregiver

    monkeypatch.setattr(caregiver.config, "load_config", lambda: {"pin": ""})
    called = False

    def fake_prompt(msg: str) -> str:
        nonlocal called
        called = True
        return ""

    assert caregiver.verify_pin(fake_prompt) is True
    assert called is False


def test_configure_updates_weights(monkeypatch):
    import default as caregiver

    cfg = {
        "mode": "order",
        "random": {},
        "tiles": [
            {"show_id": "s1", "weight": 1},
            {"show_id": "s2", "weight": 1},
        ],
    }

    inputs = iter(["n", "random", "5", "y", "1.5", "2.0", ""])

    def fake_input(_prompt: str) -> str:
        return next(inputs)

    saved: dict = {}

    monkeypatch.setattr(caregiver.config, "load_config", lambda: cfg)

    def fake_save(updated: dict) -> None:
        saved.update(updated)

    monkeypatch.setattr(caregiver.config, "save_config", fake_save)

    caregiver.configure(fake_input)

    assert saved["mode"] == "random"
    assert saved["random"]["use_comfort_weights"] is True
    assert saved["random"]["exclude_last_n"] == 5
    assert [t["weight"] for t in saved["tiles"]] == [1.5, 2.0]


def test_configure_manages_tiles_and_history(monkeypatch):
    import default as caregiver

    cfg = {
        "mode": "order",
        "random": {},
        "tiles": [{"show_id": "s1", "path": "p1"}],
        "history": {"max": 50},
    }

    inputs = iter([
        "y",  # manage tiles
        "add",
        "s2",
        "p2",
        "",  # label
        "",  # default weight
        "remove",
        "s1",
        "done",
        "",  # mode unchanged
        "75",  # history limit
    ])

    def fake_input(_prompt: str) -> str:
        return next(inputs)

    saved: dict = {}

    monkeypatch.setattr(caregiver.config, "load_config", lambda: cfg)

    def fake_save(updated: dict) -> None:
        saved.update(updated)

    monkeypatch.setattr(caregiver.config, "save_config", fake_save)

    caregiver.configure(fake_input)

    assert [t["show_id"] for t in saved["tiles"]] == ["s2"]
    assert saved["tiles"][0]["path"] == "p2"
    assert saved["history"]["max"] == 75


def test_manage_tiles_edit_and_reorder(monkeypatch):
    import default as caregiver

    cfg = {
        "mode": "order",
        "random": {},
        "tiles": [
            {"show_id": "s1", "path": "p1", "label": "L1"},
            {"show_id": "s2", "path": "p2", "label": "L2"},
        ],
        "history": {"max": 50},
    }

    inputs = iter([
        "y",  # manage tiles
        "edit",
        "s1",
        "NL1",  # new label
        "p1n",  # new path
        "",  # weight unchanged
        "reorder",
        "s2",
        "0",
        "done",
        "",  # mode unchanged
        "",  # history unchanged
    ])

    def fake_input(_prompt: str) -> str:
        return next(inputs)

    saved: dict = {}

    monkeypatch.setattr(caregiver.config, "load_config", lambda: cfg)

    def fake_save(updated: dict) -> None:
        saved.update(updated)

    monkeypatch.setattr(caregiver.config, "save_config", fake_save)

    caregiver.configure(fake_input)

    assert [t["show_id"] for t in saved["tiles"]] == ["s2", "s1"]
    s1 = next(t for t in saved["tiles"] if t["show_id"] == "s1")
    assert s1["path"] == "p1n"
    assert s1["label"] == "NL1"


def test_menu_runs_selected_actions(monkeypatch):
    import default as caregiver

    called: list[str] = []

    monkeypatch.setattr(
        caregiver, "configure", lambda _inp=None: called.append("config")
    )
    monkeypatch.setattr(
        caregiver.db, "purge_history", lambda _show=None: called.append("purge")
    )

    inputs = iter(["1", "2", "", "3"])

    def fake_input(_prompt: str) -> str:
        return next(inputs)

    caregiver.menu(fake_input)

    assert called == ["config", "purge"]
