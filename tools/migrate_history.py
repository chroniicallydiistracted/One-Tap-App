"""Convert legacy JSON playback history to the SQLite database."""
from __future__ import annotations

import json
import sys
from pathlib import Path

# Ensure the one_tap package is importable when running from the repo root
repo_root = Path(__file__).resolve().parents[1]
sys.path.append(str(repo_root / "addons" / "script.module.one_tap" / "lib"))

from one_tap import config, db  # noqa: E402

OLD_JSON_PATH = "special://profile/addon_data/plugin.one_tap.play/progress.json"


def main() -> None:
    src = config._resolve(OLD_JSON_PATH)
    if not src.exists():
        print(f"No legacy history found at {src}")
        return

    with src.open("r", encoding="utf-8") as f:
        data = json.load(f)

    with db._connect() as conn:
        for show_id, episodes in data.items():
            conn.executemany(
                "INSERT INTO history(show_id, episode) VALUES (?, ?)",
                ((show_id, ep) for ep in episodes),
            )
            conn.execute(
                """
                DELETE FROM history
                WHERE show_id=?
                  AND rowid NOT IN (
                    SELECT rowid FROM history WHERE show_id=? ORDER BY rowid DESC LIMIT ?
                  )
                """,
                (show_id, show_id, len(episodes)),
            )

    dest = config._resolve(db.DB_PATH)
    print(f"Migrated history from {src} to {dest}")
   
    try:
        src.unlink()
        print(f"Removed legacy history file {src}")
    except OSError as exc:  # pragma: no cover - defensive
        print(f"Failed to remove legacy history file {src}: {exc}")


if __name__ == "__main__":
    main()

