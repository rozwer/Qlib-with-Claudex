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
    run_result.json       # Backtest results
    feedback.json         # Evaluator output
    implementations/
      factor.py           # Generated factor code
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

## Common Issues

| Symptom | Cause | Fix |
|---------|-------|-----|
| Missing feedback.json | Evaluator failed after max retries | Check manifest.json for schema_failure status |
| Empty run_result.json | Backtest timeout or crash | Re-run with longer timeout |
| Duplicate SOTA entries | Race condition in concurrent writes | Use trace.json as SSOT, ignore manifests |
