# RD Loop Plan — {{RUN_ID}}

> テンプレート: `.claude/templates/rdloop-plan.md`
> コピー元スキル: `qlib-rd-loop`

## 設定

| 項目 | 値 |
|------|-----|
| run_id | {{RUN_ID}} |
| rounds | {{N_ROUNDS}} |
| artifact_dir | {{ARTIFACT_DIR}} |
| scenario | factor |

## Phase 0: 環境準備

- [ ] **0-1** Qlib データ存在確認 (`~/.qlib/qlib_data/cn_data`)
- [ ] **0-2** RD-Agent venv 動作確認 (`python -c "import qlib"`)
- [ ] **0-3** Codex CLI 動作確認 (`codex --version`)
- [ ] **0-4** artifact_dir 作成 + 全ラウンドの `implementations/` ディレクトリ作成
- [ ] **0-5** source_data.h5 生成 → 全ラウンドの `implementations/` に配置
- [ ] **0-6** trace.json 初期化（新規）または読み込み（Resume）

## Phase 1: データ品質検証（初回のみ）

- [ ] **1-1** source_data.h5 の各カラム欠損率を検査
- [ ] **1-2** `data_quality.json` を artifact_dir に書き出し
- [ ] **1-3** usable_columns を確認・ログ出力

## Phase 2: ラウンド実行

### Round {{i}} / {{N_ROUNDS}}

#### 2a. TraceView 構築
- [ ] **2a** trace.json から TraceView を構築（SOTA, 失敗仮説, data_quality）

#### 2b. 仮説生成 → Planner サブエージェント
- [ ] **2b-1** Planner サブエージェント起動（Agent tool, subagent_type=Explore）
- [ ] **2b-2** hypothesis.json 出力確認（スキーマ検証）
- [ ] **2b-3** experiment.json 出力確認（factor_name が有効な識別子か）

#### 2c. コード生成 → Codex CLI
- [ ] **2c-1** `codex exec --full-auto` 実行
- [ ] **2c-2** factor.py 生成確認
- [ ] **2c-3** 構文検証（`python -c "import py_compile; py_compile.compile('factor.py')"`)

#### 2d. バックテスト → Bash 直接
- [ ] **2d-1** `python factor.py` 実行（RD-Agent venv）
- [ ] **2d-2** result.h5 生成確認
- [ ] **2d-3** IC メトリクス計算（`/tmp/calc_ic.py` 実行）
- [ ] **2d-4** run_result.json 確認

#### 2e. 評価 → Evaluator サブエージェント
- [ ] **2e-1** Evaluator サブエージェント起動（Agent tool）
- [ ] **2e-2** feedback.json 出力確認
- [ ] **2e-3** decision 判定（true=SOTA更新, false=棄却）

#### 2f. 状態更新
- [ ] **2f-1** trace.json に追記
- [ ] **2f-2** ラウンドサマリを表示

---

> **Round テンプレート**: 上記 2a〜2f を各ラウンドで繰り返す。
> ラウンド開始時にこのセクションをコピーして `Round {{i}}` に書き換えること。

## Phase 3: 最終レポート

- [ ] **3-1** 全ラウンド結果テーブル出力
- [ ] **3-2** 最終 SOTA 詳細表示
- [ ] **3-3** 今後の探索提案

## チェックポイントルール

1. 各 `- [ ]` をクリアしたら `- [x]` に更新すること
2. エラー発生時は該当タスクに `⚠️ ERROR: <概要>` を追記
3. ラウンドスキップ時は全タスクに `⏭️ SKIP` を追記
4. Phase 2 のラウンドセクションは実行前にコピーして展開すること
