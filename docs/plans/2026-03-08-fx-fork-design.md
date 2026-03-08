# Qlib_FX リポジトリ作成 設計書

## 概要

Claudex シリーズ（Qlib-with-Claudex / RD-Agent-with-Claudex）を FX 対応に寄せるため、独立した親リポジトリ `Qlib_FX/` を作成し、全体コピー後に FX 移行レポートに従って編集を進める。

## 決定事項

| 項目 | 決定 |
|------|------|
| 親ディレクトリ | `/Users/roz/Desktop/Qlib_FX/` |
| サブリポジトリ名 | `Qlib_FX-with-Claudex/`, `RD-Agent_FX-with-Claudex/` |
| コピー方式 | 全体コピー、git history 新規開始 |
| docs の扱い | 全コピー後、株式版設計ドキュメントを `docs/plans/archive/` に移動 |
| `.claude/` | 最小構成で新規作成（CLAUDE.md のみ FX 用に書き直し） |
| FX 移行方針 | Option B: Qlib データ基盤は利用、執行/会計/評価は独立実装 |

## 最終構造

```
/Users/roz/Desktop/Qlib_FX/
├── .git/
├── .gitignore
├── CLAUDE.md                          # FX 用に新規作成
├── Plans.md                           # FX Phase (FX-0〜FX-5)
├── Qlib_FX-with-Claudex/
│   ├── .git/                          # upstream: microsoft/qlib
│   ├── CLAUDE.md                      # FX 用
│   ├── qlib/                          # Layer 1 編集対象
│   └── scripts/data_collector/fx/     # N4: 新規
├── RD-Agent_FX-with-Claudex/
│   ├── .git/                          # upstream: microsoft/RD-Agent
│   ├── CLAUDE.md                      # FX 用
│   ├── rdagent/adapters/factor/       # Layer 3 編集対象
│   ├── rdagent/scenarios/qlib/        # Layer 2 編集対象
│   ├── rdagent/scenarios/fx/          # N1-N3: 新規
│   └── test/adapters/                 # Layer 4 編集対象
└── docs/
    ├── plans/
    │   ├── archive/                   # 株式版退避
    │   └── FX移行レポート.md
    ├── skills/                        # FX 用に編集
    └── subagents/                     # FX 用に編集
```

## コピー時の除外対象

| ディレクトリ | 理由 | 推定サイズ削減 |
|-------------|------|---------------|
| `RD-Agent-with-Claudex/.venv/` | Python 仮想環境（再作成可能） | ~500MB |
| `RD-Agent-with-Claudex/git_ignore_folder/` | 生成データ（再生成可能） | ~400MB |
| `RD-Agent-with-Claudex/.pytest_cache/` | キャッシュ | ~1MB |
| `*/.git/` | 各サブリポの git history（新規開始） | ~100MB |
| `Qlib/.claude/` | 株式版の Claude 設定（最小構成で再作成） | ~5MB |

コピー後のサイズ見込み: 約 50MB

## 関連ドキュメント

- [FX移行レポート](FX移行レポート.md) — 変更箇所 39 件 + 新規 4 件の詳細
- [基本方針](基本方針.md) — 元プロジェクトの概要（archive 移動対象）
