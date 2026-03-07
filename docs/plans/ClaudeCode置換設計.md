# Claude Code 置換設計

## 設計思想: 制御の反転

現在: `Python (RD-Agent) → LLM API → レスポンス → Python で処理`
目標: `Claude Code → Python/Qlib を道具として使う`

RD-Agent のワークフローロジックを Claude Code のスキル/フック/サブエージェントとして再実装する。
ただし RD-Agent を「自律エージェント」から「実験カーネル」に作り替える再設計であり、単なるバックエンド差し替えではない。

> 詳細設計は [Adapter詳細設計.md](Adapter詳細設計.md) を参照。

---

## 現在の RD-Agent ループ（5ステップ）

```
propose → exp_gen → coding → running → feedback → (record → ループ)
```

| ステップ | 現在の実装 | LLM呼び出し | Claude Code での担当 |
|---|---|---|---|
| 1. propose | HypothesisGen.gen() | あり | Claude Planner サブエージェント |
| 2. exp_gen | Hypothesis2Experiment.convert() | あり | Claude Planner サブエージェント |
| 3. coding | CoSTEER.develop() | あり(複数回) | Codex |
| 4. running | QlibFactorRunner.develop() | なし(Bash/Docker) | Bash |
| 5. feedback | Experiment2Feedback.generate_feedback() | あり | Claude Evaluator サブエージェント |

---

## 新アーキテクチャ

```
ユーザー ↔ Claude Code（メインセッション）
              │
              ├── スキル: qlib-rd-loop
              │     全体ループを制御する起点スキル
              │
              ├── サブエージェント: Planner
              │     ├── Trace（過去の実験履歴）を読む
              │     ├── 仮説を生成（propose）
              │     └── 仮説を実験仕様に変換（exp_gen）
              │
              ├── Codex: Implementer
              │     ├── 実験仕様からPythonコード生成（coding）
              │     ├── 実行エラー時の修正
              │     └── 進化ループ（最大10回）
              │
              ├── Bash: Runner
              │     ├── Qlibバックテスト実行
              │     └── メトリクス収集
              │
              └── サブエージェント: Evaluator
                    ├── 結果分析（feedback）
                    ├── SOTA比較
                    └── 次仮説の示唆
```

---

## Adapter 層（最重要）

外部エージェント出力と RD-Agent の in-memory オブジェクト / workspace の間を繋ぐ変換層。
この層が設計の最脆弱点であり、最も慎重に設計する必要がある。

### 3つの Adapter Interface

```
PlannerAdapter
  入力: TraceView（圧縮済み履歴サマリー）
  出力: hypothesis.json + experiment.json
  変換先: Hypothesis オブジェクト + Experiment オブジェクト（FactorTask リスト付き）

ImplementerAdapter
  入力: experiment.json + workspace template（FBWorkspace のテンプレート）
  出力: file patch / workspace snapshot（implementations/）
  変換先: exp.sub_workspace_list への注入

EvaluatorAdapter
  入力: run_result.json + baseline metrics + experiment 情報
  出力: feedback.json
  変換先: HypothesisFeedback オブジェクト → Trace に追記
```

### なぜ Adapter が必要か

- RD-Agent は `Developer.develop()` が `Experiment` を **in-place 更新**する契約
- `FBWorkspace` はファイル群として注入され、パス・チェックポイント・復元まで管理
- Claude Code/Codex の出力（テキスト/ファイル）をこの構造に安全に落とす変換が必要
- adapter なしだと「動いているように見えるが再現できない」状態になる

### Adapter の実装方針

Phase 1 では RDLoop の内部クラス差し替え（`BasePropSetting` による注入）で進める。
`RDLoop` 自体は当面残し、全置換しない。

```python
# 概念コード
class ClaudePlannerAdapter(HypothesisGen):
    """hypothesis.json を読んで Hypothesis を返す"""
    def gen(self, trace):
        h = json.load(open(artifact_path / "hypothesis.json"))
        return Hypothesis(**h)

class ClaudeImplementerAdapter(Developer):
    """implementations/ のコードを FBWorkspace に注入"""
    def develop(self, exp):
        for task, impl_file in zip(exp.tasks, impl_files):
            workspace = exp.sub_workspace_list[task]
            workspace.inject_code(impl_file.read_text())
        return exp

class ClaudeEvaluatorAdapter(Experiment2Feedback):
    """feedback.json を読んで HypothesisFeedback を返す"""
    def generate_feedback(self, exp, trace):
        fb = json.load(open(artifact_path / "feedback.json"))
        return HypothesisFeedback(**fb)
```

---

## State Management: 再開機構の統一

### 問題
- 既存 RD-Agent は `LoopBase.dump/load()` でセッション保存・再開している
- 新しい artifact 設計と二重化すると壊れる

### 方針: artifact を Single Source of Truth にする

- 既存の再開機構は Phase 4 で廃止（段階移行）
- Phase 1 では両方を併存させるが、artifact 側を正とする
- trace.json は run-level にトップ1つ。各 round は parent pointer を持つ

```
.claude/artifacts/rdloop/<run_id>/
  ├── trace.json              # SSOT: 全体の実験履歴（run-level に1つ）
  ├── round_manifest.json     # 全 round のインデックス
  └── round_<N>/
      ├── manifest.json       # メタ情報
      ├── hypothesis.json
      ├── experiment.json
      ├── implementations/
      │   └── factor_001.py
      ├── run_result.json
      ├── feedback.json
      ├── environment.json    # 再現性（git SHA, Qlib version, dataset path）
      ├── commands.json       # 実行した bash コマンド, exit code, 所要時間
      ├── stdout.log
      ├── stderr.log
      └── validation.json    # schema 検証結果, parse error, fallback 使用有無
```

### manifest.json（各 round）
```json
{
  "run_id": "abc123",
  "round_id": 3,
  "status": "completed",
  "started_at": "2026-03-07T19:30:00+09:00",
  "ended_at": "2026-03-07T19:45:00+09:00",
  "parent_round_ids": [2],
  "action": "factor",
  "retry_count": 0,
  "schema_version": "1.0.0",
  "failure_type": null
}
```

### 失敗分類

| failure_type | 説明 |
|---|---|
| `schema_failure` | artifact の JSON が schema に合わない |
| `codegen_failure` | Codex がコード生成に失敗 |
| `qlib_failure` | Qlib バックテスト実行エラー |
| `metric_parse_failure` | メトリクス抽出失敗 |
| `timeout` | 実行タイムアウト |
| `approval_blocked` | ユーザーが承認しなかった |

---

## Trace 圧縮（文脈汚染対策）

毎ラウンドの Trace をそのまま Planner/Evaluator に渡すとコンテキスト肥大化する。
**要約された TraceView** を作成してサブエージェントに渡す。

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
      "hypothesis": "...",
      "decision": false,
      "key_observation": "IC 低下 -12%"
    },
    {
      "round_id": 5,
      "hypothesis": "...",
      "decision": false,
      "key_observation": "ドローダウン悪化"
    }
  ],
  "failed_hypotheses_summary": ["窓幅固定は効果薄", "セクター分割は過学習"]
}
```

---

## 既存コードの扱い（修正版）

### APIBackend 依存の規模

- `APIBackend` 系参照: 約198箇所
- `rdagent.oai` 参照: 約81箇所
- 即削除すると import 崩壊する → **compatibility shim で段階移行**

### 残すもの
- `rdagent/core/` — データ構造。ただし外部エージェントが乗れるよう契約を再確認
  - `Hypothesis`, `Trace`, `HypothesisFeedback` → そのまま使える
  - `Developer.develop()` の in-place 更新契約 → Adapter 経由で遵守
  - `FBWorkspace` → template workspace の境界を明確化
- `rdagent/scenarios/qlib/experiment/` — シナリオ定義（実験実行基盤）
- `rdagent/scenarios/qlib/developer/factor_runner.py` — 実行ロジック
- `rdagent/components/workflow/rd_loop.py` — 当面残す（内部クラス差し替えで進める）
- テンプレートシステム（`.prompts`）— Planner/Evaluator のプロンプト参考資料

### 段階的に置換するもの（compatibility shim 経由）
- `rdagent/oai/backend/` → `ExternalAgentBackend` shim を噛ませてから段階移行
- `rdagent/components/proposal/` → PlannerAdapter に段階移行
- `rdagent/components/coder/` → ImplementerAdapter に段階移行
- `rdagent/scenarios/qlib/developer/feedback.py` → EvaluatorAdapter に段階移行

### 最終的に削除するもの（Phase 4）
- `rdagent/oai/backend/deprec.py`
- `rdagent/oai/backend/pydantic_ai.py`
- `rdagent/oai/llm_conf.py` の OpenAI/Azure 設定群
- requirements.txt の `openai`, `pydantic-ai-slim[openai]`
- 既存のセッション保存再開機構

---

## スキル設計

### qlib-rd-loop（メインスキル）

全体ループの起点。ユーザーが `/qlib-rd-loop` で起動。

```
1. 設定確認（対象: factor/model/quant、ラウンド数）
2. 既存 trace.json 読み込み or 新規作成
3. ラウンドループ:
   a. TraceView を生成（圧縮済み履歴サマリー）
   b. Planner サブエージェント起動 → hypothesis.json + experiment.json
   c. Codex 起動 → implementations/
   d. Bash で Qlib バックテスト → run_result.json + stdout/stderr
   e. Evaluator サブエージェント起動 → feedback.json
   f. manifest.json + trace.json 更新
   g. ユーザーに結果サマリー表示、続行確認
4. 最終レポート生成
```

### qlib-factor-implement（Codex用スキル）

Codexがファクターコードを生成する際のガイドライン。

```
- Qlibのファクターインターフェース仕様
- FBWorkspace テンプレート構造
- テンプレートコード
- 成功/失敗例
- バリデーション基準
- 出力先: implementations/ ディレクトリ
```

---

## Phase 1: 最小ループを通す（2段階）

### Phase 1A: 固定仮説で Codex→実行→結果保存（adapter 検証）

**目標**: adapter 層が正しく動くことを検証

1. artifact ディレクトリ構造を作成
2. hypothesis.json と experiment.json を**手動で固定入力**
3. Codex: experiment.json → factor.py 生成（ImplementerAdapter 検証）
4. Bash: Qlib バックテスト実行 → run_result.json + logs
5. feedback.json を**手動で固定入力**
6. manifest.json + trace.json 更新
7. 再開テスト: artifact から状態復元できることを確認

### Phase 1B: Planner + Evaluator を自動化

**目標**: factor 1個、1ラウンド、完全自律で完走

1. Planner サブエージェント: TraceView → hypothesis.json + experiment.json
2. Codex: experiment.json → factor.py 生成
3. Bash: Qlib バックテスト実行
4. Evaluator サブエージェント: run_result.json → feedback.json
5. trace.json に記録

---

## リスクと対策（修正版）

| リスク | 対策 |
|---|---|
| 長期ループでの文脈汚染 | TraceView で圧縮。サブエージェントは毎回新規起動 |
| 評価者と実装者の癒着 | Evaluator は独立サブエージェント + 情報分離（実装文脈を渡さない） |
| 構造化出力の破綻 | JSON Schema 厳密定義 + validation.json で検証結果記録 |
| 再現性 | environment.json（git SHA, Qlib ver, dataset path）を毎 round 記録 |
| embedding 依存 | Phase 1 では RAG を省略。Phase 2 でローカル embedding 検討 |
| adapter/state 層の不整合 | Phase 1A で adapter 単体検証してから自律化 |
| import 崩壊 | oai/ 即削除せず compatibility shim で段階移行 |
| 再開機構の二重化 | artifact を SSOT に。既存再開機構は Phase 4 で廃止 |
| SOTA 選択のズレ | 既存 Trace の parent 選択ルールを artifact に忠実に再現 |
| 並列化の race | Phase 1 は並列禁止。直列実行のみ |
| workspace 境界の曖昧さ | Implementer の出力先を implementations/ に限定。template workspace は readonly |
| 失敗分類不足 | manifest.json に failure_type を6種類定義 |
| レイテンシ増大 | Qlib 実行自体が重いため、エージェントセッション追加分は相対的に小さいと想定。要計測 |
