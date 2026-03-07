# Phase 1B: Planner + Evaluator 自動化

作成日: 2026-03-07
起点: Phase 1A の Adapter 検証完了（固定入力での artifact 生成・再開・shim 動作確認済み）
目的: factor 1個、1ラウンド、完全自律で完走。Planner / Evaluator サブエージェントとスキルを実装し、人手介入なしの RDLoop を実現する。
依存: Phase 1A 完了

実装スコープ:
- スキル原本は親 repo の `docs/skills/`
- RD-Agent 側の実装先は `RD-Agent-with-Claudex/`
- artifact 出力先は親 repo ルートの `.claude/artifacts/rdloop/<run_id>/`

---

## レビュー反映事項

- `Trace.get_sota_hypothesis_and_experiment()` と既存 feedback/runner 実装は「最高 IC」ではなく「直近の accepted experiment」を SOTA とみなす。Phase 1B もこの定義に揃える。
- `based_experiments` の初期値は空ではなく baseline 用 `QlibFactorExperiment(sub_tasks=[])` を含める。Planner 出力仕様も 1A と揃える。
- Evaluator にソースコードを渡さない方針は維持するが、必須の `code_change_summary` を生成するため `exp.prop_dev_feedback` や workspace `change_summary` の要約は入力に含める。
- skill ファイルの最終配置はツール依存なので、Phase 1B ではソースを `docs/skills/` に置く。`.claude/skills/` や `.codex/skills/` への配備は Phase 3 で決める。
- 「完全自律」と「各 round で続行確認」は両立しないため、Phase 1B の標準フローは無確認で進む。対話停止はオプション機能として後置する。

---

## Phase 1B.1: Planner サブエージェント実装

### 1B.1.1 TraceView 生成ロジック

Trace オブジェクト全体をサブエージェントに渡すと文脈汚染が起きる。
`trace_view.py` で Trace を軽量 JSON に圧縮し、Planner / Evaluator に渡す。

**TraceView スキーマ:**

```json
{
  "total_rounds": 5,
  "sota": {
    "round_id": 3,
    "hypothesis": "出来高加重移動平均乖離率",
    "IC": 0.045,
    "annualized_return": 0.12
  },
  "recent_rounds": [
    {
      "round_id": 4,
      "hypothesis": "ボリンジャーバンド幅正規化",
      "decision": false,
      "key_metrics": {"IC": 0.031, "annualized_return": 0.08},
      "key_observation": "IC 低下 -31%、仮説棄却"
    }
  ],
  "failed_hypotheses_summary": [
    "窓幅固定は効果薄",
    "セクター分割は過学習傾向"
  ]
}
```

**生成ルール:**

- `total_rounds`: `len(trace.hist)`
- `sota`: `trace.hist` を末尾から走査して最初に見つかった `decision=True` の round。初回は `null`
- `recent_rounds`: 直近 3〜5 round（設定可能、デフォルト 3）。各 round から hypothesis 文、decision、主要メトリクス、key_observation を抽出
- `failed_hypotheses_summary`: `decision=False` の round から concise_reason を収集し重複排除。最大 10 件

### 1B.1.2 Planner プロンプト設計

**入力:**
- TraceView JSON
- Qlib factor シナリオ記述（ドメイン知識: 利用可能データ列、ファクター設計の制約、評価指標の意味）

**プロンプト構成:**
1. ロール定義: 量的投資ファクター研究者として振る舞う
2. TraceView を提示し、過去の成功・失敗パターンを踏まえた仮説立案を指示
3. 出力フォーマットを JSON Schema で厳密指定
4. 「過去に失敗した仮説の再提案を避けよ」という制約

**出力:** 2つの JSON ファイル

`hypothesis.json` 必須フィールド:
| フィールド | 型 | 説明 |
|---|---|---|
| hypothesis | str | 仮説の全文記述 |
| reason | str | 仮説の根拠（詳細） |
| concise_reason | str | 根拠の要約（1〜2文） |
| concise_observation | str | 観察の要約 |
| concise_justification | str | 正当化の要約 |
| concise_knowledge | str | 関連知識の要約 |

`experiment.json` 必須フィールド:
| フィールド | 型 | 説明 |
|---|---|---|
| sub_tasks | list[FactorTask] | factor_name, factor_description, factor_formulation, variables を含む |
| sub_workspace_list | list[null] | len(sub_tasks) に揃えて初期化（Codex が後で埋める） |
| experiment_workspace | obj | QlibFBWorkspace の template_folder_path 等 |
| based_experiments | list[str] | artifact 上は experiment ref。初回は baseline ref、その後は末尾に直近 accepted experiment ref を持つ |

### 1B.1.3 エラーハンドリング

1. Planner 出力を JSON Schema でバリデーション（jsonschema ライブラリ使用）
2. バリデーション失敗時: エラーメッセージを付与して Planner に再投入（最大 2 回リトライ）
3. 3回失敗で `schema_failure` として manifest に記録し、round をスキップ

### タスク表

| Task | 内容 | 成果物 | Status |
|------|------|--------|--------|
| 1B.1.1 | TraceView 生成関数実装 | `trace_view.py` | cc:TODO |
| 1B.1.2 | Planner プロンプトテンプレート作成 | `planner.py` 内テンプレート | cc:TODO |
| 1B.1.3 | Planner サブエージェント起動・応答パース | `planner.py` launcher | cc:TODO |
| 1B.1.4 | 出力バリデーション + リトライロジック | `planner.py` validator | cc:TODO |

---

## Phase 1B.2: Evaluator サブエージェント実装

### 1B.2.1 入出力設計

**入力:**
- `run_result.json`: status, result メトリクス (IC, annualized_return 等), stdout 抜粋
- 実験コンテキスト: hypothesis 文、factor_description、factor_formulation
- ベースライン / SOTA メトリクス（TraceView の `sota` セクション）

**出力 `feedback.json`:**

| フィールド | 型 | 必須 | 説明 |
|---|---|---|---|
| reason | str | o | 判定理由の詳細 |
| decision | bool | o | SOTA 更新するか |
| code_change_summary | str | o | コード変更の要約 |
| observations | str | - | 実験結果の観察 |
| hypothesis_evaluation | str | - | 仮説の妥当性評価 |
| new_hypothesis | str | - | 次ラウンドへの示唆 |
| acceptable | bool | - | 最低品質基準を満たすか |

### 1B.2.2 情報分離原則

Evaluator には**実装コード（factor.py）を渡さない**。
理由: 実装者と評価者の癒着を防ぐ。Evaluator はメトリクスと仮説の整合性のみで判断する。

渡す情報:
- 仮説の記述（何を試みたか）
- 実行結果のメトリクス（何が得られたか）
- SOTA との比較値
- `prop_dev_feedback` / workspace `change_summary` 由来のコード変更要約

渡さない情報:
- factor.py のソースコード
- Codex の中間出力・修正履歴
- 実装上の技術的判断

### 1B.2.3 Evaluator プロンプト設計

1. ロール定義: 量的投資の実験評価者として振る舞う
2. SOTA メトリクスと今回メトリクスの比較表を提示
3. 判定基準を明示: IC が SOTA を上回り、かつドローダウンが許容範囲内なら `decision=true`
4. 出力フォーマットを JSON Schema で厳密指定

### タスク表

| Task | 内容 | 成果物 | Status |
|------|------|--------|--------|
| 1B.2.1 | Evaluator 入力組み立てロジック | `evaluator.py` input builder | cc:TODO |
| 1B.2.2 | Evaluator プロンプトテンプレート作成 | `evaluator.py` 内テンプレート | cc:TODO |
| 1B.2.3 | Evaluator サブエージェント起動・応答パース | `evaluator.py` launcher | cc:TODO |
| 1B.2.4 | 出力バリデーション + リトライロジック | `evaluator.py` validator | cc:TODO |

---

## Phase 1B.3: スキル実装

### 1B.3.1 qlib-rd-loop スキル

全体ループを制御する起点スキル。Phase 1B ではソースを `docs/skills/qlib-rd-loop.md` として管理する。

**フロー:**

```
1. 設定確認
   - 対象シナリオ: factor（Phase 1 固定）
   - ラウンド数（デフォルト 5、ユーザー指定可能）
   - artifact ディレクトリ: .claude/artifacts/rdloop/<run_id>/

2. Trace 読み込み or 新規作成
   - trace.json が存在すれば読み込み（resume）
   - 存在しなければ空の Trace を初期化

3. ラウンドループ（N 回繰り返し）
   a. TraceView 生成（trace_view.py）
   b. Planner サブエージェント起動
      → hypothesis.json + experiment.json を round_<N>/ に保存
   c. Codex 起動（qlib-factor-implement スキル適用）
      → implementations/ にコード生成
   d. Bash で Qlib バックテスト実行
      → run_result.json + stdout.log + stderr.log 保存
   e. Evaluator サブエージェント起動
      → feedback.json を round_<N>/ に保存
   f. manifest.json 更新（status, timestamps, failure_type）
   g. trace.json 更新（hist に experiment_ref + feedback_ref 追加）
   h. ユーザーに結果サマリー表示
      - 仮説、主要メトリクス、decision、SOTA 状況

4. 最終レポート生成
   - 全ラウンドの仮説・メトリクス・decision の一覧表
   - 最終 SOTA の詳細
```

### 1B.3.2 qlib-factor-implement スキル

Codex がファクターコードを生成する際のガイドライン。Phase 1B ではソースを `docs/skills/qlib-factor-implement.md` として管理する。

**内容:**

1. **Qlib factor 実行仕様**
   - `factor.py` は `FactorFBWorkspace.execute()` から直接実行される
   - 実行後に `result.h5` を workspace 直下へ出力する
   - `target_task.version == 1` 前提では、ワークスペースにリンクされた市場データを読み込んで factor 値 DataFrame を生成する

2. **FBWorkspace テンプレート構造**
   ```
   workspace/
   ├── factor.py          # Codex が生成するファイル
   ├── conf_baseline.yaml
   ├── conf_combined_factors.yaml
   ├── conf_combined_factors_sota_model.yaml
   └── read_exp_res.py
   ```

3. **テンプレートコード**: factor.py の雛形を提示

4. **成功例**: IC > 0.03 を達成した factor.py の構造パターン

5. **失敗例と回避策**: よくあるエラー（データ列名ミス、look-ahead bias 等）

6. **バリデーション基準**
   - Python syntax check (`py_compile`)
   - `result.h5` を生成する実行パスが存在すること
   - `factor.py` が workspace テンプレートと競合しないこと

7. **出力先**: `round_<N>/implementations/factor.py`

### タスク表

| Task | 内容 | 成果物 | Status |
|------|------|--------|--------|
| 1B.3.1 | qlib-rd-loop スキル定義 | `docs/skills/qlib-rd-loop.md` | cc:TODO |
| 1B.3.2 | qlib-factor-implement スキル定義 | `docs/skills/qlib-factor-implement.md` | cc:TODO |
| 1B.3.3 | ループ制御ロジック実装（resume 対応含む） | `planner.py` / skill 内 | cc:TODO |

---

## Phase 1B.4: 統合テスト

### 1B.4.1 End-to-end 1ラウンドテスト

実 Claude Code サブエージェントを使用した 1 ラウンド完走テスト。

**検証項目:**
- [ ] Planner が TraceView（初回は空）から hypothesis.json + experiment.json を生成
- [ ] Codex が experiment.json から implementations/factor.py を生成
- [ ] Bash で Qlib バックテストが実行され run_result.json が生成
- [ ] Evaluator が feedback.json を生成
- [ ] trace.json の hist に 1 エントリ追加
- [ ] manifest.json の status が "completed"
- [ ] 全 artifact が `round_0/` に存在

### 1B.4.2 マルチラウンドテスト（3ラウンド）

**検証項目:**
- [ ] SOTA 追跡: Round 1 で decision=true の場合、Round 2 の TraceView に SOTA として反映
- [ ] 仮説進化: Planner が過去の失敗仮説を避けて新しい仮説を提案
- [ ] based_experiments: Round 2 以降で前回 SOTA の experiment が参照される
- [ ] trace.json の hist が 3 エントリ、dag_parent が正しい親子関係

### 1B.4.3 エラーリカバリテスト

| シナリオ | 期待動作 |
|---|---|
| Codex が構文エラーのあるコードを生成 | Bash 実行失敗 → run_result.json の status="failed" → Evaluator が decision=false |
| Planner が不正 JSON を返す | バリデーション失敗 → リトライ（最大2回）→ 3回失敗で schema_failure |
| Qlib バックテストがタイムアウト | run_result.json の status="timeout" → Evaluator が適切に判定 |
| Evaluator が不正 JSON を返す | バリデーション失敗 → リトライ → 3回失敗で round スキップ |

---

## 受け入れ条件

- [ ] TraceView が Trace から正しく圧縮 JSON を生成する（SOTA 抽出、recent_rounds、failed_hypotheses）
- [ ] Planner が TraceView から hypothesis.json と experiment.json を生成し、JSON Schema バリデーションを通過する
- [ ] Evaluator が run_result.json + コンテキストから feedback.json を生成し、JSON Schema バリデーションを通過する
- [ ] Evaluator に実装コードが渡されていないことを確認（情報分離）
- [ ] qlib-rd-loop スキルで factor 1個・1ラウンドが完全自律完走する
- [ ] qlib-factor-implement スキルで Codex が Qlib 互換の factor.py を生成する
- [ ] 3ラウンド連続実行で SOTA 追跡と仮説進化が動作する
- [ ] バリデーション失敗時のリトライが正しく動作する
- [ ] 全 artifact が所定のディレクトリ構造に保存される

---

## 実装対象ファイル

| ファイル | 種別 | 内容 |
|---|---|---|
| `docs/skills/qlib-rd-loop.md` | 新規 | メインループ制御スキル定義 |
| `docs/skills/qlib-factor-implement.md` | 新規 | Codex 用ファクター実装ガイドライン |
| `RD-Agent-with-Claudex/rdagent/adapters/factor/trace_view.py` | 新規 | Trace → TraceView 圧縮ロジック |
| `RD-Agent-with-Claudex/rdagent/adapters/factor/planner.py` | 新規 | Planner サブエージェント起動・バリデーション |
| `RD-Agent-with-Claudex/rdagent/adapters/factor/evaluator.py` | 新規 | Evaluator サブエージェント起動・バリデーション |
| `RD-Agent-with-Claudex/test/adapters/test_e2e_loop.py` | 新規 | 1ラウンド / 3ラウンド / エラーリカバリの統合テスト |
