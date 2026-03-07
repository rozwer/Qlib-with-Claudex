# Phase 1A: Adapter 検証（deterministic stub）

作成日: 2026-03-07
起点: OpenAI API 依存分析完了、Adapter 詳細設計完了
目的: Adapter 層が正しく動くことを検証。実 Qlib/Docker は使わない。
依存: なし（最初のフェーズ）

実装スコープ:
- 設計書の管理場所は親 repo（`docs/plans/`）
- 実コードの追加先は `RD-Agent-with-Claudex/`
- artifact 出力先は親 repo ルートの `.claude/artifacts/rdloop/<run_id>/`

---

## レビュー反映事項

- `based_experiments` は in-memory では `QlibFactorExperiment` 実体を持つ。artifact には参照文字列を書いてよいが、Adapter 返却時点では実体へ復元済みであること。
- factor proposal の既存実装に合わせ、Round 1 の `based_experiments` は空ではなく baseline 用の `QlibFactorExperiment(sub_tasks=[])` を先頭に持たせる。
- `NotConfiguredError` は現行コードベースに存在しないため、Phase 1A では新規例外を増やさず `RuntimeError` で fail-fast する。
- token count のモデル名はハードコードせず `LLM_SETTINGS.chat_model` を使う。Phase 1A の設定値は Claude 系モデルに寄せるが、shim 自体は設定追従にする。
- resume の比較対象は pickle session ではなく artifact SSOT。`LoopBase.dump/load()` との論理同値は Phase 1A の受け入れ条件から外す。
- round 番号は「ユーザー向け説明は 1-origin」「artifact ディレクトリは `round_0`, `round_1`, ... の 0-origin」で統一する。

---

## Phase 1A.1: 基盤実装

### Task 1A.1.1: Artifact ディレクトリ構造

#### ディレクトリレイアウト

```
.claude/artifacts/rdloop/<run_id>/
  ├── trace.json              # run-level: 全体の実験履歴（SSOT）
  ├── round_manifest.json     # run-level: 全 round のインデックス
  └── round_<N>/
      ├── manifest.json       # round メタ情報（status, failure_type, timestamps）
      ├── hypothesis.json     # HypothesisGen 出力
      ├── experiment.json     # H2E 出力（sub_tasks, workspace 定義）
      ├── implementations/    # Coder 出力
      │   └── factor_001.py
      ├── run_result.json     # Runner 出力（IC 等メトリクス）
      ├── feedback.json       # Summarizer 出力（decision, reason）
      ├── environment.json    # 再現性情報（git SHA, Qlib version, dataset path）
      ├── commands.json       # 実行 bash コマンド, exit code, 所要時間
      ├── stdout.log          # Runner 標準出力
      ├── stderr.log          # Runner 標準エラー
      └── validation.json     # schema 検証結果, parse error, fallback 使用有無
```

#### ヘルパー関数

| 関数 | 引数 | 戻り値 | 説明 |
|---|---|---|---|
| `create_run_dir(base, run_id)` | base: Path, run_id: str | Path | `<base>/<run_id>/` を作成。trace.json, round_manifest.json を空初期化 |
| `create_round_dir(run_dir, round_idx)` | run_dir: Path, round_idx: int | Path | `round_<N>/` と `implementations/` を作成。manifest.json を初期化 |
| `resolve_artifact(run_dir, round_idx, name)` | run_dir, round_idx, name: str | Path | `run_dir/round_<N>/<name>` を返す。存在チェック付き |
| `load_artifact(path)` | path: Path | dict | JSON 読み込み + schema_version 検証 |
| `save_artifact(path, data)` | path: Path, data: dict | None | JSON 書き込み + updated_at 自動付与 |

| Status |
|--------|
| cc:TODO |

---

### Task 1A.1.2: ClaudeCodeAPIBackend compatibility shim

#### 差し込み点

```python
# 変更前
LLM_SETTINGS.backend = "rdagent.oai.backend.LiteLLMAPIBackend"
# 変更後
LLM_SETTINGS.backend = "rdagent.oai.backend.claude_code.ClaudeCodeAPIBackend"
```

#### 4 抽象メソッドの実装

```python
class ClaudeCodeAPIBackend(APIBackend):

    def supports_response_schema(self) -> bool:
        return False  # base parser が後段で JSON parse

    def _calculate_token_from_messages(self, messages: list[dict]) -> int:
        return token_counter(model=LLM_SETTINGS.chat_model, messages=messages)

    def _create_embedding_inner_function(self, input_content_list: list[str]) -> list[list[float]]:
        raise RuntimeError(
            "Embedding backend not configured. "
            "Set embedding backend or disable knowledge (with_knowledge=False)."
        )

    def _create_chat_completion_inner_function(
        self, messages: list[dict], response_format=None, *args, **kwargs
    ) -> tuple[str, str | None]:
        # Claude Code transport に委譲。response_format は warning 出力して無視。
        # 戻り値: (content, "stop")
        ...
```

#### 三分割方針

| 機能 | 方式 | 理由 |
|---|---|---|
| chat completion | Claude Code transport 経由 | 本命の推論パス |
| token count | ローカル tokenizer（LiteLLM `token_counter`） | ネットワーク不要。prompt 短縮判定用 |
| embedding | fail-fast（`RuntimeError`） | Phase 1 は `with_knowledge=False` で回避 |

#### 実装メモ

- `APIBackend` はクラスではなく `rdagent.oai.llm_utils.APIBackend()` 経由で動的生成される alias。テストは `get_api_backend()` / alias 両方を確認する。
- `supports_response_schema()` が `False` でも `json_mode=True` は base parser により成立するため、shim では `response_format` を transport に渡さない。
- `LLM_SETTINGS.chat_model` の既定値は Phase 1A 実装時に Claude 系へ変更する。

| Status |
|--------|
| cc:TODO |

---

## Phase 1A.2: Adapter 実装

### Task 1A.2.1: ClaudeCodeFactorHypothesisGenAdapter

```python
class ClaudeCodeFactorHypothesisGenAdapter(HypothesisGen):
    def gen(self, trace: Trace, plan: ExperimentPlan | None = None) -> Hypothesis:
```

- **入力**: trace.json（過去履歴）
- **出力**: `round_<N>/hypothesis.json`
- **必須フィールド**: hypothesis, reason, concise_reason, concise_observation, concise_justification, concise_knowledge
- **Stub 実装**: 固定値 Hypothesis を返し、hypothesis.json に書き出す

| Status |
|--------|
| cc:TODO |

### Task 1A.2.2: ClaudeCodeFactorH2EAdapter

```python
class ClaudeCodeFactorH2EAdapter(Hypothesis2Experiment):
    def convert(self, hypothesis: Hypothesis, trace: Trace) -> QlibFactorExperiment:
```

- **入力**: hypothesis.json, trace.json
- **出力**: `round_<N>/experiment.json`
- **必須フィールド**: sub_tasks（各要素に factor_name, factor_description, factor_formulation, variables, version）、sub_workspace_list（`len == len(sub_tasks)`）、experiment_workspace（QlibFBWorkspace）、based_experiments（artifact 上は ref、返却オブジェクト上は `QlibFactorExperiment` 実体）
- **Stub 実装**: FactorTask 1件 + 空 workspace を生成。Round 1 は `QlibFactorExperiment(sub_tasks=[])` を baseline として入れ、Round 2 以降は trace.hist から `decision=True` の最新 experiment を末尾に入れる

| Status |
|--------|
| cc:TODO |

### Task 1A.2.3: ClaudeCodeFactorCoderAdapter

```python
class ClaudeCodeFactorCoderAdapter(Developer):
    def develop(self, exp: QlibFactorExperiment) -> QlibFactorExperiment:
```

- **入力**: experiment.json
- **出力**: `round_<N>/implementations/factor_*.py` + experiment.json 更新
- **必須契約**: `sub_workspace_list[i].target_task is sub_tasks[i]`、`sub_workspace_list[i].file_dict["factor.py"]` にコード格納、`prop_dev_feedback` を CoSTEERMultiFeedback 互換で設定
- **Stub 実装**: 固定 factor.py コードを file_dict に注入。in-place 更新して exp を返す

| Status |
|--------|
| cc:TODO |

### Task 1A.2.4: ClaudeCodeFactorSummarizerAdapter

```python
class ClaudeCodeFactorSummarizerAdapter(Experiment2Feedback):
    def generate_feedback(
        self, exp: Experiment, trace: Trace, exception: Exception | None = None
    ) -> HypothesisFeedback:
```

- **入力**: run_result.json, experiment.json, trace.json
- **出力**: `round_<N>/feedback.json`
- **必須フィールド**: reason, decision（bool: SOTA 更新するか）, code_change_summary
- **推奨フィールド**: observations, hypothesis_evaluation, new_hypothesis, acceptable
- **Stub 実装**: Round 番号に応じて decision を切り替え（Round 1: True, Round 2: False）

| Status |
|--------|
| cc:TODO |

---

## Phase 1A.3: テスト

### Task 1A.3.1: 2-round 検証シナリオ

#### Round 1

| Step | Adapter | 出力 | 検証内容 |
|---|---|---|---|
| 1 | StubHypothesisGen | Hypothesis 1件 | 6必須フィールド全て非空 |
| 2 | StubH2E | QlibFactorExperiment | sub_tasks=1件, based_experiments[0] が baseline (`QlibFactorExperiment(sub_tasks=[])`) |
| 3 | StubCoder | file_dict={"factor.py": "..."} | CoSTEERMultiFeedback([accepted]) |
| 4 | StubRunner | result={"IC": 0.12, ...} | stdout="round1 ok" |
| 5 | StubSummarizer | decision=True | SOTA 更新 → trace.hist に追記 |

#### Round 2

| Step | 検証内容 |
|---|---|
| 1 | trace 履歴に Round 1 が含まれること |
| 2 | based_experiments の末尾に Round 1 の experiment 実体が入ること |
| 3 | decision=True の Round 1 が SOTA として参照されること |
| 5 | decision=False → SOTA は Round 1 のまま維持 |

**最終検証**: trace.json の hist 長=2、dag_parent 整合、全 artifact ファイル存在確認

| Status |
|--------|
| cc:TODO |

### Task 1A.3.2: Resume テスト（4 checkpoint）

| # | 地点 | 存在する artifact | 再開スロット |
|---|---|---|---|
| 1 | exp_gen 完了後 | hypothesis.json, experiment.json | coding から再開 |
| 2 | coding 完了後 | + implementations/ | running から再開 |
| 3 | running 完了後 | + run_result.json | feedback から再開 |
| 4 | feedback 完了後 | + feedback.json | 次 round から再開 |

#### 各地点の検証手順

1. 当該地点まで実行し、プロセスを停止
2. manifest.json の `step_idx` を確認
3. artifact + trace.json から状態復元して再開
4. 最終状態を fresh 2-round run と比較

#### 比較項目（resume 正当性）

| # | 項目 | 判定方法 |
|---|---|---|
| 1 | `trace.hist` の長さと順序 | fresh と一致 |
| 2 | `trace.dag_parent` | fresh と一致 |
| 3 | round ごとの `step_idx` | fresh と一致 |
| 4 | 最終 experiment/result/feedback | 内容が論理同値 |
| 5 | checkpoint 前の step 非再実行 | adapter call counter が増えていないこと |

| Status |
|--------|
| cc:TODO |

### Task 1A.3.3: Compatibility shim テスト

| # | テスト項目 | 期待結果 |
|---|---|---|
| 1 | `LLM_SETTINGS.backend` で import | ClaudeCodeAPIBackend instance 取得 |
| 2 | `rdagent.oai.llm_utils.APIBackend()` が shim instance を返す | isinstance チェック通過 |
| 3 | `build_messages_and_create_chat_completion()` | text（str）を返す |
| 4 | `json_mode=True` 指定 | base parser が JSON parse 成功 |
| 5 | `build_messages_and_calculate_token()` | int を返す（> 0） |
| 6 | `create_embedding()` 未設定時 | `RuntimeError` で fail-fast |

#### Negative テスト

- embedding backend 未設定で `_create_embedding_inner_function()` 呼び出し
- 期待: `RuntimeError("Embedding backend not configured. Set embedding backend or disable knowledge (with_knowledge=False).")`

| Status |
|--------|
| cc:TODO |

---

## 受け入れ条件

| # | 基準 | 検証方法 |
|---|---|---|
| a | fresh 2-round 実行で artifact 群が一式生成される | round_0/, round_1/ 以下の全ファイル存在確認 |
| b | 4 checkpoint 全てから resume 成功 | 各地点で再開し完走 |
| c | fresh と resumed の最終 trace.json / manifest.json が論理同値 | JSON diff で比較 |
| d | shim 経由で token 長判定と embedding fail-fast が意図通り動作 | 6項目テスト全通過 |

---

## 実装対象ファイル

### 新規作成

| ファイル | 内容 |
|---|---|
| `RD-Agent-with-Claudex/rdagent/oai/backend/claude_code.py` | ClaudeCodeAPIBackend（compatibility shim） |
| `RD-Agent-with-Claudex/rdagent/adapters/factor/__init__.py` | パッケージ初期化 |
| `RD-Agent-with-Claudex/rdagent/adapters/factor/hypothesis_gen.py` | ClaudeCodeFactorHypothesisGenAdapter |
| `RD-Agent-with-Claudex/rdagent/adapters/factor/h2e.py` | ClaudeCodeFactorH2EAdapter |
| `RD-Agent-with-Claudex/rdagent/adapters/factor/coder.py` | ClaudeCodeFactorCoderAdapter |
| `RD-Agent-with-Claudex/rdagent/adapters/factor/summarizer.py` | ClaudeCodeFactorSummarizerAdapter |
| `RD-Agent-with-Claudex/rdagent/adapters/artifact_utils.py` | ヘルパー関数（create_run_dir 等） |
| `RD-Agent-with-Claudex/test/adapters/test_artifact.py` | Artifact ディレクトリ構造テスト |
| `RD-Agent-with-Claudex/test/adapters/test_shim.py` | Compatibility shim テスト（6項目 + negative） |
| `RD-Agent-with-Claudex/test/adapters/test_adapters.py` | 2-round 検証シナリオ |
| `RD-Agent-with-Claudex/test/adapters/test_resume.py` | Resume テスト（4 checkpoint） |

### 変更

| ファイル | 変更内容 |
|---|---|
| `RD-Agent-with-Claudex/rdagent/oai/llm_conf.py` | `LLM_SETTINGS.backend` デフォルト値の切り替えオプション追加 |
