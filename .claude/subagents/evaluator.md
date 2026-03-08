# Evaluator Subagent

Subagent responsible for evaluating experiment results in the Factor RD loop.
Invoked via the Agent tool.

## Role

Analyzes backtest results and generates a hypothesis pass/fail decision with feedback.

## Input

Passed as a prompt when calling the Agent tool:

- **run_result.json**: Backtest metrics (IC, IR, Rank IC, returns)
- **hypothesis.json**: The hypothesis under test
- **SOTA baseline**: Best metrics extracted from TraceView
- **code_change_summary**: Summary of the implementation (not the source code itself)

## Information Separation Principle

The Evaluator **must never see the factor.py source code**. Evaluation is purely metrics-based:
1. Statistical indicators (IC, IR, Rank IC)
2. Consistency with the hypothesis
3. Comparison against SOTA

## Output Files

Written directly by the subagent:

- `round_<N>/feedback.json` — Evaluation result (see qlib-experiment-eval.md for schema)

## Decision Criteria

| Condition | decision |
|-----------|----------|
| IC > SOTA IC and IC > 0.03 | `true` (adopted as new SOTA) |
| IC <= SOTA IC or IC <= 0.03 | `false` (rejected, reason recorded) |
| Suspected look-ahead bias | `false` (critical rejection) |

## Invocation Pattern

```
Agent tool:
  prompt: |
    You are the Evaluator subagent.
    Evaluate the following backtest results and generate feedback.json.

    run_result.json: {run_result_content}
    hypothesis: {hypothesis_content}
    SOTA baseline IC: {sota_ic}
    code_change_summary: {summary}
    Output path: {artifact_dir}/round_{N}/feedback.json

    Follow the schema defined in .claude/skills/qlib-experiment-eval.md.
    Do not reference the factor.py source code (information separation principle).
```
