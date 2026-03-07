---
name: qlib-factor-implement
description: Guidelines for implementing a Qlib factor. Used by Coder subagent (.claude/subagents/coder.md).
---

# Qlib Factor Implementation Guide

Coder サブエージェントが参照するガイドライン。
Agent tool として起動された Coder がこのガイドに従い factor.py を生成する。

## ワークスペース構造

```
workspace/
├── factor.py              # Coder が生成するファイル
├── conf_baseline.yaml
├── conf_combined_factors.yaml
├── conf_combined_factors_sota_model.yaml
├── read_exp_res.py
├── source_data.h5         # マーケットデータ（変更禁止）
└── result.h5              # 出力ファイル
```

## factor.py 要件

### 入力
- ワークスペース内の `source_data.h5` から読み込み
- HDF5 には DataFrame: columns = `open`, `close`, `high`, `low`, `volume`, `vwap`, index = (date, instrument)

### 出力
- `result.h5` に key `"data"` でファクター値を書き出し
- (date, instrument) の MultiIndex を持つ Series または DataFrame

### テンプレート

```python
import pandas as pd
import numpy as np

def calculate_factor(df: pd.DataFrame) -> pd.Series:
    """
    Parameters
    ----------
    df : pd.DataFrame
        columns: open, close, high, low, volume, vwap
        MultiIndex: (datetime, instrument)

    Returns
    -------
    pd.Series
        (datetime, instrument) index のファクター値
    """
    # 実装
    pass

if __name__ == "__main__":
    df = pd.read_hdf("source_data.h5")
    result = calculate_factor(df)
    result.to_hdf("result.h5", key="data")
```

## 品質基準

### 必須
- Valid Python syntax
- 実行時に `result.h5` を生成
- Look-ahead bias なし（過去データのみ使用）
- NaN を適切に処理

### 目標メトリクス
- IC > 0.03 が良好
- 期間間で安定した IC はロバストネスを示す

## よくあるパターン（成功例）

1. **Momentum**: `close / close.shift(N) - 1`
2. **Mean Reversion**: `(close - close.rolling(N).mean()) / close.rolling(N).std()`
3. **Volume-Price**: `(close * volume) / (close * volume).rolling(N).mean()`
4. **Volatility**: `close.rolling(N).std() / close.rolling(N).mean()`

## よくあるミス（回避）

| ミス | 修正 |
|------|------|
| 未来データ使用 (look-ahead) | `.shift(N)` で N > 0、`.rolling()` のみ |
| カラム名間違い | 正確に: `open`, `close`, `high`, `low`, `volume`, `vwap` |
| MultiIndex 未対応 | `.groupby(level="instrument")` で銘柄別計算 |
| 出力フォーマット不正 | (datetime, instrument) index の Series/DataFrame |
| ゼロ除算 | `.replace([np.inf, -np.inf], np.nan)` を追加 |

## 出力先

`round_<N>/implementations/factor.py`
