# Qlib-with-Claudex / RD-Agent-with-Claudex

Microsoft Qlib と RD-Agent をフォークし、OpenAI API 依存を Claude Code + サブエージェント + Codex に置き換えた OSS。

## Project Structure

```
Qlib/
├── Qlib-with-Claudex/       # microsoft/qlib フォーク（量的投資フレームワーク）
├── RD-Agent-with-Claudex/    # microsoft/RD-Agent フォーク（LLM駆動 R&D エージェント）
└── docs/plans/               # 設計ドキュメント群
```

## Key Architecture

**制御の反転**: `Python → LLM API` から `Claude Code → Python/Qlib を道具として使う` へ。

RD-Agent の5ステップループ（propose → exp_gen → coding → running → feedback）を
Claude Code コンポーネント（Planner サブエージェント / Codex / Bash / Evaluator サブエージェント）で置換する。

### Adapter 層

RDLoop の5スロットに対応する Adapter クラスで外部エージェント出力を RD-Agent のデータ構造に変換:

| スロット | Adapter | 詳細 |
|---|---|---|
| hypothesis_gen | ClaudeCodeFactorHypothesisGenAdapter | 仮説生成 |
| hypothesis2experiment | ClaudeCodeFactorH2EAdapter | 仮説→実験仕様 |
| coder | ClaudeCodeFactorCoderAdapter | Codex でコード生成 |
| runner | QlibFactorRunner（既存） | Qlib バックテスト実行 |
| summarizer | ClaudeCodeFactorSummarizerAdapter | 結果分析・フィードバック |

## Design Documents

- [基本方針](docs/plans/基本方針.md) — プロジェクト概要・フェーズ定義
- [OpenAI依存箇所レポート](docs/plans/OpenAI依存箇所レポート.md) — 依存分析結果
- [ClaudeCode置換設計](docs/plans/ClaudeCode置換設計.md) — アーキテクチャ・artifact・スキル設計
- [Adapter詳細設計](docs/plans/Adapter詳細設計.md) — Adapter契約・Schema・Shim・テスト仕様

## Conventions

- ドキュメントは簡潔な日本語
- ライセンス: MIT 継承
- ブランド名: `with-Claudex`
- Phase 1 スコープ: factor シナリオ限定

## Important Paths (RD-Agent)

- `rdagent/oai/backend/` — LLM バックエンド（置換対象）
- `rdagent/core/` — データ構造（Hypothesis, Trace, Experiment）— 残す
- `rdagent/components/workflow/rd_loop.py` — メインループ — 内部差し替えで進める
- `rdagent/scenarios/qlib/` — Qlib シナリオ実装
- `rdagent/scenarios/qlib/developer/factor_runner.py` — 実行ロジック — 残す
