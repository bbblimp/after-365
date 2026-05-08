#!/usr/bin/env python3
"""Coordinate one After 365 run."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sqlite3
from pathlib import Path
from typing import Any

from init_db import DEFAULT_DB_PATH, init_db, resolve_db_path
from render_markdown import write_markdown


SLUG_RE = re.compile(r"[^a-z0-9]+")


def iso_today() -> str:
    return dt.date.today().isoformat()


def lookback_date(run_date: str) -> str:
    value = dt.date.fromisoformat(run_date)
    return (value - dt.timedelta(days=365)).isoformat()


def slugify(value: str) -> str:
    slug = SLUG_RE.sub("-", value.lower()).strip("-")
    return slug or "entry"


def load_input(path: str | None) -> dict[str, Any]:
    if not path:
        return {}
    with Path(path).expanduser().open("r", encoding="utf-8") as handle:
        return json.load(handle)


def upsert_daily_run(
    conn: sqlite3.Connection,
    run_date: str,
    lookback: str,
    status: str,
    summary: str | None,
    notes: str | None,
) -> None:
    conn.execute(
        """
        INSERT INTO daily_runs (run_date, lookback_date, status, daily_summary, notes)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(run_date) DO UPDATE SET
            lookback_date = excluded.lookback_date,
            status = excluded.status,
            daily_summary = COALESCE(excluded.daily_summary, daily_runs.daily_summary),
            notes = COALESCE(excluded.notes, daily_runs.notes),
            updated_at = CURRENT_TIMESTAMP
        """,
        (run_date, lookback, status, summary, notes),
    )


def replace_candidates(conn: sqlite3.Connection, run_date: str, candidates: list[dict[str, Any]]) -> dict[str, int]:
    conn.execute("DELETE FROM candidates WHERE run_date = ?", (run_date,))
    candidate_ids: dict[str, int] = {}
    for item in candidates:
        cursor = conn.execute(
            """
            INSERT INTO candidates (
                run_date, original_event_date, title, category, region, source_hint,
                why_selected, score, status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_date,
                item.get("original_event_date"),
                item["title"],
                item.get("category", "Uncategorized"),
                item.get("region"),
                item.get("source_hint"),
                item.get("why_selected"),
                item.get("score"),
                item.get("status", "candidate"),
            ),
        )
        key = item.get("key") or item.get("slug") or item["title"]
        candidate_ids[str(key)] = int(cursor.lastrowid)
    return candidate_ids


def replace_entries(
    conn: sqlite3.Connection,
    run_date: str,
    lookback: str,
    entries: list[dict[str, Any]],
    candidate_ids: dict[str, int],
) -> None:
    existing = conn.execute("SELECT id FROM entries WHERE run_date = ?", (run_date,)).fetchall()
    for row in existing:
        conn.execute("DELETE FROM sources WHERE entry_id = ?", (row["id"],))
    conn.execute("DELETE FROM entries WHERE run_date = ?", (run_date,))

    used_slugs: set[str] = set()
    for item in entries:
        base_slug = item.get("slug") or slugify(item["title"])
        slug = base_slug
        suffix = 2
        while slug in used_slugs:
            slug = f"{base_slug}-{suffix}"
            suffix += 1
        used_slugs.add(slug)

        candidate_key = item.get("candidate_key")
        candidate_id = candidate_ids.get(str(candidate_key)) if candidate_key is not None else None
        cursor = conn.execute(
            """
            INSERT INTO entries (
                run_date, candidate_id, slug, title, category, region,
                original_event_date, summary_then, summary_now, direct_impacts,
                indirect_impacts, missed_by_original_coverage, one_year_assessment,
                confidence, revisit_candidate
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_date,
                candidate_id,
                slug,
                item["title"],
                item.get("category", "Uncategorized"),
                item.get("region"),
                item.get("original_event_date", lookback),
                item["summary_then"],
                item["summary_now"],
                item.get("direct_impacts"),
                item.get("indirect_impacts"),
                item.get("missed_by_original_coverage"),
                item["one_year_assessment"],
                item.get("confidence", "Medium"),
                1 if item.get("revisit_candidate", True) else 0,
            ),
        )
        entry_id = int(cursor.lastrowid)
        for source in item.get("sources", []):
            conn.execute(
                """
                INSERT INTO sources (entry_id, phase, title, url, publisher, published_date, note)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    entry_id,
                    source["phase"],
                    source.get("title"),
                    source["url"],
                    source.get("publisher"),
                    source.get("published_date"),
                    source.get("note"),
                ),
            )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-date", help="Run date in YYYY-MM-DD format, default: today")
    parser.add_argument("--db-path", default=str(DEFAULT_DB_PATH), help="SQLite path")
    parser.add_argument("--input", help="JSON file containing researched candidates and entries")
    parser.add_argument("--dry-run", action="store_true", help="Create run record and placeholder Markdown only")
    args = parser.parse_args()

    payload = load_input(args.input)
    run_date = args.run_date or payload.get("run_date") or iso_today()
    lookback = lookback_date(run_date)
    db_path = resolve_db_path(args.db_path)
    init_db(db_path)

    candidates = payload.get("candidates", [])
    entries = payload.get("entries", [])
    status = "done" if entries else "partial"
    if args.dry_run and not entries:
        status = "partial"

    summary = payload.get("daily_summary")
    if not summary:
        summary = f"Run initialized for lookback date {lookback}. Final researched entries have not been recorded yet."

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        upsert_daily_run(conn, run_date, lookback, status, summary, payload.get("notes"))
        candidate_ids = replace_candidates(conn, run_date, candidates) if candidates else {}
        if entries:
            replace_entries(conn, run_date, lookback, entries, candidate_ids)
        conn.commit()
        output_path = write_markdown(conn, run_date)

    print(f"{status}: {run_date} -> {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
