---
name: qlib-hypothesis-gen
description: Generate a novel factor hypothesis from market data analysis and prior experiment history. Used by Planner subagent (.claude/subagents/planner.md).
---

# Qlib Factor Hypothesis Generation

Guidelines referenced by the Planner subagent.
Not called directly — the Planner follows this schema when launched as an Agent tool.

## Input Context

The Planner subagent receives:
- **TraceView**: Compressed summary of past experiments (SOTA, recent results, failed hypotheses)
- **Scenario**: Market data description (columns: open, close, high, low, volume, vwap)
- **data_quality.json**: Missing rate and usability of each column (`usable_columns` list)
- **Constraints**: No repeating failed hypotheses; columns with `usable=false` must not be used

## Output Schema

```json
{
  "hypothesis": "Volume-weighted momentum captures institutional flow",
  "reason": "Institutions trade with volume...",
  "concise_reason": "Volume-weighted momentum isolates institutional flow",
  "concise_observation": "High volume bars predict short-term direction",
  "concise_justification": "Academic research supports volume-price linkage",
  "concise_knowledge": "VWAP momentum = vwap / vwap.shift(20) - 1",
  "factor_name": "vwap_momentum_20d",
  "factor_description": "20-day VWAP momentum factor",
  "factor_formulation": "vwap / vwap.shift(20) - 1",
  "variables": {"lookback": 20}
}
```

## Hypothesis Categories

| Category | Example | Typical IC |
|----------|---------|------------|
| Momentum | Price/volume trend continuation | 0.02-0.05 |
| Mean Reversion | Deviation from moving average | 0.02-0.04 |
| Volatility | Realized vs implied vol spread | 0.01-0.03 |
| Liquidity | Bid-ask spread, turnover | 0.02-0.04 |
| Microstructure | Order flow, VWAP deviation | 0.03-0.06 |

## Quality Criteria

- **Novelty**: Must not appear in the TraceView's failed_hypotheses_summary
- **Testability**: Must be computable using only columns listed in `usable_columns` from `data_quality.json`
- **No look-ahead bias**: Use only past data at each point in time
- **Valid Python identifier**: factor_name must match `[a-z][a-z0-9_]*`

## Data Quality Notes

- Column availability varies by data source (e.g., vwap is entirely NaN in Simple Data)
- Always check `data_quality.json` before proposing a hypothesis; do not propose hypotheses that depend on columns with `usable=false`
- If a column is unavailable, alternative calculations (e.g., typical price = (H+L+C)/3 as a vwap substitute) may be considered, but this must be explicitly noted
