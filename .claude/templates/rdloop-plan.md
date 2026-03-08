# RD Loop Plan — {{RUN_ID}}

> Template: `.claude/templates/rdloop-plan.md`
> Source skill: `qlib-rd-loop`

## Configuration

| Item | Value |
|------|-------|
| run_id | {{RUN_ID}} |
| rounds | {{N_ROUNDS}} |
| artifact_dir | {{ARTIFACT_DIR}} |
| scenario | factor |

## Phase 0: Environment Setup

- [ ] **0-1** Verify Qlib data exists (`~/.qlib/qlib_data/cn_data`)
- [ ] **0-2** Verify RD-Agent venv works (`python -c "import qlib"`)
- [ ] **0-3** Verify Codex CLI works (`codex --version`)
- [ ] **0-4** Create artifact_dir + `implementations/` directories for all rounds
- [ ] **0-5** Generate source_data.h5 and place in all rounds' `implementations/`
- [ ] **0-6** Initialize trace.json (new) or load (resume)

## Phase 1: Data Quality Verification (First Run Only)

- [ ] **1-1** Inspect missing rate for each column in source_data.h5
- [ ] **1-2** Write `data_quality.json` to artifact_dir
- [ ] **1-3** Confirm and log usable_columns

## Phase 2: Round Execution

### Round {{i}} / {{N_ROUNDS}}

#### 2a. Build TraceView
- [ ] **2a** Build TraceView from trace.json (SOTA, failed hypotheses, data_quality)

#### 2b. Hypothesis Generation -> Planner Subagent
- [ ] **2b-1** Launch Planner subagent (Agent tool, subagent_type=Explore)
- [ ] **2b-2** Verify hypothesis.json output (schema validation)
- [ ] **2b-3** Verify experiment.json output (factor_name is a valid identifier)

#### 2c. Code Generation -> Codex CLI
- [ ] **2c-1** Run `codex exec --full-auto`
- [ ] **2c-2** Verify factor.py was generated
- [ ] **2c-3** Syntax verification (`python -c "import py_compile; py_compile.compile('factor.py')"`)

#### 2d. Backtest -> Direct Bash Execution
- [ ] **2d-1** Run `python factor.py` (RD-Agent venv)
- [ ] **2d-2** Verify result.h5 was generated
- [ ] **2d-3** Calculate IC metrics (run `/tmp/calc_ic.py`)
- [ ] **2d-4** Verify run_result.json

#### 2e. Evaluation -> Evaluator Subagent
- [ ] **2e-1** Launch Evaluator subagent (Agent tool)
- [ ] **2e-2** Verify feedback.json output
- [ ] **2e-3** Decision judgment (true=SOTA update, false=reject)

#### 2f. State Update
- [ ] **2f-1** Append to trace.json
- [ ] **2f-2** Display round summary

---

> **Round template**: Repeat steps 2a-2f above for each round.
> Copy this section at the start of each round and replace `Round {{i}}`.

## Phase 3: Final Report

- [ ] **3-1** Output results table for all rounds
- [ ] **3-2** Display final SOTA details
- [ ] **3-3** Suggest future exploration directions

## Checkpoint Rules

1. Update each `- [ ]` to `- [x]` upon completion
2. On error, append `ERROR: <summary>` to the relevant task
3. When skipping a round, append `SKIP` to all tasks
4. Expand the Phase 2 round section by copying before execution
