---
name: logbook
description: >
  Generate a PDF experiment report over a time window by reading the local mllog run records.
argument-hint: "[--from <when>] [--to <when>]  e.g. --from yesterday"
allowed-tools: mcp__plugin_mllog_mllog__mllog_query, mcp__plugin_mllog_mllog__mllog_get_record, Bash(mllog-python:*), Bash(git:*), Read, Write, Glob, Grep
license: MIT
---

# /logbook — generate a PDF experiment report

You are the **report step** of the mllog pipeline. Per-run capture has already stored JSON
records locally (via `/mllog` or the automatic Stop hook). Your job is to **read those records
and generate a professional PDF report** using reportlab — a document a researcher can read to
understand what happened, what changed, what the results were, and what to do next.

**Hard rules**

- Read **only** the stored JSON records. Do not run MLflow or git, and do not re-derive
  anything live — capture already froze the facts.
- Every qualitative claim must be grounded in a recorded item (a metric, a diff, an event, or
  a transcript moment). If you can't ground it, don't write it.
- Never invent runs, metrics, or outcomes. Report gaps plainly.
- **DO NOT** just run `mllog get-logs --render`. That produces a mechanical data dump, not a
  report. Your value is analyzing and interpreting the facts into a readable narrative.

## Inputs

- Time window: `$ARGUMENTS` — e.g. `--from yesterday`, `--from 2026-06-20 --to 2026-06-23`.
- If no window is given, default to **since the last logbook checkpoint**.

## Steps

1. **Resolve the window.** If `$ARGUMENTS` specifies `--from`/`--to`, use it. Otherwise read
   the last-report checkpoint (`mllog checkpoint --show`) and start from there to now.

2. **Fetch records** using the `mllog_query` tool with the resolved `from_when` and `to_when`.
   Parse the returned JSON array of records.

3. **Analyze the records.** Read each record's sources deeply:
   - `sources.agent`: edit_ledger (files touched, churn), config_deltas (parameter changes),
     commands (what was run, exit codes), event_count
   - `sources.git`: commit hash, dirty state, changed files
   - `sources.mlflow`: run_id, params, metrics (if present)
   - `sources.env`: python version, platform
   - `digest`: summary and evidence-backed claims (if present)
   - `transcript_ref`: pointer to full session log (read it for context if available)

   Use `mllog_get_record` to fetch individual record details if the query result is truncated.

4. **Write a Python script that generates the PDF using reportlab.** Save the script to
   `./mllog/.logbook_gen.py` and run it with the project's Python.

   The script should:
   - Read the records JSON (pass the JSON output from step 2 as a file or inline)
   - Build a reportlab `SimpleDocTemplate` with `Paragraph`, `Table`, `Spacer`, etc.
   - Save the PDF to `./mllog/logbooks/<from>_<to>.pdf`

   ### reportlab patterns

   ```python
   import json, io
   from pathlib import Path
   from reportlab.lib import colors
   from reportlab.lib.pagesizes import letter
   from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
   from reportlab.lib.units import inch
   from reportlab.platypus import (
       SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
       PageBreak, ListFlowable, ListItem,
   )

   # Page setup
   doc = SimpleDocTemplate(
       str(output_path),
       pagesize=letter,
       leftMargin=0.75*inch, rightMargin=0.75*inch,
       topMargin=0.75*inch, bottomMargin=0.75*inch,
   )
   styles = getSampleStyleSheet()

   # Useful custom styles
   s_title = ParagraphStyle("Title", parent=styles["Title"], fontSize=20, spaceAfter=6)
   s_h1 = ParagraphStyle("H1", parent=styles["Heading1"], fontSize=16, spaceBefore=16)
   s_h2 = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=13, spaceBefore=12)
   s_body = ParagraphStyle("Body", parent=styles["Normal"], fontSize=10, leading=14)
   s_mono = ParagraphStyle("Mono", fontName="Courier", fontSize=8, leading=10)
   s_caption = ParagraphStyle("Caption", parent=styles["Normal"], fontSize=8,
                               textColor=colors.grey, spaceAfter=8)

   # Tables — use for metrics, comparisons, config deltas
   data = [["Metric", "Value", "Delta"], ["val_loss", "0.38", "-0.07"]]
   t = Table(data, colWidths=[2*inch, 1.5*inch, 1*inch])
   t.setStyle(TableStyle([
       ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
       ("FONTSIZE", (0, 0), (-1, -1), 9),
       ("BACKGROUND", (0, 0), (-1, 0), colors.Color(0.93, 0.93, 0.93)),
       ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
       ("TOPPADDING", (0, 0), (-1, -1), 3),
       ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
   ]))

   # Build story list, then: doc.build(story)
   ```

   ### Report structure

   Adapt the structure to the data — a single session doesn't need "phases"; ten sessions
   across three approaches need phase grouping and cross-comparison.

   **Sections to include (when data warrants):**

   - **Title page / header:** "Experiment Report: \<from\> to \<to\>"
   - **Overview:** 2-4 sentence executive summary — goal, session count, headline result
   - **Phase sections** (group related sessions):
     - What was attempted (from config_deltas, edited files, commands)
     - Changes made (specific parameter changes, code edits, git state)
     - Results table (metrics, comparison to prior runs)
     - Analysis (what worked, what didn't, why)
   - **Cross-session comparison table** (if multiple runs with comparable metrics)
   - **Failure analysis** (for failed sessions: what went wrong, root cause, resolution)
   - **Key findings** (numbered, evidence-grounded)
   - **Recommendations** (1-3 concrete next steps supported by data)

5. **Run the script:**
   `mllog-python ./mllog/.logbook_gen.py`

6. **Clean up** the generator script: delete `./mllog/.logbook_gen.py`

7. **Advance the checkpoint:**
   `mllog checkpoint --advance`

8. **Report back** concisely: the window covered, how many sessions were included, the output
   file location, and a one-line summary of the headline finding.

## Quality bar

Think of a document a PI or collaborator could read to understand the full arc of
experimentation without looking at code. Rich tables, clear analysis, honest about what
worked and what didn't. Dense with evidence, light on filler.

## Key guidance

- **Group sessions into phases** when the work has a logical arc (baseline → tuning → evaluation).
- **Compare metrics across runs** in tables. Tables are your friend.
- **Explain failures honestly.** Failed attempts are valuable data.
- If `config_deltas` exist, call out specific parameter changes and their impact on results.
- If `transcript_ref` points to a session log, read it for additional context.
- Use `PageBreak()` between major sections for readability.
- Use color sparingly: green for improvements, red for regressions, grey for neutral.
