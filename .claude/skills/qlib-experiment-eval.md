---
name: qlib-experiment-eval
description: Evaluate factor experiment results and provide feedback. Used by Evaluator subagent (.claude/subagents/evaluator.md).
---

# Qlib Factor Experiment Evaluation

Evaluator サブエージェントが参照するガイドライン。
直接呼び出しではなく、Evaluator が Agent tool として起動された際にこのスキーマに従う。

## 入力

Evaluator サブエージェントが受け取る:
- **run_result.json**: バックテストメトリクス（IC, IR, Rank IC, returns）
- **hypothesis**: テスト対象のファクター仮説
- **SOTA baseline**: ベスト実験のメトリクス（TraceView から）
- **code_change_summary**: 実装内容の要約（ソースコードではない）

## 情報分離原則

Evaluator は **factor.py のソースコードを絶対に見ない**。評価は純粋に:
1. 統計指標（IC, IR, Rank IC）
2. 仮説との整合性（結果は仮説を支持するか？）
3. SOTA との比較（ベースラインからの改善？）

## 出力スキーマ

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

## 判定基準

| メトリクス | 閾値 | ウェイト |
|-----------|------|---------|
| IC > SOTA IC | decision=true の必要条件 | High |
| IC > 0.03 | 単独での良好パフォーマンス | Medium |
| IC 安定性 (std < 0.02) | ロバストネス指標 | Medium |
| Look-ahead bias なし | 必須 | Critical |

## decision フィールド

- `true`: ファクター採用（新 SOTA）。ベースライン更新。
- `false`: ファクター棄却。理由を失敗仮説として記録し、将来の回避に使用。
