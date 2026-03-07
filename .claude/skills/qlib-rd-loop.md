---
name: qlib-rd-loop
description: Run the Qlib factor R&D loop — propose hypotheses, generate code, backtest, evaluate. Use when asked to run factor experiments or start the RD loop.
---

# Qlib Factor R&D Loop

自動ファクター探索ループのオーケストレーター。
各ステップはサブエージェント（Agent tool）に委託する。

## サブエージェント構成

| ステップ | サブエージェント | 定義 |
|---------|---------------|------|
| 仮説生成 + 実験設計 | Planner | `.claude/subagents/planner.md` |
| コード生成 | Coder | `.claude/subagents/coder.md` |
| バックテスト実行 | _(Bash 直接)_ | `python factor.py` |
| 結果評価 | Evaluator | `.claude/subagents/evaluator.md` |

## 設定

| パラメータ | デフォルト | 説明 |
|-----------|---------|------|
| scenario | factor | Phase 1 は factor 固定 |
| rounds | 5 | 実験ラウンド数 |
| run_id | 自動生成 | ユニーク実行 ID |
| artifact_dir | `.claude/artifacts/rdloop/<run_id>/` | 出力先 |

## フロー

### 1. 初期化

- `artifact_dir/trace.json` が存在？
  - YES → Resume: trace を読み込み次のラウンドを特定
  - NO → 新規: ディレクトリ作成、trace.json 初期化

### 2. ラウンドループ（N 回繰り返し）

各ラウンド `i`:

#### a. TraceView 構築
過去実験の圧縮サマリを生成（SOTA, 直近結果, 失敗仮説）。

#### b. Plan → Planner サブエージェント
```
Agent tool に委託（.claude/subagents/planner.md 参照）
入力: TraceView, Scenario
出力: round_<i>/hypothesis.json, round_<i>/experiment.json
```

#### c. Implement → Coder サブエージェント
```
Agent tool に委託（.claude/subagents/coder.md 参照）
入力: experiment.json, hypothesis.json
出力: round_<i>/implementations/factor.py
```

#### d. Run Backtest → Bash 直接実行
```bash
cd <workspace_path> && python factor.py
```
結果を `round_<i>/run_result.json` に保存。

#### e. Evaluate → Evaluator サブエージェント
```
Agent tool に委託（.claude/subagents/evaluator.md 参照）
入力: run_result.json, hypothesis, SOTA baseline, code_change_summary
出力: round_<i>/feedback.json
注意: factor.py のソースコードは渡さない（情報分離原則）
```

#### f. 状態更新
- `round_<i>/manifest.json` にステータス・タイムスタンプ記録
- `trace.json` に追記
- ラウンドサマリを表示

### 3. 最終レポート
全ラウンド完了後:
- ラウンド一覧テーブル（仮説, メトリクス, 判定）
- 最終 SOTA 詳細
- 今後の探索提案

## Resume プロトコル

`trace.json` に途中履歴がある場合:
1. `round_manifest.json` から最終完了ラウンドを特定
2. `manifest.json` の step_idx で未完了ステップを特定
3. 次の未完了ステップから再開

## エラーハンドリング

| エラー | 対応 |
|--------|------|
| Planner スキーマ不正 (3回) | ラウンドスキップ、manifest に記録 |
| Coder 構文エラー | バックテスト失敗 → Evaluator が status=failed を評価 |
| バックテストタイムアウト | run_result.json に status=timeout |
| Evaluator スキーマ不正 (3回) | 評価スキップ、decision=false |
