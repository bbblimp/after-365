# Agent Instructions: After 365

This repository supports a local-first daily retrospective project. Treat it as an inspectable archive, not a hosted service.

## Core Rules

- Keep the project simple, local, and repository-centered.
- Use SQLite as internal durable state and Markdown as the rendered output layer.
- Do not commit secrets, tokens, API keys, raw logs, caches, local databases, or private machine details.
- Do not push directly to `main` from automation.
- Do not force-push.
- Do not delete historical outputs or remove historical entries unless explicitly asked.
- Do not rewrite `AGENTS.md`, `README.md`, schema documentation, schema implementation, or cron wiring unless explicitly asked.
- Prefer additive, traceable changes.

## Daily Run Rules

- Compute `lookback_date` as exactly 365 days before `run_date`.
- Consider a broad candidate set before selecting final entries.
- Select 3-4 final items for consequence, traceability, diversity, and analytical value.
- Drama alone is not sufficient.
- Store considered candidates, selected entries, and sources in SQLite.
- Render final daily output to `outputs/YYYY/YYYY-MM-DD.md`.
- Update the README archive index when a completed report is added; newest dates go first.
- Keep runs idempotent for a given `run_date`.
- Use lockfile protection for unattended runs.

## Editorial Rules

- Write in a factual, calm, restrained, archival voice.
- Separate established fact, reasonable inference, and uncertainty.
- Do not force dramatic conclusions.
- Treat accidents, deaths, illness, and personal tragedy with restraint.
- A finding that an event faded without lasting impact is valid.

## Git Hygiene

- SQLite databases belong in `data/` and are ignored.
- Lockfiles and transient state belong in `state/` and are ignored except `.gitkeep`.
- Raw runtime logs belong in `logs/raw/` and are ignored.
- Generated Markdown in `outputs/` may be committed after review.
