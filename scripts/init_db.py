#!/usr/bin/env python3
"""Initialize the After 365 SQLite database."""

from __future__ import annotations

import argparse
import os
import sqlite3
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = REPO_ROOT / "data" / "after_365.db"

SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS daily_runs (
    run_date TEXT PRIMARY KEY,
    lookback_date TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'started',
    daily_summary TEXT,
    output_path TEXT,
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS candidates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_date TEXT NOT NULL,
    original_event_date TEXT,
    title TEXT NOT NULL,
    category TEXT NOT NULL,
    region TEXT,
    source_hint TEXT,
    why_selected TEXT,
    score REAL,
    status TEXT NOT NULL DEFAULT 'candidate',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (run_date) REFERENCES daily_runs(run_date) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_date TEXT NOT NULL,
    candidate_id INTEGER,
    slug TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    category TEXT NOT NULL,
    region TEXT,
    original_event_date TEXT NOT NULL,
    summary_then TEXT NOT NULL,
    summary_now TEXT NOT NULL,
    direct_impacts TEXT,
    indirect_impacts TEXT,
    missed_by_original_coverage TEXT,
    one_year_assessment TEXT NOT NULL,
    confidence TEXT NOT NULL CHECK (confidence IN ('High','Medium','Low')),
    revisit_candidate INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (run_date) REFERENCES daily_runs(run_date) ON DELETE CASCADE,
    FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_id INTEGER NOT NULL,
    phase TEXT NOT NULL CHECK (phase IN ('then','followup','today')),
    title TEXT,
    url TEXT NOT NULL,
    publisher TEXT,
    published_date TEXT,
    note TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (entry_id) REFERENCES entries(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_candidates_run_date ON candidates(run_date);
CREATE INDEX IF NOT EXISTS idx_entries_run_date ON entries(run_date);
CREATE INDEX IF NOT EXISTS idx_entries_original_event_date ON entries(original_event_date);
CREATE INDEX IF NOT EXISTS idx_entries_category ON entries(category);
CREATE INDEX IF NOT EXISTS idx_sources_entry_id ON sources(entry_id);
"""


def resolve_db_path(value: str | None = None) -> Path:
    raw = value or os.environ.get("AFTER365_DB_PATH") or str(DEFAULT_DB_PATH)
    return Path(raw).expanduser().resolve()


def init_db(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.executescript(SCHEMA_SQL)
        conn.commit()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db-path", help=f"SQLite path, default: {DEFAULT_DB_PATH}")
    args = parser.parse_args()

    db_path = resolve_db_path(args.db_path)
    init_db(db_path)
    print(f"Initialized {db_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
