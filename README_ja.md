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
# 1. サブモジュールごとクローン（1コマンド）
git clone --recurse-submodules git@github.com:rozwer/Qlib-with-Claudex.git Qlib
cd Qlib

# すでにクローン済みの場合:
# git submodule update --init --recursive

# 2. RD-Agent 仮想環境セットアップ
cd RD-Agent-with-Claudex
uv venv --python 3.12 && source .venv/bin/activate
uv pip install -e ".[dev]"

# 3. Qlib をvenvにインストール
uv pip install -e ../Qlib-with-Claudex/

# 4. Qlib 市場データダウンロード (~50MB, CSI300 2005-2021)
cd ../Qlib-with-Claudex/scripts
python get_data.py qlib_data --name qlib_data_simple \
  --target_dir ~/.qlib/qlib_data/cn_data --region cn
cd ../..

# 5. source_data.h5 生成（クイックテスト）
python scripts/prepare_source_data.py --output /tmp/source_data.h5

# 6. データ品質チェック
python scripts/check_data_quality.py /tmp/source_data.h5 /tmp/data_quality.json
```

## スクリプト

| スクリプト | 用途 |
|-----------|------|
| `scripts/prepare_source_data.py` | Qlib 市場データから source_data.h5 を生成 |
| `scripts/calc_ic.py` | バックテスト結果から IC/IR/RankIC を計算 |
| `scripts/check_data_quality.py` | カラム欠損率を検査、data_quality.json を出力 |

```bash
# R&D ループ用に source_data.h5 を生成（5ラウンド、50銘柄、2019-2020）
source RD-Agent-with-Claudex/.venv/bin/activate
python scripts/prepare_source_data.py --output_dir .claude/artifacts/rdloop/my_run --rounds 5

# カスタマイズ: 100銘柄、長期間
python scripts/prepare_source_data.py --output_dir .claude/artifacts/rdloop/my_run \
  --rounds 10 --n_instruments 100 --start_time 2015-01-01 --end_time 2020-12-31
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
