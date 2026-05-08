# SQLite Schema

SQLite is the internal source of truth. Markdown is rendered output.

The default database path is:

```text
data/after_365.db
```

## Tables

- `daily_runs`: one row per daily run, including dates, status, summary, and output path.
- `candidates`: the wider set of events considered before final selection.
- `entries`: final selected items and their one-year-later analysis.
- `sources`: structured source references attached to final entries.

## Schema SQL

```sql
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
```

## Useful Queries

Final entries for a day:

```sql
SELECT title, category, confidence
FROM entries
WHERE run_date = '2026-04-10'
ORDER BY category, title;
```

Revisit candidates:

```sql
SELECT run_date, original_event_date, title
FROM entries
WHERE revisit_candidate = 1
ORDER BY original_event_date;
```

Considered but dropped candidates:

```sql
SELECT run_date, title, category, why_selected
FROM candidates
WHERE status = 'dropped'
ORDER BY run_date DESC;
```
