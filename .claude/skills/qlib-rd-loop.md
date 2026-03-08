---
name: qlib-rd-loop
description: Run the Qlib factor R&D loop — propose hypotheses, generate code, backtest, evaluate. Use when asked to run factor experiments or start the RD loop.
---

# Qlib Factor R&D Loop

Orchestrator for the automated factor discovery loop.
Each step is delegated to a subagent (Agent tool).

## Subagent Configuration

| Step | Subagent | Definition |
|------|----------|------------|
| Hypothesis generation + experiment design | Planner | `.claude/subagents/planner.md` |
| Code generation | Coder | `.claude/subagents/coder.md` |
| Backtest execution | _(Bash directly)_ | `python factor.py` |
| Result evaluation | Evaluator | `.claude/subagents/evaluator.md` |

## Settings

| Parameter | Default | Description |
|-----------|---------|-------------|
| scenario | factor | Fixed to factor for Phase 1 |
| rounds | 5 | Number of experiment rounds |
| run_id | auto-generated | Unique run ID |
| artifact_dir | `.claude/artifacts/rdloop/<run_id>/` | Output directory |

## Prerequisites

### Preparing Qlib Data

```bash
# Install Qlib-with-Claudex into the RD-Agent venv (using uv)
cd RD-Agent-with-Claudex
uv pip install -e ../Qlib-with-Claudex/

# Fetch CSI300 Simple data (~50MB, 2005-2021, 714 stocks)
cd ../Qlib-with-Claudex/scripts
python get_data.py qlib_data --name qlib_data_simple \
  --target_dir ~/.qlib/qlib_data/cn_data --region cn

# Verify installation
python -c "import qlib; print(qlib.__version__)"
```

### Creating source_data.h5

**Important**: On macOS, `multiprocessing.set_start_method("fork", force=True)` is required.
Run as a script file (stdin is not supported; this avoids multiprocessing spawn errors).

```python
# Save as /tmp/prepare_source_data.py and execute
import multiprocessing
multiprocessing.set_start_method("fork", force=True)
import qlib, pandas as pd

qlib.init(provider_uri="~/.qlib/qlib_data/cn_data", region="cn")
from qlib.data import D

instruments = D.instruments("csi300")
stock_list = D.list_instruments(instruments, start_time="2019-01-01", end_time="2020-12-31")
symbols = sorted(stock_list.keys())[:50]  # 50 stocks for testing

df = D.features(
    symbols,
    ["$open", "$close", "$high", "$low", "$volume", "$vwap"],
    start_time="2019-01-01", end_time="2020-12-31"
)
df.columns = ["open", "close", "high", "low", "volume", "vwap"]

# Place in each round's workspace
for r in range(N_ROUNDS):
    df.to_hdf(f"{ARTIFACT_DIR}/round_{r}/implementations/source_data.h5", key="data")
```

**Note**: The Simple data covers 2005 through June 2021. Dates after 2022 will return empty results.

## Flow

### 0. Expand Plan Template (always run first)

```bash
# Copy the template and substitute variables
cp .claude/templates/rdloop-plan.md <artifact_dir>/plan.md
# Replace {{RUN_ID}}, {{N_ROUNDS}}, {{ARTIFACT_DIR}} with actual values
```

**Proceed based on this plan.md, checking off each task as it completes.**
Also register the same tasks with the TodoWrite tool to track progress.

### 1. Initialization

- Does `artifact_dir/trace.json` exist?
  - YES: Resume — load the trace and identify the next round
  - NO: New run — create directories and initialize trace.json

### 1b. Data Quality Validation (first run only)

Validate the missing rate of each column in source_data.h5 and save to `artifact_dir/data_quality.json`.
This information is passed to the Planner across all rounds.

```python
# Run as /tmp/check_data_quality.py
import multiprocessing
multiprocessing.set_start_method("fork", force=True)
import pandas as pd, json

df = pd.read_hdf(f"{ARTIFACT_DIR}/round_0/implementations/source_data.h5", key="data")
quality = {
    "total_rows": len(df),
    "columns": {}
}
for col in df.columns:
    notna = int(df[col].notna().sum())
    quality["columns"][col] = {
        "notna": notna,
        "missing_pct": round((1 - notna / len(df)) * 100, 1),
        "usable": notna > len(df) * 0.5  # Usable if more than 50% present
    }
quality["usable_columns"] = [c for c, v in quality["columns"].items() if v["usable"]]

with open(f"{ARTIFACT_DIR}/data_quality.json", "w") as f:
    json.dump(quality, f, indent=2)
```

**Example output**:
```json
{
  "usable_columns": ["open", "close", "high", "low", "volume"],
  "columns": {
    "vwap": {"notna": 0, "missing_pct": 100.0, "usable": false}
  }
}
```

### 2. Round Loop (repeat N times)

For each round `i`:

#### a. Build TraceView
Generate a compressed summary of past experiments (SOTA, recent results, failed hypotheses).
Include `usable_columns` from `data_quality.json` in the TraceView.

#### b. Plan — Planner Subagent
```
Delegate to Agent tool (see .claude/subagents/planner.md)
Input: TraceView, Scenario, usable_columns from data_quality.json
Output: round_<i>/hypothesis.json, round_<i>/experiment.json
```

#### c. Implement — Codex CLI or Subagent Fallback

**Primary (Codex CLI available):**
```bash
codex exec --full-auto -C <workspace_path> \
  "Generate <workspace_path>/factor.py based on the following factor specification.
   Spec: $(cat <artifact_dir>/round_<i>/experiment.json)
   Rules: source_data.h5 -> result.h5, MultiIndex support, no look-ahead bias"
```
**Note**: Codex uses its own Python environment. Run factor.py in the RD-Agent venv.

**Fallback (Codex CLI not available):**
```
Delegate to Agent tool (see .claude/subagents/coder.md, Subagent Fallback section)
Input: experiment.json contents, workspace path
Output: round_<i>/implementations/factor.py
The agent writes factor.py directly using the Write tool.
```

Detection: run `which codex` at initialization (Phase 0). Set `codex_available=true/false`.

#### d. Run Backtest — Direct Bash Execution
```bash
cd <artifact_dir>/round_<i>/implementations && python factor.py
# source_data.h5 -> result.h5 is generated
```

#### d2. Compute IC Metrics — Direct Bash Execution

After running factor.py, compute IC/IR/RankIC from result.h5 to generate run_result.json:

```python
# Save as /tmp/calc_ic.py and execute (stdin not supported)
# Args: workspace artifact_dir round_idx factor_name
import multiprocessing
multiprocessing.set_start_method("fork", force=True)
import pandas as pd, numpy as np, json, sys

workspace, artifact_dir = sys.argv[1], sys.argv[2]
round_idx, factor_name = int(sys.argv[3]), sys.argv[4]

result = pd.read_hdf(f"{workspace}/result.h5")
source = pd.read_hdf(f"{workspace}/source_data.h5")

# Index-order independent: reset_index + merge approach
result_df = result.reset_index()
source_df = source.reset_index()

factor_col = [c for c in result_df.columns if c not in ("instrument", "datetime")][0]
result_df = result_df.rename(columns={factor_col: "factor"})

source_df = source_df.sort_values(["instrument", "datetime"])
source_df["forward_return"] = source_df.groupby("instrument")["close"].transform(
    lambda s: s.pct_change().shift(-1)
)

merged = pd.merge(result_df[["instrument", "datetime", "factor"]],
                   source_df[["instrument", "datetime", "forward_return"]],
                   on=["instrument", "datetime"])
merged = merged.dropna(subset=["factor", "forward_return"])

# Daily IC / Rank IC (use loop to avoid groupby.apply return type issues)
ic_list, rank_ic_list = [], []
for dt, grp in merged.groupby("datetime"):
    if len(grp) < 5:
        continue
    ic_list.append(grp["factor"].corr(grp["forward_return"]))
    rank_ic_list.append(grp["factor"].rank().corr(grp["forward_return"].rank()))

daily_ic = pd.Series(ic_list).dropna()
daily_rank_ic = pd.Series(rank_ic_list).dropna()

run_result = {
    "status": "success",
    "factor_name": factor_name,
    "metrics": {
        "ic_mean": round(float(daily_ic.mean()), 6),
        "ic_std": round(float(daily_ic.std()), 6),
        "ir": round(float(daily_ic.mean() / daily_ic.std()), 6),
        "rank_ic_mean": round(float(daily_rank_ic.mean()), 6),
        "daily_ic_positive_ratio": round(float((daily_ic > 0).mean()), 4),
        "n_observations": int(merged.shape[0]),
        "n_days": int(len(daily_ic))
    }
}
with open(f"{artifact_dir}/round_{round_idx}/run_result.json", "w") as f:
    json.dump(run_result, f, indent=2)
```

Save results to `round_<i>/run_result.json`.

#### e. Evaluate — Evaluator Subagent
```
Delegate to Agent tool (see .claude/subagents/evaluator.md)
Input: run_result.json, hypothesis, SOTA baseline, code_change_summary
Output: round_<i>/feedback.json
Note: Do not pass factor.py source code (information separation principle)
```

#### f. State Update
- Record status and timestamps in `round_<i>/manifest.json`
- Append to `trace.json`
- Display round summary

### 3. Final Report
After all rounds complete:
- Round summary table (hypothesis, metrics, decision)
- Final SOTA details
- Suggestions for future exploration

## Resume Protocol

When `trace.json` contains partial history:
1. Identify the last completed round from `round_manifest.json`
2. Identify incomplete steps via `manifest.json` step_idx
3. Resume from the next incomplete step

## Error Handling

| Error | Response |
|-------|----------|
| Planner schema invalid (3 times) | Skip round, record in manifest |
| Coder syntax error | Backtest fails — Evaluator evaluates with status=failed |
| Backtest timeout | Set status=timeout in run_result.json |
| Evaluator schema invalid (3 times) | Skip evaluation, decision=false |
