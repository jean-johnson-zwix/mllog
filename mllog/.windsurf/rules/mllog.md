# mllog — ML experiment logging

When the user completes a training, evaluation, or analysis run, suggest capturing it:

```bash
mllog capture --type <train|eval|analysis> --status <ok|failed> --auto
```

To generate a logbook report:
```bash
mllog get-logs --from yesterday --render --out logbook.md
```

To query recent runs:
```bash
mllog get-logs --from yesterday --json
```

To check sensor/adapter/sink status:
```bash
mllog doctor
```

**Rules:**
- Record facts only: agent events, git commit, status. Do not invent values.
- If MLflow is present, its sensor captures the run id. If not, skip it — mllog works without it.
- Determine status from the session: errors/crashes = `failed`, otherwise `ok`.
- Classify type from context: model training -> `train`, held-out metrics -> `eval`, inspection/plotting -> `analysis`.
