#!/usr/bin/env python3
"""Show recent After 365 topics and flag repeated themes."""

from __future__ import annotations

import argparse
import datetime as dt
import re
import sqlite3
from collections import Counter, defaultdict

from init_db import DEFAULT_DB_PATH, init_db, resolve_db_path


ENTITY_PATTERNS = {
    "Pope Leo XIV": re.compile(r"\bpope\s+leo\b|\bleo\s+xiv\b", re.I),
    "Donald Trump": re.compile(r"\btrump\b", re.I),
    "China / U.S.-China trade": re.compile(r"\bchina\b|\bu\.?s\.?-china\b|\btariff\b", re.I),
    "Russia / Ukraine war": re.compile(r"\brussia\b|\bukraine\b|\bputin\b|\bzelensky", re.I),
    "India / Pakistan": re.compile(r"\bindia\b|\bpakistan\b|\bkashmir\b", re.I),
    "Gaza / Israel / Hamas": re.compile(r"\bgaza\b|\bisrael\b|\bhamas\b|\bhostage\b", re.I),
}


def since_date(run_date: str, days: int) -> str:
    current = dt.date.fromisoformat(run_date)
    return (current - dt.timedelta(days=days)).isoformat()


def rows_for_window(conn: sqlite3.Connection, run_date: str, days: int) -> list[sqlite3.Row]:
    return list(
        conn.execute(
            """
            SELECT run_date, title, category, region
            FROM entries
            WHERE run_date >= ?
              AND run_date < ?
            ORDER BY run_date DESC, id
            """,
            (since_date(run_date, days), run_date),
        )
    )


def entity_hits(row: sqlite3.Row) -> list[str]:
    text = " ".join(str(row[key] or "") for key in ("title", "category", "region"))
    return [name for name, pattern in ENTITY_PATTERNS.items() if pattern.search(text)]


def render_context(conn: sqlite3.Connection, run_date: str, days: int) -> str:
    rows = rows_for_window(conn, run_date, days)
    lines = [
        "# Recent Topic Diversity Context",
        "",
        f"Run date under consideration: {run_date}",
        f"Lookback window: previous {days} run days",
        "",
    ]

    if not rows:
        lines.append("No recent completed entries found.")
        return "\n".join(lines) + "\n"

    category_counts = Counter(row["category"] for row in rows)
    entity_counts: Counter[str] = Counter()
    by_entity: dict[str, list[sqlite3.Row]] = defaultdict(list)
    for row in rows:
        for entity in entity_hits(row):
            entity_counts[entity] += 1
            by_entity[entity].append(row)

    lines.extend(
        [
            "## Selection Guidance",
            "",
            "- Prefer topics, regions, institutions, and protagonists not represented below.",
            "- Avoid repeating the same named person, war, bilateral dispute, or policy area within this window unless it is clearly one of the day's highest-consequence events.",
            "- If repetition is unavoidable, choose a substantially different angle and explain why it clears the exception.",
            "- Aim for category diversity across the final 3-4 entries.",
            "",
            "## Recent Entries",
            "",
        ]
    )

    for row in rows:
        lines.append(f"- {row['run_date']}: {row['title']} [{row['category']}]")

    lines.extend(["", "## Repetition Warnings", ""])
    repeated_entities = {name: count for name, count in entity_counts.items() if count >= 2}
    repeated_categories = {name: count for name, count in category_counts.items() if count >= 2}

    if not repeated_entities and not repeated_categories:
        lines.append("- No repeated entities or categories detected in this window.")
    else:
        for entity, count in sorted(repeated_entities.items(), key=lambda item: (-item[1], item[0])):
            examples = "; ".join(f"{row['run_date']} {row['title']}" for row in by_entity[entity][:3])
            lines.append(f"- Avoid repeating `{entity}` unless there is a major-event exception ({count} recent entries: {examples}).")
        for category, count in sorted(repeated_categories.items(), key=lambda item: (-item[1], item[0])):
            lines.append(f"- Category `{category}` appears {count} times recently; prefer a different category if the evidence supports it.")

    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-date", required=True, help="Run date in YYYY-MM-DD format")
    parser.add_argument("--db-path", default=str(DEFAULT_DB_PATH), help="SQLite path")
    parser.add_argument("--days", type=int, default=7, help="Prior run-day window")
    args = parser.parse_args()

    db_path = resolve_db_path(args.db_path)
    init_db(db_path)

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        print(render_context(conn, args.run_date, args.days), end="")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
