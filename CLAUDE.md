# Qlib-with-Claudex / RD-Agent-with-Claudex

Microsoft Qlib と RD-Agent をフォークし、Claude Code がファクター研究ループを自律実行する OSS。

## Quick Start

```bash
# 1. 環境セットアップ
cd RD-Agent-with-Claudex
source .venv/bin/activate   # Python 3.12 (uv)

# 2. Qlib データ取得（初回のみ）
cd ../Qlib-with-Claudex/scripts
python get_data.py qlib_data --name qlib_data_simple \
  --target_dir ~/.qlib/qlib_data/cn_data --region cn

# 3. 既存テスト実行（38 pass）
cd ../../RD-Agent-with-Claudex
pytest test/adapters/ -v
```

## R&D ループの実行

Claude Code に以下のように依頼する:

> 「ファクター R&D ループを 3 ラウンド回してください」

ループは自動で以下を繰り返す:

1. **Planner** (Agent tool) → 仮説 + 実験仕様（hypothesis.json, experiment.json）
2. **Coder** (`codex exec --full-auto`) → factor.py 生成
3. **Backtest** (Bash) → `python factor.py`（source_data.h5 → result.h5、RD-Agent venv で実行）
4. **IC 計算** (Bash) → run_result.json（IC/IR/RankIC）
5. **Evaluator** (Agent tool) → feedback.json（IC > 0.03 で SOTA 採用）

詳細: `.claude/skills/qlib-rd-loop.md`

## Project Structure

```
Qlib/
├── Qlib-with-Claudex/           # microsoft/qlib フォーク
├── RD-Agent-with-Claudex/       # microsoft/RD-Agent フォーク
│   ├── rdagent/adapters/        # 5スロット Adapter 層
│   ├── rdagent/oai/backend/     # LLM バックエンド（LiteLLM + Claude shim）
│   ├── rdagent/core/            # データ構造（Hypothesis, Trace, Experiment）
│   ├── test/adapters/           # Adapter テスト（38 pass）
│   └── .venv/                   # Python 3.12 仮想環境
├── .claude/
│   ├── skills/                  # 5 スキル定義
│   ├── subagents/               # Planner / Coder / Evaluator
│   └── artifacts/rdloop/        # 実行結果（trace.json が SSOT）
└── docs/plans/                  # 設計ドキュメント
```

## Skills & Subagents

| スキル | 用途 |
|--------|------|
| qlib-rd-loop | ループ全体のオーケストレーション |
| qlib-hypothesis-gen | Planner 向け仮説生成ガイドライン |
| qlib-factor-implement | Coder 向け factor.py 実装ガイドライン |
| qlib-experiment-eval | Evaluator 向け判定基準 |
| qlib-artifact-inspect | artifact ディレクトリの検査・IC 確認 |

| サブエージェント | 実行方法 | 役割 |
|----------------|---------|------|
| Planner | Agent tool | 仮説生成 + 実験設計（TraceView → JSON） |
| Coder | **Codex CLI** (`codex exec`) | factor.py 生成（experiment.json → Python） |
| Evaluator | Agent tool | メトリクス評価（IC ベース判定、コード非参照） |

## Key Architecture

**制御の反転**: Claude Code が Python/Qlib/Codex を道具として使う（API Key 不要）。

```
Claude Code (オーケストレーター)
  ├── Planner  → Agent tool でサブエージェントに仮説生成を委託
  ├── Coder   → codex exec --full-auto で factor.py 生成
  ├── Backtest → Bash で python factor.py (RD-Agent venv)
  ├── IC計算   → Bash でスクリプト実行
  └── Evaluator → Agent tool でサブエージェントに評価を委託
```

## macOS 注意事項

- `multiprocessing.set_start_method("fork", force=True)` が必須
- Qlib のデータ取得はスクリプトファイルで実行（stdin 不可）
- Simple データの期間: 2005〜2021年6月

## Conventions

- ドキュメントは簡潔な日本語
- ライセンス: MIT 継承
- ブランド名: `with-Claudex`
- パッケージ管理: uv
- テスト: `pytest test/adapters/ -v`
