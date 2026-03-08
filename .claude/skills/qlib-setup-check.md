---
name: qlib-setup-check
description: Verify that all prerequisites for running the Qlib R&D loop are met. Use when starting a new session or before running the loop.
---

# Qlib R&D ループ セットアップ検証

R&D ループ実行前に必要な環境・データ・ツールを検証する。

## チェックリスト

以下を順番に Bash で検証し、結果を表示する。

### 1. Python 仮想環境

```bash
cd RD-Agent-with-Claudex && source .venv/bin/activate
python --version  # Python 3.12 が必要
```

**失敗時**: `uv venv .venv --python 3.12 && uv pip install -e .`

### 2. Qlib インストール

```bash
python -c "import qlib; print(f'qlib {qlib.__version__}')"
```

**失敗時**: `uv pip install -e ../Qlib-with-Claudex/`

### 3. Qlib データ

```bash
ls ~/.qlib/qlib_data/cn_data/calendars/day.txt && \
  echo "Data exists" && \
  head -1 ~/.qlib/qlib_data/cn_data/calendars/day.txt && \
  tail -1 ~/.qlib/qlib_data/cn_data/calendars/day.txt
```

**失敗時**:
```bash
cd Qlib-with-Claudex/scripts
python get_data.py qlib_data --name qlib_data_simple \
  --target_dir ~/.qlib/qlib_data/cn_data --region cn
```

### 4. 主要 Python パッケージ

```bash
python -c "
import pandas, numpy, tables
print(f'pandas {pandas.__version__}')
print(f'numpy {numpy.__version__}')
print(f'pytables {tables.__version__}')
"
```

**失敗時**: `uv pip install tables`

### 5. Codex CLI

```bash
which codex && codex --version
```

**失敗時**: `bun install -g @anthropic-ai/codex` または `npm install -g @anthropic-ai/codex`

### 6. Adapter テスト

```bash
cd RD-Agent-with-Claudex && pytest test/adapters/ -v --tb=short 2>&1 | tail -5
```

**失敗時**: テストエラー内容を確認して修正

## 出力フォーマット

各チェックの結果を以下のテーブルで表示:

```
| # | チェック項目 | 状態 | 詳細 |
|---|------------|------|------|
| 1 | Python venv | OK | 3.12.x |
| 2 | Qlib | OK | 0.9.8.dev27 |
| 3 | Qlib データ | OK | 2005-01-04 〜 2021-06-11 |
| 4 | pytables | OK | 3.x.x |
| 5 | Codex CLI | OK | 0.97.0 |
| 6 | Adapter テスト | OK | 38 passed, 1 skipped |
```

全て OK なら「R&D ループ実行可能」と表示。
NG がある場合は修正手順を提示。
