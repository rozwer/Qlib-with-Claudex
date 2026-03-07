---
name: qlib-hypothesis-gen
description: Generate a novel factor hypothesis from market data analysis and prior experiment history. Use when proposing new factors for the RD loop.
---

# Qlib Factor Hypothesis Generation

## Overview

Propose a novel, testable factor hypothesis for quantitative equity research. The hypothesis should be grounded in market microstructure, behavioral finance, or statistical patterns.

## Input Context

- **TraceView**: Compressed summary of prior experiment rounds (SOTA, recent results, failed hypotheses)
- **Scenario**: Market data description (columns: open, close, high, low, volume, vwap)
- **Constraints**: Must not repeat previously failed hypotheses

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

| Category | Example | Typical IC Range |
|----------|---------|------------------|
| Momentum | Price/volume trend continuation | 0.02-0.05 |
| Mean Reversion | Deviation from moving average | 0.02-0.04 |
| Volatility | Realized vs implied vol spread | 0.01-0.03 |
| Liquidity | Bid-ask spread, turnover ratio | 0.02-0.04 |
| Microstructure | Order flow imbalance, VWAP deviation | 0.03-0.06 |

## Quality Criteria

- **Novelty**: Not in failed_hypotheses_summary from TraceView
- **Testability**: Can be computed from available columns (OHLCV + vwap)
- **No look-ahead bias**: Factor must use only past data at each point
- **Valid Python identifier**: factor_name must be `[a-z][a-z0-9_]*`
