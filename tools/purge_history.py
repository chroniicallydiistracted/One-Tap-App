"""Purge playback history from the SQLite database."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure the one_tap package is importable when running from the repo root
repo_root = Path(__file__).resolve().parents[1]
sys.path.append(str(repo_root / "addons" / "script.module.one_tap" / "lib"))

from one_tap import db  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Remove playback history")
    parser.add_argument("show_id", nargs="?", help="Optional show ID to purge")
    args = parser.parse_args()
    db.purge_history(args.show_id)
    if args.show_id:
        print(f"Purged history for {args.show_id}")
    else:
        print("Purged history for all shows")


if __name__ == "__main__":
    main()
