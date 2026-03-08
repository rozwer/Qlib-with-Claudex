# Coder サブエージェント（Codex CLI）

Factor RD ループのファクター実装コード生成を担当。
**Codex CLI** を Bash tool 経由で呼び出す。

## 役割

experiment.json のファクター仕様に基づき、Qlib 互換の factor.py を生成する。

## 呼び出し方法

```bash
codex exec --full-auto -C <workspace_path> \
  "以下のファクター仕様に基づき、<workspace_path>/factor.py を生成してください。

   仕様:
   $(cat <artifact_dir>/round_<N>/experiment.json)

   実装ルール:
   - source_data.h5 から pd.read_hdf で読み込み (key='data')
   - columns: open, close, high, low, volume, vwap / MultiIndex: (instrument, datetime) の順序
   - result.h5 に key='data' で書き出し（Series、name は factor_name）
   - groupby(level='instrument').transform() で銘柄別計算（apply は index 崩壊の原因になるため禁止）
   - look-ahead bias なし（shift, rolling のみ）
   - NaN/inf を replace([np.inf, -np.inf], np.nan) で処理
   - 出力 Series の index は入力 DataFrame の index と完全一致させること
   - カラムが全 NaN の場合に備え、使用前に notna().sum() > 0 でチェックすること"
```

## CLI オプション

| オプション | 値 | 説明 |
|-----------|---|------|
| `exec` | - | 非対話モード |
| `--full-auto` | - | 承認不要 + workspace-write sandbox |
| `-C` | workspace path | 作業ディレクトリ（書込み許可） |

## 入力

- **experiment.json**: ファクター仕様（factor_name, formulation, variables）
- experiment.json の内容は prompt にインライン展開して渡す

## 出力ファイル

- `round_<N>/implementations/factor.py` — 実行可能なファクター計算コード

## 注意事項

- Codex は独自の Python 環境を使う（Python 3.14、tables/pytables がない）
- factor.py の**実行**は RD-Agent の venv (`cd RD-Agent-with-Claudex && source .venv/bin/activate`) で行うこと
- Codex は `--full-auto` モードで自律的に `py_compile` やダミーデータテストを実行してバグを検出する
- Codex は既存ファイルを読んでパターンを学習するため、前ラウンドの factor.py が参考になる

## 実戦で判明した問題と対策

| 問題 | 対策 |
|------|------|
| `groupby.apply()` で index が崩壊し全 NaN | `groupby.transform()` を使用する |
| MultiIndex の順序が (instrument, datetime) | `groupby(level=0)` か `groupby(level="instrument")` で統一 |
| カラム（例: vwap）が全 NaN | 使用前に `notna().sum() > 0` でチェック。代替計算（typical price 等）をフォールバックに |
| Codex 環境に tables 未導入 | `py_compile` で構文検証のみ。実データ検証は venv で行う |

## 実装ガイドライン

`.claude/skills/qlib-factor-implement.md` に従う。要点:

- `source_data.h5` から読み込み、`result.h5` に書き出す
- MultiIndex (datetime, instrument) を正しく扱う
- Look-ahead bias を避ける（`.shift(N)` で N > 0、`.rolling()` のみ）
- NaN / inf を適切に処理
- Valid Python syntax であること
