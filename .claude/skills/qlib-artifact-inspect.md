---
name: qlib-artifact-inspect
description: Inspect and validate an RD loop artifact directory. Use when checking run status, debugging failures, or summarizing experiment history.
---

# Qlib Artifact Inspector

## Overview

Inspect the `.claude/artifacts/rdloop/<run_id>/` directory structure to verify integrity, summarize progress, and diagnose issues.

## Directory Structure

```
.claude/artifacts/rdloop/<run_id>/
  trace.json              # Experiment history (SSOT)
  round_manifest.json     # Run-level manifest
  round_<N>/
    manifest.json         # Round status + timestamps
    hypothesis.json       # Planner output
    experiment.json       # Experiment specification
    run_result.json       # Backtest results (IC/IR/RankIC)
    feedback.json         # Evaluator output
    implementations/
      source_data.h5      # Market data input (do not modify)
      factor.py           # Generated factor code
      result.h5           # Factor computation result
```

## Inspection Commands

### 1. Run Status Summary

List all rounds with their status:
```bash
for d in .claude/artifacts/rdloop/*/round_*/manifest.json; do
  echo "$(dirname $d): $(python -c "import json; m=json.load(open('$d')); print(m.get('status','unknown'))")"
done
```

### 2. Trace Integrity Check

Verify trace.json matches round directories:
- Number of entries in `trace.json.hist` should match completed rounds
- Each round directory should have all required files for its status

### 3. SOTA Extraction

Find the best-performing experiment:
```python
import json
trace = json.load(open("trace.json"))
for entry in reversed(trace.get("hist", [])):
    if entry.get("feedback", {}).get("decision"):
        print(f"SOTA: Round {entry['round_idx']}")
        break
```

## Validation Rules

| Check | Rule | Severity |
|-------|------|----------|
| trace.json exists | Required for resume | Error |
| manifest.json per round | Required | Error |
| hypothesis.json before experiment.json | Ordering | Warning |
| feedback.json has boolean decision | Schema | Error |
| factor_name is valid Python identifier | Schema | Error |
| No duplicate round directories | Integrity | Error |

## Quick IC Check

Quickly check IC from a round's result.h5:

```bash
# Run as a script file (stdin execution not supported on macOS)
cat > /tmp/calc_ic.py << 'PYEOF'
import multiprocessing
multiprocessing.set_start_method("fork", force=True)
import pandas as pd, numpy as np, json, sys

workspace = sys.argv[1]  # e.g. .claude/artifacts/rdloop/<run_id>/round_0/implementations

result = pd.read_hdf(f"{workspace}/result.h5")
source = pd.read_hdf(f"{workspace}/source_data.h5")

returns = source["close"].groupby(level="instrument").pct_change().shift(-1)
combined = pd.concat([result.rename("factor"), returns.rename("forward_return")], axis=1).dropna()

daily_ic = combined.groupby(level="datetime").apply(
    lambda x: x["factor"].corr(x["forward_return"])
)
daily_rank_ic = combined.groupby(level="datetime").apply(
    lambda x: x["factor"].rank().corr(x["forward_return"].rank())
)

ic_mean = daily_ic.mean()
ic_std = daily_ic.std()
print(f"IC={ic_mean:.4f}  IR={ic_mean/ic_std:.4f}  RankIC={daily_rank_ic.mean():.4f}  IC>0={((daily_ic>0).mean()):.1%}")
PYEOF

python /tmp/calc_ic.py <workspace_path>
```

## macOS Notes

- `multiprocessing.set_start_method("fork", force=True)` is required (macOS defaults to spawn)
- Qlib's D.features() etc. must be run as script files (stdin/heredoc causes multiprocessing errors)
- Simple data covers 2005 through June 2021. Date ranges after 2022 will return an empty DataFrame

## Common Issues

| Symptom | Cause | Fix |
|---------|-------|-----|
| Missing feedback.json | Evaluator failed after max retries | Check manifest.json for schema_failure status |
| Empty run_result.json | Backtest timeout or crash | Re-run with longer timeout |
| Duplicate SOTA entries | Race condition in concurrent writes | Use trace.json as SSOT, ignore manifests |
