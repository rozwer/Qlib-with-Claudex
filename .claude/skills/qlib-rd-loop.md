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

## 前提条件

### Qlib データの準備

```bash
# Qlib-with-Claudex を RD-Agent venv にインストール（uv 使用）
cd RD-Agent-with-Claudex
uv pip install -e ../Qlib-with-Claudex/

# CSI300 Simple データの取得（~50MB, 2005-2021年, 714銘柄）
cd ../Qlib-with-Claudex/scripts
python get_data.py qlib_data --name qlib_data_simple \
  --target_dir ~/.qlib/qlib_data/cn_data --region cn

# 動作確認
python -c "import qlib; print(qlib.__version__)"
```

### source_data.h5 の作成

**重要**: macOS では `multiprocessing.set_start_method("fork", force=True)` が必須。
スクリプトファイルとして実行すること（stdin 不可、multiprocessing spawn エラー回避）。

```python
# /tmp/prepare_source_data.py として保存して実行
import multiprocessing
multiprocessing.set_start_method("fork", force=True)
import qlib, pandas as pd

qlib.init(provider_uri="~/.qlib/qlib_data/cn_data", region="cn")
from qlib.data import D

instruments = D.instruments("csi300")
stock_list = D.list_instruments(instruments, start_time="2019-01-01", end_time="2020-12-31")
symbols = sorted(stock_list.keys())[:50]  # テスト用50銘柄

df = D.features(
    symbols,
    ["$open", "$close", "$high", "$low", "$volume", "$vwap"],
    start_time="2019-01-01", end_time="2020-12-31"
)
df.columns = ["open", "close", "high", "low", "volume", "vwap"]

# 各ラウンドの workspace に配置
for r in range(N_ROUNDS):
    df.to_hdf(f"{ARTIFACT_DIR}/round_{r}/implementations/source_data.h5", key="data")
```

**注意**: Simple データの期間は 2005〜2021年6月。2022年以降は空になる。

## フロー

### 1. 初期化

- `artifact_dir/trace.json` が存在？
  - YES → Resume: trace を読み込み次のラウンドを特定
  - NO → 新規: ディレクトリ作成、trace.json 初期化

### 1b. データ品質検証（初回のみ）

source_data.h5 の各カラムの欠損率を検証し、`artifact_dir/data_quality.json` に保存する。
この情報は全ラウンドの Planner に渡される。

```python
# /tmp/check_data_quality.py として実行
import multiprocessing
multiprocessing.set_start_method("fork", force=True)
import pandas as pd, json

df = pd.read_hdf(f"{ARTIFACT_DIR}/round_0/implementations/source_data.h5", key="data")
quality = {
    "total_rows": len(df),
    "columns": {}
}
for col in df.columns:
    notna = int(df[col].notna().sum())
    quality["columns"][col] = {
        "notna": notna,
        "missing_pct": round((1 - notna / len(df)) * 100, 1),
        "usable": notna > len(df) * 0.5  # 50%以上あれば利用可能
    }
quality["usable_columns"] = [c for c, v in quality["columns"].items() if v["usable"]]

with open(f"{ARTIFACT_DIR}/data_quality.json", "w") as f:
    json.dump(quality, f, indent=2)
```

**出力例**:
```json
{
  "usable_columns": ["open", "close", "high", "low", "volume"],
  "columns": {
    "vwap": {"notna": 0, "missing_pct": 100.0, "usable": false}
  }
}
```

### 2. ラウンドループ（N 回繰り返し）

各ラウンド `i`:

#### a. TraceView 構築
過去実験の圧縮サマリを生成（SOTA, 直近結果, 失敗仮説）。
`data_quality.json` の `usable_columns` も TraceView に含める。

#### b. Plan → Planner サブエージェント
```
Agent tool に委託（.claude/subagents/planner.md 参照）
入力: TraceView, Scenario, data_quality.json の usable_columns
出力: round_<i>/hypothesis.json, round_<i>/experiment.json
```

#### c. Implement → Codex CLI
```bash
codex exec --full-auto -C <workspace_path> \
  "以下のファクター仕様に基づき、<workspace_path>/factor.py を生成してください。
   仕様: $(cat <artifact_dir>/round_<i>/experiment.json)
   ルール: source_data.h5→result.h5, MultiIndex対応, look-ahead bias なし"
```
**注意**: Codex は自身の Python 環境を使う。factor.py の実行は RD-Agent の venv で行うこと。

#### d. Run Backtest → Bash 直接実行
```bash
cd <artifact_dir>/round_<i>/implementations && python factor.py
# source_data.h5 → result.h5 が生成される
```

#### d2. IC メトリクス計算 → Bash 直接実行

factor.py 実行後、result.h5 から IC/IR/RankIC を算出して run_result.json を生成:

```python
# /tmp/calc_ic.py として保存して実行（stdin 不可）
# 引数: workspace artifact_dir round_idx factor_name
import multiprocessing
multiprocessing.set_start_method("fork", force=True)
import pandas as pd, numpy as np, json, sys

workspace, artifact_dir = sys.argv[1], sys.argv[2]
round_idx, factor_name = int(sys.argv[3]), sys.argv[4]

result = pd.read_hdf(f"{workspace}/result.h5")
source = pd.read_hdf(f"{workspace}/source_data.h5")

# MultiIndex 順序に依存しない: reset_index + merge 方式
result_df = result.reset_index()
source_df = source.reset_index()

factor_col = [c for c in result_df.columns if c not in ("instrument", "datetime")][0]
result_df = result_df.rename(columns={factor_col: "factor"})

source_df = source_df.sort_values(["instrument", "datetime"])
source_df["forward_return"] = source_df.groupby("instrument")["close"].transform(
    lambda s: s.pct_change().shift(-1)
)

merged = pd.merge(result_df[["instrument", "datetime", "factor"]],
                   source_df[["instrument", "datetime", "forward_return"]],
                   on=["instrument", "datetime"])
merged = merged.dropna(subset=["factor", "forward_return"])

# Daily IC / Rank IC（groupby.apply の戻り値型問題を回避するためループ）
ic_list, rank_ic_list = [], []
for dt, grp in merged.groupby("datetime"):
    if len(grp) < 5:
        continue
    ic_list.append(grp["factor"].corr(grp["forward_return"]))
    rank_ic_list.append(grp["factor"].rank().corr(grp["forward_return"].rank()))

daily_ic = pd.Series(ic_list).dropna()
daily_rank_ic = pd.Series(rank_ic_list).dropna()

run_result = {
    "status": "success",
    "factor_name": factor_name,
    "metrics": {
        "ic_mean": round(float(daily_ic.mean()), 6),
        "ic_std": round(float(daily_ic.std()), 6),
        "ir": round(float(daily_ic.mean() / daily_ic.std()), 6),
        "rank_ic_mean": round(float(daily_rank_ic.mean()), 6),
        "daily_ic_positive_ratio": round(float((daily_ic > 0).mean()), 4),
        "n_observations": int(merged.shape[0]),
        "n_days": int(len(daily_ic))
    }
}
with open(f"{artifact_dir}/round_{round_idx}/run_result.json", "w") as f:
    json.dump(run_result, f, indent=2)
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
