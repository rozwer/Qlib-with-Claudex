[English](README.md) | [日本語](README_ja.md)

# Qlib-with-Claudex

Microsoft Qlib + RD-Agent を Claude Code + Codex で自律駆動する量的投資 R&D フレームワーク。

## 概要

OpenAI API 依存を **Claude Code サブエージェント + Codex CLI** に置き換え、
「Python → LLM API」から「**Claude Code → Python/Qlib を道具として使う**」制御の反転を実現。

## リポジトリ構成

```
Qlib/                          ← このリポジトリ（親）
├── .claude/                   ← Claude Code 設定・スキル・サブエージェント定義
│   ├── skills/                # RD ループ・仮説生成・ファクター実装 etc.
│   ├── subagents/             # Planner / Coder / Evaluator 定義
│   ├── settings.json          # 共有パーミッション
│   └── artifacts/             # 実験アーティファクト
├── Qlib-with-Claudex/         ← microsoft/qlib フォーク（サブプロジェクト）
├── RD-Agent-with-Claudex/     ← microsoft/RD-Agent フォーク（サブプロジェクト）
└── docs/plans/                ← 設計ドキュメント
```

## セットアップ

```bash
# 1. 親リポジトリをクローン
git clone git@github.com:rozwer/Qlib-with-Claudex.git Qlib
cd Qlib

# 2. 子リポジトリをクローン
git clone git@github.com:rozwer/qlib-with-claudex-sub.git Qlib-with-Claudex
git clone git@github.com:rozwer/RD-Agent-with-Claudex.git RD-Agent-with-Claudex

# 3. RD-Agent 仮想環境セットアップ
cd RD-Agent-with-Claudex
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"

# 4. Qlib データダウンロード
python -m qlib.run.get_data qlib_data --target_dir ~/.qlib/qlib_data/cn_data --region cn
```

## R&D ループ

Claude Code が以下のサブエージェントを順に呼び出してファクター探索を自動化:

| ステップ | コンポーネント | 役割 |
|----------|---------------|------|
| 仮説生成 | Planner (Agent tool) | TraceView 分析 → 新仮説提案 |
| コード生成 | Codex CLI (`codex exec --full-auto`) | ファクター計算コード生成 |
| 実行 | Bash (RD-Agent venv) | factor.py 実行 + IC 計算 |
| 評価 | Evaluator (Agent tool) | 結果分析 → フィードバック |

## ライセンス

MIT（Microsoft Qlib / RD-Agent から継承）
