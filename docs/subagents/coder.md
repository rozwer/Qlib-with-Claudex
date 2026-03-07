# Coder サブエージェント

Factor RD ループのファクター実装コード生成を担当するサブエージェント。
Agent tool で起動される。

## 役割

experiment.json のファクター仕様に基づき、Qlib 互換の factor.py を生成する。

## 入力

Agent tool 呼び出し時に prompt として渡す:

- **experiment.json**: ファクター仕様（factor_name, formulation, variables）
- **hypothesis.json**: 仮説コンテキスト
- **Workspace path**: source_data.h5 がある作業ディレクトリ

## 出力ファイル

サブエージェントが直接書き込む:

- `round_<N>/implementations/factor.py` — 実行可能なファクター計算コード

## 実装ガイドライン

`.claude/skills/qlib-factor-implement.md` に従う。要点:

- `source_data.h5` から読み込み、`result.h5` に書き出す
- MultiIndex (datetime, instrument) を正しく扱う
- Look-ahead bias を避ける（`.shift(N)` で N > 0、`.rolling()` のみ）
- NaN / inf を適切に処理
- Valid Python syntax であること

## 呼び出しパターン

```
Agent tool:
  prompt: |
    あなたは Coder サブエージェントです。
    以下のファクター仕様に基づき、factor.py を生成してください。

    experiment.json: {experiment_content}
    hypothesis: {hypothesis_content}
    出力先: {artifact_dir}/round_{N}/implementations/factor.py

    実装ガイドラインは .claude/skills/qlib-factor-implement.md に従うこと。
```
