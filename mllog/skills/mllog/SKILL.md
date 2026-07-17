---
name: mllog
description: >
  Capture the run that just completed as a JSON record in the local mllog store
  (agent events, git state, optional MLflow).
argument-hint: "[train|eval|analysis]"
allowed-tools: Bash(mllog:*), Bash(git:*), Read, Glob, Grep
license: MIT
---

# /mllog — capture this run

You are the **capture step** of the mllog pipeline. mllog is an external observer that
documents experiments alongside this coding agent — it records, it does not replace anything.
This command runs after a run (training, evaluation, or analysis) and writes **one JSON record**
of that run to the local store. It does NOT write narrative or a logbook — that is `/logbook`'s
job.

**Hard rules**

- Store **facts only**: agent events, git commit info, optional MLflow info, type, and status.
  Do not synthesize prose here.
- Never invent values. If something isn't available (e.g. no MLflow, no commit), its key will
  be **absent** from the record rather than null or guessed.
- MLflow is **optional**. Capture must succeed without it.

## Inputs

- Requested activity type: `$ARGUMENTS` (`train`, `eval`, or `analysis`; may be empty).

## Steps

1. **Determine the activity type.** Use `$ARGUMENTS` if given; otherwise classify from the
   session: model training -> `train`; metrics on a held-out set -> `eval`;
   inspecting/plotting/explaining without a new run -> `analysis`.

2. **Determine the status** (`ok` | `failed`) from the session — errors, crashes, or
   aborted runs mean `failed`. If `failed`, note the likely cause from the evidence.

3. **Write the run record** to the local store via the CLI. The capture command automatically
   gathers git info, agent events, and optional MLflow data via sensors:
   `mllog capture --type <type> --status <status>`.

   If you have the session JSONL path, pass it:
   `mllog capture --type <type> --status <status> --session-path <path>`.

4. **Confirm** briefly: type, status, whether git and MLflow info were present, and the
   record location. Flag anything missing rather than filling it in.
