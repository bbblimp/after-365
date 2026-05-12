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

This renders the daily Markdown output and updates `docs/archive.md`. The archive index is managed between `after365-archive` markers and should list the most recent completed report first. `README.md` should keep only a short link to that full archive.

## Cron

Use `scripts/cron_wrapper.sh` from cron. The wrapper:

- changes into the repository root,
- creates a lockfile in `state/`,
- runs the local Codex CLI with `prompts/cron-agent.md`,
- appends recent topic-diversity context from `scripts/topic_diversity.py`,
- checks for missed dates since the latest completed report and processes them oldest-first,
- commits generated reports plus `docs/archive.md` and pushes that narrow commit to `origin/main`,
- falls back to `scripts/daily_run.py` only if Codex is unavailable,
- writes raw logs under `logs/raw/`.

Example cron entry:

```cron
0 2 * * * /home/blech/git/after-365/scripts/cron_wrapper.sh
```

The auto-publish step stages only `docs/archive.md` and the generated files under `outputs/YYYY/`. It does not stage SQLite databases, raw logs, state payloads, or unrelated local edits.

Disable auto-publish for a run with:

```bash
AFTER365_AUTO_PUBLISH=0 scripts/cron_wrapper.sh
```

By default, catch-up is capped at 14 dates per invocation. Override with:

```bash
AFTER365_CATCHUP_LIMIT=30 scripts/cron_wrapper.sh
```

By default, the topic-diversity guard looks back over the prior 7 run days. Override with:

```bash
AFTER365_DIVERSITY_DAYS=14 scripts/cron_wrapper.sh
```

Preview recent topic warnings for a date:

```bash
python3 scripts/topic_diversity.py --run-date YYYY-MM-DD
```

Preview due dates without running the agent:

```bash
scripts/cron_wrapper.sh --list-missing
```

Smoke-test the agent wiring without doing a full research run:

```bash
scripts/cron_wrapper.sh --smoke-agent
```

Run the old placeholder-only path explicitly:

```bash
scripts/cron_wrapper.sh --python-only --dry-run
```

## Research Input Format

`scripts/daily_run.py --input` accepts JSON with optional `run_date`, `daily_summary`, `candidates`, and `entries` fields. Each entry may include nested `sources`.

See `examples/sample_input.json`.
