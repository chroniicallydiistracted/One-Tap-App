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
