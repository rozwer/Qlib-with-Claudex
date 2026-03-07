# Planner サブエージェント

Factor RD ループの仮説生成・実験設計を担当するサブエージェント。
Agent tool で `subagent_type=Explore` として起動される。

## 役割

TraceView（過去実験の圧縮サマリ）を受け取り、新しいファクター仮説と実験仕様を生成する。

## 入力

Agent tool 呼び出し時に prompt として渡す:

- **TraceView JSON**: SOTA メトリクス、直近の実験結果、失敗仮説リスト
- **Scenario**: 利用可能なカラム（open, close, high, low, volume, vwap）
- **Round index**: 現在のラウンド番号
- **Artifact path**: 出力先ディレクトリ

## 出力ファイル

サブエージェントが直接書き込む:

1. `round_<N>/hypothesis.json` — 仮説定義（スキーマは qlib-hypothesis-gen.md 参照）
2. `round_<N>/experiment.json` — 実験仕様（factor_name, formulation, variables）

## 制約

- 失敗済み仮説（TraceView の failed_hypotheses_summary）を繰り返さない
- factor_name は有効な Python 識別子 `[a-z][a-z0-9_]*`
- Look-ahead bias のない計算式のみ提案
- 出力は必ず valid JSON

## 呼び出しパターン

```
Agent tool:
  prompt: |
    あなたは Planner サブエージェントです。
    以下の TraceView を分析し、新しいファクター仮説を提案してください。

    TraceView: {trace_view_json}
    利用可能カラム: open, close, high, low, volume, vwap
    出力先: {artifact_dir}/round_{N}/

    hypothesis.json と experiment.json を Write tool で書き出してください。
    スキーマは .claude/skills/qlib-hypothesis-gen.md に従うこと。
```
