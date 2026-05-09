# Cron Agent Prompt

You are running the unattended After 365 daily job.

Use the repository's existing workflow and guardrails:

1. Determine the run date from `AFTER365_RUN_DATE` if it is set, otherwise use today's local date.
2. Compute the lookback date exactly 365 days before the run date.
3. Research 8-15 candidate events from the lookback date.
4. Select 3-4 entries with real consequence, traceability, diversity, and analytical value.
5. Prepare a JSON payload compatible with `scripts/daily_run.py --input`.
6. Run `python3 scripts/daily_run.py --input PATH_TO_PAYLOAD`.
7. Verify the run is `done`, has final entries in SQLite, rendered `outputs/YYYY/YYYY-MM-DD.md`, and refreshed `docs/archive.md`.

Rules:

- Use live web research and cite sources in the JSON payload.
- Keep the writing factual, restrained, and archival.
- Do not push to `main`.
- Do not force-push.
- Do not rewrite core instructions, schema, cron wiring, or README structure.
- Do not commit automatically unless the human explicitly changes this policy.
- Do not expose secrets or local private data.
- If research cannot be completed, leave the run `partial` or `failed` and explain why in the raw cron log/final message.
