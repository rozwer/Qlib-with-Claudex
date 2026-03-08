# Qlib-with-Claudex

A quantitative investment R&D framework that autonomously drives Microsoft Qlib + RD-Agent using Claude Code + Codex.

## Overview

Replaces OpenAI API dependencies with **Claude Code subagents + Codex CLI**,
achieving a control inversion from "Python → LLM API" to "**Claude Code → uses Python/Qlib as tools**".

## Repository Structure

```
Qlib/                          ← This repository (parent)
├── .claude/                   ← Claude Code config, skills, subagent definitions
│   ├── skills/                # RD loop, hypothesis generation, factor implementation, etc.
│   ├── subagents/             # Planner / Coder / Evaluator definitions
│   ├── settings.json          # Shared permissions
│   └── artifacts/             # Experiment artifacts
├── Qlib-with-Claudex/         ← microsoft/qlib fork (subproject)
├── RD-Agent-with-Claudex/     ← microsoft/RD-Agent fork (subproject)
└── docs/plans/                ← Design documents
```

## Setup

```bash
# 1. Clone with submodules (single command)
git clone --recurse-submodules git@github.com:rozwer/Qlib-with-Claudex.git Qlib
cd Qlib

# If you already cloned without --recurse-submodules:
# git submodule update --init --recursive

# 3. Set up RD-Agent virtual environment
cd RD-Agent-with-Claudex
uv venv --python 3.12 && source .venv/bin/activate
uv pip install -e ".[dev]"

# 4. Install Qlib into the venv
uv pip install -e ../Qlib-with-Claudex/

# 5. Download Qlib market data (~50MB, CSI300 2005-2021)
cd ../Qlib-with-Claudex/scripts
python get_data.py qlib_data --name qlib_data_simple \
  --target_dir ~/.qlib/qlib_data/cn_data --region cn
cd ../..

# 6. Generate source_data.h5 (quick test)
python scripts/prepare_source_data.py --output /tmp/source_data.h5

# 7. Verify data quality
python scripts/check_data_quality.py /tmp/source_data.h5 /tmp/data_quality.json
```

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/prepare_source_data.py` | Generate source_data.h5 from Qlib market data |
| `scripts/calc_ic.py` | Calculate IC/IR/RankIC from backtest results |
| `scripts/check_data_quality.py` | Inspect column missing rates, output data_quality.json |

```bash
# Generate source_data.h5 for a full R&D loop (5 rounds, 50 instruments, 2019-2020)
source RD-Agent-with-Claudex/.venv/bin/activate
python scripts/prepare_source_data.py --output_dir .claude/artifacts/rdloop/my_run --rounds 5

# Customize: 100 instruments, longer period
python scripts/prepare_source_data.py --output_dir .claude/artifacts/rdloop/my_run \
  --rounds 10 --n_instruments 100 --start_time 2015-01-01 --end_time 2020-12-31
```

## R&D Loop

Claude Code sequentially invokes the following subagents to automate factor discovery:

| Step | Component | Role |
|------|-----------|------|
| Hypothesis Generation | Planner (Agent tool) | TraceView analysis → propose new hypothesis |
| Code Generation | Codex CLI (`codex exec --full-auto`) | Generate factor calculation code |
| Execution | Bash (RD-Agent venv) | Run factor.py + calculate IC |
| Evaluation | Evaluator (Agent tool) | Analyze results → provide feedback |

## License

MIT (inherited from Microsoft Qlib / RD-Agent)
