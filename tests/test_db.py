import json
import sys
from pathlib import Path

# Ensure one_tap package is importable
repo_root = Path(__file__).resolve().parents[1]
sys.path.append(str(repo_root / "addons" / "script.module.one_tap" / "lib"))

from one_tap import config, db


def _fake_resolve(base: Path, path: str) -> Path:
    """Resolve paths within tests to the temporary directory."""
    return base / Path(path).name


def test_update_history_limits_records(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "_resolve", lambda p: _fake_resolve(tmp_path, p))
    monkeypatch.setattr(db, "DB_PATH", "history.db")

    for i in range(60):
        db.update_history("show", f"ep{i}", max_history=50)

    history = db.get_history("show")
    assert len(history) == 50
    assert history[0] == "ep10"
    assert history[-1] == "ep59"


def test_migrate_history(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "_resolve", lambda p: _fake_resolve(tmp_path, p))
    monkeypatch.setattr(db, "DB_PATH", "history.db")

    legacy = {"show": ["a", "b", "c"]}
    (tmp_path / "progress.json").write_text(json.dumps(legacy))

    sys.path.append(str(repo_root))
    from tools import migrate_history

    monkeypatch.setattr(migrate_history, "OLD_JSON_PATH", "progress.json")

    migrate_history.main()
    assert db.get_history("show") == ["a", "b", "c"]

