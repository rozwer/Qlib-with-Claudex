---
name: qlib-hypothesis-gen
description: Generate a novel factor hypothesis from market data analysis and prior experiment history. Used by Planner subagent (.claude/subagents/planner.md).
---

# Qlib Factor Hypothesis Generation

Planner サブエージェントが参照するガイドライン。
直接呼び出しではなく、Planner が Agent tool として起動された際にこのスキーマに従う。

## 入力コンテキスト

Planner サブエージェントが受け取る:
- **TraceView**: 過去実験の圧縮サマリ（SOTA, 直近結果, 失敗仮説）
- **Scenario**: マーケットデータ記述（columns: open, close, high, low, volume, vwap）
- **制約**: 失敗済み仮説の繰り返し禁止

## 出力スキーマ

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

## 仮説カテゴリ

| カテゴリ | 例 | 典型的 IC |
|---------|-----|----------|
| Momentum | 価格/出来高トレンド継続 | 0.02-0.05 |
| Mean Reversion | 移動平均からの乖離 | 0.02-0.04 |
| Volatility | 実現 vs インプライド Vol スプレッド | 0.01-0.03 |
| Liquidity | ビッドアスク、ターンオーバー | 0.02-0.04 |
| Microstructure | 注文フロー、VWAP 乖離 | 0.03-0.06 |

## 品質基準

- **Novelty**: TraceView の failed_hypotheses_summary に含まれないこと
- **Testability**: 利用可能カラム（OHLCV + vwap）で計算可能
- **No look-ahead bias**: 各時点で過去データのみ使用
- **Valid Python identifier**: factor_name は `[a-z][a-z0-9_]*`
