# After 365

After 365 is a local-first archive that looks back exactly 365 days and asks what remained.

The project generates daily retrospective analyses of events from one year earlier. It is not a normal news digest. The point is to compare immediate public attention with longer-term consequence: which stories mattered, which faded, which predictions held, and which effects only became visible later.

## Archive

See [docs/archive.md](docs/archive.md) for the complete list of handled dates.

## How It Works

Each daily run should:

1. compute today's date and the lookback date 365 days earlier,
2. gather a broader candidate set of events from that lookback date,
3. select 3-4 analytically strong items,
4. store structured state in local SQLite,
5. render a readable Markdown report under `outputs/YYYY/YYYY-MM-DD.md`,
6. update `docs/archive.md` with newest handled dates first,
7. catch up missed dates after local downtime,
8. preserve enough identity and context to revisit entries after 730 or 1095 days.

SQLite is the internal source of truth. Markdown is the published, browsable output layer.

## Repository Layout

```text
.
├── docs/                 Stable project documentation
├── prompts/              Reusable operating prompts
├── scripts/              Local tooling and cron entrypoints
├── outputs/              Generated Markdown reports
├── examples/             Example report shape
├── data/                 Local SQLite files, ignored by git
├── state/                Lockfiles and transient run state
├── todo/                 Human-readable backlog
└── logs/                 Curated project journal and ignored raw logs
```

## Quick Start

Initialize the local database:

```bash
python3 scripts/init_db.py
```

Run a dry daily pass without researched entries:

```bash
python3 scripts/daily_run.py --dry-run
```

Render an existing run:

```bash
python3 scripts/render_markdown.py --run-date YYYY-MM-DD
```

The database defaults to `data/after_365.db`. You can override this with `--db-path` or the `AFTER365_DB_PATH` environment variable.

## Automation

Cron should call `scripts/cron_wrapper.sh`, not the Python script directly. The wrapper sets a predictable working directory, creates a lockfile, runs the local Codex agent with `prompts/cron-agent.md`, catches up missed dates oldest-first, and writes raw logs under `logs/raw/`.

The automation must not push directly to `main`. Daily runs may update the working tree or create reviewable local commits/branches, but publishing remains an explicit human action.

Preview due dates without running the agent:

```bash
scripts/cron_wrapper.sh --list-missing
```

See [docs/operations.md](docs/operations.md) for cron setup, smoke tests, and catch-up controls.

## Safety

This repository is designed to be public-safe:

- do not commit SQLite databases, caches, raw logs, secrets, API keys, or local machine details,
- commit generated Markdown outputs when they are ready for review,
- keep core instructions, schema, and cron wiring stable unless explicitly asked to change them,
- make daily runs idempotent and lock-protected.
