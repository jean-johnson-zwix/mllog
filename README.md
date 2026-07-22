# mllog — Claude Code Plugin

Automatic experiment logging for ML coding sessions.

## What it does

- **Stop hook** — auto-captures a run record (agent events, git state, session transcript ref)
- `/mllog` — manually capture a run
- `/logbook` — generate a PDF experiment report from stored records

## Prerequisites

```bash
pip install multimodal-mllog
```

The `mllog` CLI must be on PATH (installed via pip in your project's venv).

## Install the plugin

```
/plugin marketplace add jean-johnson-zwix/mllog
/plugin install mllog@mllog
```

## Usage

1. Start a Claude Code session in your ML project.
2. Do your work (train, eval, analyze).
3. When the session ends, the Stop hook captures a record with git state + agent events.
4. Run `/logbook --from yesterday` to generate a report.

## Storage

Records are stored locally at `./mllog/records/<YYYY-MM-DD>.jsonl`.
Override with the `MLLOG_DIR` environment variable.
