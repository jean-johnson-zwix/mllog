---
name: logbook
description: >
  Generate an experiment logbook over a time window by reading the local mllog run records.
argument-hint: "[--from <when>] [--to <when>]  e.g. --from yesterday"
allowed-tools: Bash(mllog:*), Read, Glob, Grep
license: MIT
---

# /logbook — generate the logbook

You are the **report step** of the mllog pipeline. Per-run capture has already stored JSON
records locally (via `/mllog` or the automatic Stop hook). This command reads those records over
a time window, synthesizes a written logbook, and renders it as a document.

**Hard rules**

- Read **only** the stored JSON records. Do not run MLflow or git, and do not re-derive
  anything live — capture already froze the facts.
- Every qualitative claim must be grounded in a recorded item (a metric, a diff, an event, or
  a transcript moment). If you can't ground it, don't write it.
- Never invent runs, metrics, or outcomes. Report gaps plainly.

## Inputs

- Time window: `$ARGUMENTS` — e.g. `--from yesterday`, `--from 2026-06-20 --to 2026-06-23`.
- If no window is given, default to **since the last logbook checkpoint**.

## Steps

1. **Resolve the window.** If `$ARGUMENTS` specifies `--from`/`--to`, use it. Otherwise read
   the last-report checkpoint and start from there to now.

2. **Select records** in that window from the local store:
   `mllog get-logs --from <...> --to <...> --json` (read-only).

3. **Synthesize the logbook** from the selected records: what was attempted, what changed, what
   the results show, and what to do next — organized by run/activity. Note each metric's
   source (MLflow vs agent session) where relevant. Ground every claim per the hard rules.

4. **Render the document** deterministically from the records:
   `mllog get-logs --from <...> --to <...> --render --out <path>`. This is a pure projection
   of the JSON.

5. **Advance the checkpoint** so the next default `/logbook` starts where this one ended:
   `mllog checkpoint --advance`.

6. **Report back** concisely: the window covered, how many runs were included, the output
   document location, and any records with missing git/MLflow info.
