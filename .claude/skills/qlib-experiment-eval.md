---
name: qlib-experiment-eval
description: Evaluate factor experiment results and provide feedback. Used by Evaluator subagent (.claude/subagents/evaluator.md).
---

# Qlib Factor Experiment Evaluation

Guidelines referenced by the Evaluator subagent.
Not called directly — the Evaluator follows this schema when launched as an Agent tool.

## Input

The Evaluator subagent receives:
- **run_result.json**: Backtest metrics (IC, IR, Rank IC, returns)
- **hypothesis**: The factor hypothesis being tested
- **SOTA baseline**: Best experiment metrics (from TraceView)
- **code_change_summary**: Summary of the implementation (not the source code)

## Information Separation Principle

The Evaluator **must never see the factor.py source code**. Evaluation is based purely on:
1. Statistical metrics (IC, IR, Rank IC)
2. Consistency with the hypothesis (do the results support the hypothesis?)
3. Comparison with SOTA (improvement over baseline?)

## Output Schema

```json
{
  "reason": "IC improved from 0.03 to 0.045. Factor shows consistent alpha.",
  "decision": true,
  "code_change_summary": "Implemented VWAP momentum with 20-day lookback",
  "observations": "IC=0.045, stable across validation windows",
  "hypothesis_evaluation": "Hypothesis supported by positive IC",
  "new_hypothesis": null,
  "acceptable": true
}
```

## Decision Criteria

| Metric | Threshold | Weight |
|--------|-----------|--------|
| IC > SOTA IC | Required for decision=true | High |
| IC > 0.03 | Good standalone performance | Medium |
| IC stability (std < 0.02) | Robustness indicator | Medium |
| No look-ahead bias | Mandatory | Critical |

## decision Field

- `true`: Factor accepted (new SOTA). Baseline is updated.
- `false`: Factor rejected. The reason is recorded as a failed hypothesis for future avoidance.
