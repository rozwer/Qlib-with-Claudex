---
name: qlib-factor-implement
description: Guidelines for implementing a Qlib factor. Use when generating factor.py code for the RD loop.
---

# Qlib Factor Implementation Guide

## Overview

Generate a `factor.py` file that computes a quantitative alpha factor from market data and outputs the result as an HDF5 file.

## Workspace Structure

```
workspace/
├── factor.py              # YOU generate this file
├── conf_baseline.yaml
├── conf_combined_factors.yaml
├── conf_combined_factors_sota_model.yaml
├── read_exp_res.py
├── source_data.h5         # Linked market data (DO NOT modify)
└── result.h5              # YOUR output file
```

## factor.py Requirements

### Input
- Read market data from `source_data.h5` in the workspace directory
- The HDF5 contains a DataFrame with columns: `open`, `close`, `high`, `low`, `volume`, `vwap`, and date/instrument indices

### Output
- Write factor values to `result.h5` with key `"data"`
- The output must be a pandas Series or DataFrame indexed by (date, instrument)

### Template

```python
import pandas as pd
import numpy as np

def calculate_factor(df: pd.DataFrame) -> pd.Series:
    """
    Calculate the factor value.

    Parameters
    ----------
    df : pd.DataFrame
        Market data with columns: open, close, high, low, volume, vwap
        MultiIndex: (datetime, instrument)

    Returns
    -------
    pd.Series
        Factor values indexed by (datetime, instrument)
    """
    # YOUR IMPLEMENTATION HERE
    pass

if __name__ == "__main__":
    df = pd.read_hdf("source_data.h5")
    result = calculate_factor(df)
    result.to_hdf("result.h5", key="data")
```

## Quality Criteria

### Must Pass
- [ ] Valid Python syntax (`py_compile` check)
- [ ] Produces `result.h5` when executed
- [ ] No look-ahead bias (only uses past data at each point)
- [ ] Handles NaN values gracefully

### Target Metrics
- IC (Information Coefficient) > 0.03 is considered good
- Stable IC across time periods indicates robustness

## Common Patterns (Success)

1. **Momentum**: `close / close.shift(N) - 1`
2. **Mean Reversion**: `(close - close.rolling(N).mean()) / close.rolling(N).std()`
3. **Volume-Price**: `(close * volume) / (close * volume).rolling(N).mean()`
4. **Volatility**: `close.rolling(N).std() / close.rolling(N).mean()`

## Common Mistakes (Avoid)

| Mistake | Fix |
|---------|-----|
| Using future data (look-ahead bias) | Only use `.shift(N)` with N > 0 or `.rolling()` |
| Wrong column names | Use exact names: `open`, `close`, `high`, `low`, `volume`, `vwap` |
| Not handling MultiIndex | Use `.groupby(level="instrument")` for per-stock calculations |
| Output wrong format | Must be Series/DataFrame with (datetime, instrument) index |
| Division by zero | Add `.replace([np.inf, -np.inf], np.nan)` after division |

## Output Location

Place the generated file at: `round_<N>/implementations/factor.py`
