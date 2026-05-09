#!/usr/bin/env python3
"""List After 365 run dates that still need completed reports."""

from __future__ import annotations

import argparse
import datetime as dt
import sqlite3

from init_db import DEFAULT_DB_PATH, init_db, resolve_db_path


def date_range(start: dt.date, end: dt.date) -> list[dt.date]:
    days = (end - start).days
    if days < 0:
        return []
    return [start + dt.timedelta(days=offset) for offset in range(days + 1)]


def completed_dates(conn: sqlite3.Connection) -> set[str]:
    rows = conn.execute(
        """
        SELECT daily_runs.run_date
        FROM daily_runs
        JOIN entries ON entries.run_date = daily_runs.run_date
        WHERE daily_runs.status = 'done'
          AND daily_runs.output_path IS NOT NULL
        GROUP BY daily_runs.run_date
        HAVING COUNT(entries.id) > 0
        """
    ).fetchall()
    return {row[0] for row in rows}


def latest_completed_date(conn: sqlite3.Connection) -> dt.date | None:
    row = conn.execute(
        """
        SELECT MAX(daily_runs.run_date)
        FROM daily_runs
        JOIN entries ON entries.run_date = daily_runs.run_date
        WHERE daily_runs.status = 'done'
          AND daily_runs.output_path IS NOT NULL
        GROUP BY daily_runs.run_date
        HAVING COUNT(entries.id) > 0
        ORDER BY daily_runs.run_date DESC
        LIMIT 1
        """
    ).fetchone()
    if row is None or row[0] is None:
        return None
    return dt.date.fromisoformat(row[0])


def missing_dates(conn: sqlite3.Connection, today: dt.date, limit: int | None) -> list[str]:
    latest = latest_completed_date(conn)
    start = today if latest is None else latest + dt.timedelta(days=1)
    completed = completed_dates(conn)
    missing = [day.isoformat() for day in date_range(start, today) if day.isoformat() not in completed]

    if limit is not None and limit > 0:
        return missing[:limit]
    return missing


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db-path", default=str(DEFAULT_DB_PATH), help="SQLite path")
    parser.add_argument("--today", default=dt.date.today().isoformat(), help="Today in YYYY-MM-DD format")
    parser.add_argument("--limit", type=int, default=None, help="Maximum dates to return")
    args = parser.parse_args()

    db_path = resolve_db_path(args.db_path)
    init_db(db_path)
    today = dt.date.fromisoformat(args.today)

    with sqlite3.connect(db_path) as conn:
        for run_date in missing_dates(conn, today, args.limit):
            print(run_date)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
