#!/usr/bin/env python3
"""List entries marked for future revisit."""

from __future__ import annotations

import argparse
import sqlite3

from init_db import DEFAULT_DB_PATH, init_db, resolve_db_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db-path", default=str(DEFAULT_DB_PATH), help="SQLite path")
    args = parser.parse_args()

    db_path = resolve_db_path(args.db_path)
    init_db(db_path)
    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT run_date, original_event_date, title, category, confidence
            FROM entries
            WHERE revisit_candidate = 1
            ORDER BY original_event_date, title
            """
        ).fetchall()

    for row in rows:
        print(f"{row[0]} | {row[1]} | {row[3]} | {row[4]} | {row[2]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
