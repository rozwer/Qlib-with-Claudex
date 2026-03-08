# Qlib-with-Claudex / RD-Agent-with-Claudex

A fork of Microsoft Qlib and RD-Agent where Claude Code autonomously executes factor research loops.

## Quick Start

```bash
# 1. Environment setup
cd RD-Agent-with-Claudex
source .venv/bin/activate   # Python 3.12 (uv)

# 2. Download Qlib data (first time only)
cd ../Qlib-with-Claudex/scripts
python get_data.py qlib_data --name qlib_data_simple \
  --target_dir ~/.qlib/qlib_data/cn_data --region cn

# 3. Run existing tests (38 pass)
cd ../../RD-Agent-with-Claudex
pytest test/adapters/ -v
```

## Running the R&D Loop

Ask Claude Code something like:

> "Run a factor R&D loop for 3 rounds."

The loop automatically repeats the following steps:

1. **Planner** (Agent tool) — Hypothesis + experiment spec (hypothesis.json, experiment.json)
2. **Coder** (`codex exec --full-auto`) — Generate factor.py
3. **Backtest** (Bash) — `python factor.py` (source_data.h5 → result.h5, executed in RD-Agent venv)
4. **IC Calculation** (Bash) — run_result.json (IC/IR/RankIC)
5. **Evaluator** (Agent tool) — feedback.json (adopt as SOTA if IC > 0.03)

Details: `.claude/skills/qlib-rd-loop.md`

## Project Structure

```
Qlib/
├── Qlib-with-Claudex/           # microsoft/qlib fork
├── RD-Agent-with-Claudex/       # microsoft/RD-Agent fork
│   ├── rdagent/adapters/        # 5-slot Adapter layer
│   ├── rdagent/oai/backend/     # LLM backend (LiteLLM + Claude shim)
│   ├── rdagent/core/            # Data structures (Hypothesis, Trace, Experiment)
│   ├── test/adapters/           # Adapter tests (38 pass)
│   └── .venv/                   # Python 3.12 virtual environment
├── .claude/
│   ├── skills/                  # 5 skill definitions
│   ├── subagents/               # Planner / Coder / Evaluator
│   └── artifacts/rdloop/        # Execution results (trace.json is SSOT)
└── docs/plans/                  # Design documents
```

## Skills & Subagents

| Skill | Purpose |
|-------|---------|
| qlib-rd-loop | Overall loop orchestration |
| qlib-hypothesis-gen | Hypothesis generation guidelines for Planner |
| qlib-factor-implement | factor.py implementation guidelines for Coder |
| qlib-experiment-eval | Evaluation criteria for Evaluator |
| qlib-artifact-inspect | Inspect artifact directory / check IC |

| Subagent | Execution Method | Role |
|----------|-----------------|------|
| Planner | Agent tool | Hypothesis generation + experiment design (TraceView → JSON) |
| Coder | **Codex CLI** (`codex exec`) | Generate factor.py (experiment.json → Python) |
| Evaluator | Agent tool | Metrics evaluation (IC-based decision, no code reference) |

## Key Architecture

**Control Inversion**: Claude Code uses Python/Qlib/Codex as tools (no API key required).

```
Claude Code (Orchestrator)
  ├── Planner  → Delegates hypothesis generation to subagent via Agent tool
  ├── Coder   → Generates factor.py via codex exec --full-auto
  ├── Backtest → Runs python factor.py via Bash (RD-Agent venv)
  ├── IC Calc  → Executes calculation script via Bash
  └── Evaluator → Delegates evaluation to subagent via Agent tool
```

## macOS Notes

- `multiprocessing.set_start_method("fork", force=True)` is required
- Qlib data download must be run from a script file (stdin not supported)
- Simple data covers the period 2005–June 2021

## Conventions

- Documentation in concise English
- License: MIT (inherited)
- Brand name: `with-Claudex`
- Package manager: uv
- Tests: `pytest test/adapters/ -v`
