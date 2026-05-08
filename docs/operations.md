# Operations

## Manual Run

Initialize the database:

```bash
python3 scripts/init_db.py
```

Run a dry pass:

```bash
python3 scripts/daily_run.py --dry-run
```

Run with prepared research data:

```bash
python3 scripts/daily_run.py --input path/to/research.json
```

## Cron

Use `scripts/cron_wrapper.sh` from cron. The wrapper:

- changes into the repository root,
- creates a lockfile in `state/`,
- runs `scripts/daily_run.py`,
- writes raw logs under `logs/raw/`.

Example cron entry:

```cron
15 7 * * * /home/blech/git/after-365/scripts/cron_wrapper.sh
```

Review the generated Markdown and git diff before committing or publishing.

## Research Input Format

`scripts/daily_run.py --input` accepts JSON with optional `run_date`, `daily_summary`, `candidates`, and `entries` fields. Each entry may include nested `sources`.

See `examples/sample_input.json`.
