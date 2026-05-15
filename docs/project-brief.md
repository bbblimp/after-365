# Project Brief: After 365

After 365 generates a daily retrospective analysis of events from exactly 365 days earlier.

The project examines the gap between immediate media attention and real consequences one year later. Each day, it looks back 365 days, identifies candidate events, selects a quality-based set of analytically strong items, researches the following year, stores structured results locally, renders Markdown, and preserves state for later revisits.

## Principles

- Local-first Linux project.
- Dedicated git repository.
- SQLite-backed internal memory.
- Markdown outputs for human browsing.
- Cron-safe automation with lockfile protection.
- Public-safe tracked files.

## Non-Goals

Do not build a full web application, complex backend service, large ORM-heavy architecture, distributed system, or heavy dependency stack unless the project later clearly needs it.

Prefer small, robust, inspectable tooling.
