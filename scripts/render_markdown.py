#!/usr/bin/env python3
"""Render an After 365 daily run from SQLite to Markdown."""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

from init_db import DEFAULT_DB_PATH, init_db, resolve_db_path


REPO_ROOT = Path(__file__).resolve().parents[1]


def fetch_run(conn: sqlite3.Connection, run_date: str) -> sqlite3.Row:
    row = conn.execute(
        "SELECT * FROM daily_runs WHERE run_date = ?",
        (run_date,),
    ).fetchone()
    if row is None:
        raise SystemExit(f"No daily run found for {run_date}")
    return row


def fetch_entries(conn: sqlite3.Connection, run_date: str) -> list[sqlite3.Row]:
    return list(
        conn.execute(
            "SELECT * FROM entries WHERE run_date = ? ORDER BY id",
            (run_date,),
        )
    )


def fetch_sources(conn: sqlite3.Connection, entry_id: int) -> list[sqlite3.Row]:
    return list(
        conn.execute(
            "SELECT * FROM sources WHERE entry_id = ? ORDER BY phase, id",
            (entry_id,),
        )
    )


def section(title: str, body: str | None) -> str:
    return f"### {title}\n{body or 'No detail recorded.'}\n"


def render_run(conn: sqlite3.Connection, run_date: str) -> tuple[str, Path]:
    run = fetch_run(conn, run_date)
    entries = fetch_entries(conn, run_date)
    year = run_date[:4]
    output_path = REPO_ROOT / "outputs" / year / f"{run_date}.md"

    lines = [
        f"# After 365 - {run_date}",
        "",
        "## Daily Summary",
        "",
        run["daily_summary"] or "No daily summary recorded yet.",
        "",
        "---",
        "",
    ]

    if not entries:
        lines.extend(
            [
                "## No Final Entries Recorded",
                "",
                f"This run currently records the lookback date as {run['lookback_date']}, but no final entries have been added.",
                "",
            ]
        )

    for index, entry in enumerate(entries, start=1):
        lines.extend(
            [
                f"## {index}. {entry['title']}",
                "",
                f"**Original date:** {entry['original_event_date']}",
                f"**Type:** {entry['category']}",
                f"**Confidence:** {entry['confidence']}",
                "",
                section("Then", entry["summary_then"]),
                section("State after 365 days", entry["summary_now"]),
                section("Direct impacts", entry["direct_impacts"]),
                section("Indirect impacts", entry["indirect_impacts"]),
                section("What original coverage missed", entry["missed_by_original_coverage"]),
                section("One-year assessment", entry["one_year_assessment"]),
            ]
        )

        sources = fetch_sources(conn, entry["id"])
        if sources:
            lines.extend(["### Sources", ""])
            for source in sources:
                details = []
                if source["publisher"]:
                    details.append(source["publisher"])
                if source["published_date"]:
                    details.append(source["published_date"])
                suffix = f" ({', '.join(details)})" if details else ""
                label = source["title"] or source["url"]
                lines.append(f"- {source['phase']}: [{label}]({source['url']}){suffix}")
            lines.append("")

        lines.extend(["---", ""])

    return "\n".join(lines).rstrip() + "\n", output_path


def write_markdown(conn: sqlite3.Connection, run_date: str) -> Path:
    markdown, output_path = render_run(conn, run_date)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(markdown, encoding="utf-8")
    rel_path = output_path.relative_to(REPO_ROOT).as_posix()
    conn.execute(
        """
        UPDATE daily_runs
        SET output_path = ?, updated_at = CURRENT_TIMESTAMP
        WHERE run_date = ?
        """,
        (rel_path, run_date),
    )
    conn.commit()
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-date", required=True, help="Run date in YYYY-MM-DD format")
    parser.add_argument("--db-path", default=str(DEFAULT_DB_PATH), help="SQLite path")
    args = parser.parse_args()

    db_path = resolve_db_path(args.db_path)
    init_db(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        output_path = write_markdown(conn, args.run_date)
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
