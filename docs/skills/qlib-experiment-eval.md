---
name: qlib-experiment-eval
description: Evaluate factor experiment results and provide feedback. Use when assessing backtest outcomes in the RD loop.
---

# Qlib Factor Experiment Evaluation

## Overview

Assess the quality of a factor experiment by analyzing backtest metrics, comparing against SOTA, and providing actionable feedback.

## Input

- **run_result.json**: Backtest metrics (IC, IR, Rank IC, returns)
- **hypothesis**: The factor hypothesis being tested
- **SOTA baseline**: Best previous experiment metrics (from TraceView)
- **code_change_summary**: What was implemented (NOT source code)

## Information Separation Principle

The evaluator must NEVER see the factor implementation source code. This ensures evaluation is based purely on:
1. Statistical metrics (IC, IR, Rank IC)
2. Hypothesis alignment (does the result support the hypothesis?)
3. SOTA comparison (improvement over baseline?)

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
| No look-ahead bias detected | Must pass | Critical |

## decision Field

- `true`: Factor accepted as new SOTA. Update baseline.
- `false`: Factor rejected. Record reason in failed hypotheses for future avoidance.
