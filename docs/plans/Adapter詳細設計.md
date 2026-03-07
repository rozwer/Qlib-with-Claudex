# Adapter 詳細設計（factor シナリオ限定）

quant は Phase 2 以降。本書は factor のみ。

---

## 1. Adapter 対応表

### RDLoop スロット一覧

| スロット | 既存クラス | 継承元 | adapter クラス名 |
|---|---|---|---|
| hypothesis_gen | QlibFactorHypothesisGen | FactorHypothesisGen → LLMHypothesisGen → HypothesisGen | ClaudeCodeFactorHypothesisGenAdapter |
| hypothesis2experiment | QlibFactorHypothesis2Experiment | FactorHypothesis2Experiment → LLMHypothesis2Experiment → Hypothesis2Experiment | ClaudeCodeFactorH2EAdapter |
| coder | QlibFactorCoSTEER (= FactorCoSTEER) | FactorCoSTEER → CoSTEER → Developer | ClaudeCodeFactorCoderAdapter |
| runner | QlibFactorRunner | CachedRunner → Developer | **Phase 1 は既存クラスをそのまま使用** |
| summarizer | QlibFactorExperiment2Feedback | Experiment2Feedback | ClaudeCodeFactorSummarizerAdapter |

### 各 Adapter の最小契約

#### ClaudeCodeFactorHypothesisGenAdapter

```python
class ClaudeCodeFactorHypothesisGenAdapter(HypothesisGen):
    def gen(self, trace: Trace, plan: ExperimentPlan | None = None) -> Hypothesis:
        """
        Claude Code に仮説生成を依頼し、hypothesis.json を生成。
        返す Hypothesis には以下が全て必須:
          - hypothesis: str
          - reason: str
          - concise_reason: str
          - concise_observation: str
          - concise_justification: str
          - concise_knowledge: str
        """
```

#### ClaudeCodeFactorH2EAdapter

```python
class ClaudeCodeFactorH2EAdapter(Hypothesis2Experiment):
    def convert(self, hypothesis: Hypothesis, trace: Trace) -> QlibFactorExperiment:
        """
        仮説を factor task 群に分解し、experiment.json を生成。
        返す QlibFactorExperiment の最小契約:
          - sub_tasks: list[FactorTask] を埋める
          - sub_workspace_list: len(sub_tasks) に揃えて初期化
          - experiment_workspace: QlibFBWorkspace(template_folder_path=...) を用意
          - based_experiments: 前回成功の QlibFactorExperiment 実体を設定
        """
```

#### ClaudeCodeFactorCoderAdapter

```python
class ClaudeCodeFactorCoderAdapter(Developer):
    def develop(self, exp: QlibFactorExperiment) -> QlibFactorExperiment:
        """
        各 FactorTask のコードを Codex で生成し、workspace に注入。
        最小契約:
          - sub_workspace_list[i].target_task is sub_tasks[i]
          - sub_workspace_list[i].file_dict["factor.py"] にコードを格納
          - prop_dev_feedback を CoSTEERMultiFeedback 互換で埋める
          - in-place 更新して exp を返す
        """
```

#### ClaudeCodeFactorSummarizerAdapter

```python
class ClaudeCodeFactorSummarizerAdapter(Experiment2Feedback):
    def generate_feedback(
        self, exp: Experiment, trace: Trace, exception: Exception | None = None
    ) -> HypothesisFeedback:
        """
        Claude Code に結果分析を依頼し、feedback.json を生成。
        必須フィールド:
          - reason: str
          - decision: bool（SOTA 更新するか）
          - code_change_summary: str
        推奨フィールド:
          - observations: str
          - hypothesis_evaluation: str
          - new_hypothesis: str
          - acceptable: bool
        """
```

---

## 2. Artifact Schema 必須フィールド

### hypothesis.json

| フィールド | 型 | 対応元 | 必須 |
|---|---|---|---|
| schema_version | int | - | o |
| artifact_type | str | - | o |
| artifact_id | str | - | o |
| class_path | str | - | o |
| hypothesis | str | Hypothesis.hypothesis | o |
| reason | str | Hypothesis.reason | o |
| concise_reason | str | Hypothesis.concise_reason | o |
| concise_observation | str | Hypothesis.concise_observation | o |
| concise_justification | str | Hypothesis.concise_justification | o |
| concise_knowledge | str | Hypothesis.concise_knowledge | o |

### experiment.json

| フィールド | 型 | 対応元 | 必須 |
|---|---|---|---|
| schema_version | int | - | o |
| artifact_type | str | - | o |
| artifact_id | str | - | o |
| class_path | str | QlibFactorExperiment | o |
| hypothesis_ref | str\|null | - | o |
| based_experiments | list[str] | Experiment.based_experiments（artifact ref） | o |
| sub_tasks | list[task_obj] | Experiment.sub_tasks | o |
| sub_workspace_list | list[workspace_obj\|null] | Experiment.sub_workspace_list | o |
| experiment_workspace | workspace_obj | QlibFactorExperiment.experiment_workspace | o |
| prop_dev_feedback | costeer_feedback_obj\|null | Experiment.prop_dev_feedback | - |
| local_selection | list[int]\|null | Experiment.local_selection | - |

#### sub_tasks 各要素

| フィールド | 型 | 対応元 |
|---|---|---|
| class_path | str | FactorTask |
| factor_name | str | FactorTask.factor_name |
| factor_description | str | Task.description |
| factor_formulation | str | FactorTask.factor_formulation |
| variables | dict | FactorTask.variables |
| version | int | AbsTask.version |
| base_code | str\|null | CoSTEERTask.base_code |
| factor_resources | str\|null | FactorTask.factor_resources |
| factor_implementation | bool | FactorTask.factor_implementation |

#### sub_workspace_list 各要素

制約: `len(sub_workspace_list) == len(sub_tasks)`

| フィールド | 型 | 対応元 |
|---|---|---|
| class_path | str | FactorFBWorkspace |
| task_index | int | → sub_tasks[task_index] に再リンク |
| workspace_path | str | FBWorkspace.workspace_path |
| file_dict | dict[str, str] | FBWorkspace.file_dict |
| change_summary | str\|null | FBWorkspace.change_summary |
| raise_exception | bool | FactorFBWorkspace.raise_exception |

#### experiment_workspace

| フィールド | 型 | 対応元 |
|---|---|---|
| class_path | str | QlibFBWorkspace |
| workspace_path | str | workspace_path |
| file_dict | dict[str, str] | file_dict |
| init_kwargs | dict | template_folder_path 等 |

### run_result.json

| フィールド | 型 | 対応元 | 必須 |
|---|---|---|---|
| schema_version | int | - | o |
| artifact_type | str | - | o |
| artifact_id | str | - | o |
| experiment_ref | str | - | o |
| status | str | "success"\|"failed"\|"timeout" | o |
| result | dict[str, float]\|null | Experiment.running_info.result（pd.Series → dict） | o |
| stdout | str | QlibFactorExperiment.stdout | o |
| running_time_seconds | float\|null | Experiment.running_info.running_time | - |
| sub_results | dict[str, float] | Experiment.sub_results | - |

### feedback.json

| フィールド | 型 | 対応元 | 必須 |
|---|---|---|---|
| schema_version | int | - | o |
| artifact_type | str | - | o |
| artifact_id | str | - | o |
| class_path | str | HypothesisFeedback | o |
| reason | str | HypothesisFeedback.reason | o |
| decision | bool | HypothesisFeedback.decision | o |
| code_change_summary | str | HypothesisFeedback.code_change_summary | o |
| observations | str\|null | HypothesisFeedback.observations | - |
| hypothesis_evaluation | str\|null | HypothesisFeedback.hypothesis_evaluation | - |
| new_hypothesis | str\|null | HypothesisFeedback.new_hypothesis | - |
| acceptable | bool\|null | HypothesisFeedback.acceptable | - |
| exception | {type, message}\|null | exception 引数 | - |

### trace.json（run-level に1つ）

| フィールド | 型 | 対応元 | 必須 |
|---|---|---|---|
| schema_version | int | - | o |
| artifact_type | str | - | o |
| artifact_id | str | - | o |
| class_path | str | Trace | o |
| scen_class_path | str | Trace.scen | o |
| knowledge_base_class_path | str\|null | Trace.knowledge_base | - |
| hist | list[{experiment_ref, feedback_ref}] | Trace.hist | o |
| dag_parent | list[list[int]] | Trace.dag_parent | o |
| idx2loop_id | dict[str, int] | Trace.idx2loop_id | o |
| current_selection | list[int] | Trace.current_selection | o |

### manifest.json（各 round / run-level）

| フィールド | 型 | 対応元 | 必須 |
|---|---|---|---|
| schema_version | int | - | o |
| session_id | str | - | o |
| rdloop_class_path | str | FactorRDLoop | o |
| prop_setting | dict | FactorBasePropSetting | o |
| loop_idx | int | LoopBase.loop_idx | o |
| step_idx | dict[str, int] | LoopBase.step_idx | o |
| latest_checkpoint | {loop_id, step_idx, step_name} | - | o |
| trace_ref | str | → trace.json | o |
| created_at | str | ISO 8601 | o |
| updated_at | str | ISO 8601 | o |

---

## 3. Compatibility Shim

### 差し込み点

`LLM_SETTINGS.backend` の値を変更:
```
現在: "rdagent.oai.backend.LiteLLMAPIBackend"
Phase 1: "rdagent.oai.backend.claude_code.ClaudeCodeAPIBackend"
```

### 最小 interface（APIBackend の4抽象メソッド）

```python
class ClaudeCodeAPIBackend(APIBackend):

    def supports_response_schema(self) -> bool:
        """Phase 1: False 固定。base parser が後段で JSON parse する"""
        return False

    def _calculate_token_from_messages(self, messages: list[dict[str, Any]]) -> int:
        """Phase 1: LiteLLM の tokenizer にローカル委譲（ネットワーク不要）"""
        return token_counter(model="claude-sonnet-4-20250514", messages=messages)

    def _create_embedding_inner_function(self, input_content_list: list[str]) -> list[list[float]]:
        """Phase 1: fail-fast。
        embedding backend 未設定時は明示エラー:
        'embedding backend を設定するか knowledge を無効化せよ'
        embedding 設定済みなら LiteLLM に委譲"""
        raise NotConfiguredError(
            "Embedding backend not configured. "
            "Set embedding backend or disable knowledge (with_knowledge=False)."
        )

    def _create_chat_completion_inner_function(
        self,
        messages: list[dict[str, Any]],
        response_format: Optional[Union[dict, Type[BaseModel]]] = None,
        *args, **kwargs,
    ) -> tuple[str, str | None]:
        """Phase 1: Claude Code transport に messages を渡し、テキスト本文を返す。
        response_format は無視（warning 出力）。
        戻り値: (content, "stop")
        fail-fast: 非テキスト応答、空本文"""
```

### Phase 1 の三分割方針

| 機能 | 方式 | 理由 |
|---|---|---|
| chat completion | ClaudeCodeAPIBackend | 本命。Claude Code transport 経由 |
| token count | ローカル tokenizer | factor coder が prompt 短縮判定に使う。ネットワーク不要 |
| embedding | fail-fast or LiteLLM委譲 | Phase 1 は with_knowledge=False で回避推奨 |

---

## 4. Phase 1A 改訂テスト項目

### 前提

- 実 Qlib/Docker ではなく **deterministic stub** で組む
- orchestration / artifact / resume の検証に集中

### 2 round 検証シナリオ

#### Round 1

1. StubHypothesisGen → Hypothesis 1件
2. StubH2E → QlibFactorExperiment(sub_tasks=[FactorTask(...)], based_experiments=[baseline_exp])
3. StubCoder → FactorFBWorkspace(file_dict={"factor.py": "..."}) + CoSTEERMultiFeedback([accepted])
4. StubRunner → result={"IC": 0.12, ...}, stdout="round1 ok"
5. StubSummarizer → decision=True（SOTA 更新）

#### Round 2

1. Adapter が trace 履歴（Round 1）を読めることを確認
2. based_experiments に Round 1 の experiment が入ることを確認
3. decision=True の Round 1 が SOTA として参照されることを確認
4. StubSummarizer → decision=False（SOTA 維持）

### Resume テスト（4地点）

| 地点 | 状態 | 検証内容 |
|---|---|---|
| exp_gen 完了後 | hypothesis.json + experiment.json 存在 | coding から再開できる |
| coding 完了後 | implementations/ 存在 | running から再開できる |
| running 完了後 | run_result.json 存在 | feedback から再開できる |
| feedback 完了後 | feedback.json 存在 | 次 round から再開できる |

各地点で:
- プロセスを落とす
- manifest.json + trace.json + 各 artifact から再開
- 最終状態が fresh 2-round run と論理一致

### 比較項目（resume 正当性）

1. `trace.hist` の長さと順序
2. `trace.dag_parent`
3. round ごとの `step_idx`
4. 最終 experiment/result/feedback の内容
5. checkpoint 前の step が再実行されていない（adapter call counter で検証）

### Compatibility Shim 検証

1. `LLM_SETTINGS.backend` で import 成功
2. `APIBackend()` が shim instance を返す
3. `build_messages_and_create_chat_completion()` が text を返す
4. `json_mode=True` で base parser が通る
5. `build_messages_and_calculate_token()` が int を返す
6. `create_embedding()` 未設定時に明示エラーで fail-fast

### Negative テスト

- embedding backend 未設定時に `_create_embedding_inner_function()` が明示エラー:
  「embedding backend を設定するか knowledge を無効化せよ」

### 成功判定基準

| # | 基準 |
|---|---|
| a | fresh 2-round 実行で artifact 群が一式生成される |
| b | 4 checkpoint 全てから resume 成功 |
| c | fresh と resumed の最終 trace.json / manifest.json が論理同値 |
| d | shim 経由で token 長判定と embedding 呼び出しが意図通り動作 |
