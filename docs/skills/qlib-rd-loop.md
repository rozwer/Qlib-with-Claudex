---
name: qlib-rd-loop
description: Run the Qlib factor R&D loop — propose hypotheses, generate code, backtest, evaluate. Use when asked to run factor experiments or start the RD loop.
---

# Qlib Factor R&D Loop

Run an automated research-and-development loop for quantitative factor discovery using Qlib.

## Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| scenario | factor | Fixed to factor for Phase 1 |
| rounds | 5 | Number of experiment rounds |
| run_id | auto-generated | Unique run identifier |
| artifact_dir | `.claude/artifacts/rdloop/<run_id>/` | Output directory |

## Flow

### 1. Initialize

- Check if `artifact_dir/trace.json` exists
  - YES → Resume: load trace and determine next round
  - NO → Fresh start: create run directory with `create_run_dir()`

### 2. Round Loop (repeat for N rounds)

For each round `i`:

#### a. Generate TraceView
Build a compressed summary of past experiments using `build_trace_view(trace)`.

#### b. Plan (Planner subagent)
Invoke the Planner to generate:
- `round_<i>/hypothesis.json` — the factor hypothesis
- `round_<i>/experiment.json` — the experiment specification

The Planner receives the TraceView and scenario description. It must:
- Avoid repeating failed hypotheses
- Propose a novel, testable factor
- Output valid JSON matching the schema

#### c. Implement (Codex with qlib-factor-implement skill)
Delegate to Codex to generate `round_<i>/implementations/factor.py` based on:
- The factor specification from experiment.json
- The qlib-factor-implement skill guidelines

#### d. Run Backtest
Execute via Bash:
```bash
cd <workspace_path> && python factor.py
```
Capture stdout/stderr. Save `round_<i>/run_result.json`.

#### e. Evaluate (Evaluator subagent)
Invoke the Evaluator with:
- run_result.json metrics
- Hypothesis context
- SOTA baseline (from TraceView)
- Code change summary (NOT source code)

Output: `round_<i>/feedback.json` with decision (bool) and reasoning.

#### f. Update State
- Update `round_<i>/manifest.json` with status and timestamps
- Append to `trace.json` hist with experiment_ref and feedback_ref
- Display round summary to user

### 3. Final Report
After all rounds, display:
- Table of all rounds: hypothesis, key metrics, decision
- Final SOTA details
- Suggestions for future exploration

## Resume Protocol

If `trace.json` exists with partial history:
1. Determine the last completed round from `round_manifest.json`
2. Check which step was last completed using `manifest.json` step_idx
3. Resume from the next incomplete step

## Error Handling

| Error | Action |
|-------|--------|
| Planner schema failure (3x) | Skip round, log to manifest |
| Codex syntax error | Run fails → Evaluator sees status=failed |
| Backtest timeout | status=timeout in run_result.json |
| Evaluator schema failure (3x) | Skip evaluation, decision=false |
