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
records locally (via `/mllog` or the automatic Stop hook). Your job is to **read those records
and write a narrative logbook** — a document a researcher can read to understand what happened,
what changed, what the results were, and what to do next.

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

2. **Fetch records** in that window:
   `mllog get-logs --from <...> --to <...> --json`

3. **Write the logbook yourself as a markdown file.** This is the core of this skill — YOU
   write the narrative, not the CLI. Structure it as follows:

   ```markdown
   # Experiment Logbook: <from> to <to>

   ## Summary
   A 2-3 sentence overview: how many runs, what was the main thrust of work,
   what was the headline result.

   ## Runs

   ### Run 1: <activity_type> — <status>
   **When:** <started_at>
   **Git:** <commit> (dirty/clean)

   **What was attempted:** Describe what this run did based on the config deltas,
   edited files, and commands. e.g. "Lowered learning rate from 3e-4 to 1e-4 in
   configs/train.yaml and re-ran training for 10 epochs."

   **What changed:** List files edited, config changes, code changes.

   **Results:** Present the metrics in a table. Compare to previous runs if data
   is available. Note the metrics source (MLflow vs agent session).

   **Observations:** Any notable patterns — did accuracy improve? Did the run fail?
   Was comparison safety flagged?

   (repeat for each run)

   ## What's Next
   Based on the trajectory of results, suggest 1-3 concrete next steps.
   Only suggest things grounded in the data.
   ```

   Write this file to `logbook.md` in the project root (or the path specified in arguments).

4. **Advance the checkpoint:**
   `mllog checkpoint --advance`

5. **Report back** concisely: the window covered, how many runs were included, the output
   file location, and any records with missing data.

## Key guidance

- **DO NOT** just run `mllog get-logs --render`. That produces a raw data dump, not a logbook.
  Your value is interpreting the facts into a readable narrative.
- Compare metrics across runs when multiple runs exist in the window.
- If a run has `comparison_safety.safe_for_delta: false`, note that metric comparisons to
  prior runs are unreliable because code or config changed.
- If `events` were captured, use them to describe what the agent did (edits, commands).
- If `config_deltas` exist, call out the specific parameter changes.
- Keep it factual but readable. A researcher should be able to skim this and know what happened.
