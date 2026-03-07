# Plans — Qlib-with-Claudex Migration

この計画は親 repo 配下の 2 subrepo をまたいで進める。
- `RD-Agent-with-Claudex/`: Phase 1A-4 の主実装対象
- `Qlib-with-Claudex/`: 主に Phase 3 の公開準備対象
- `docs/plans/`: 親 repo 側の設計・進捗管理

## Phase 1A: Adapter 検証（deterministic stub）

> 目標: Adapter 層が正しく動くことを検証。実 Qlib/Docker は使わない。

- [x] Artifact ディレクトリ構造の実装（`.claude/artifacts/rdloop/<run_id>/round_<N>/`）
- [x] ClaudeCodeAPIBackend compatibility shim 実装（chat/token/embedding 三分割）
- [x] ClaudeCodeFactorHypothesisGenAdapter 実装
- [x] ClaudeCodeFactorH2EAdapter 実装
- [x] ClaudeCodeFactorCoderAdapter 実装
- [x] ClaudeCodeFactorSummarizerAdapter 実装
- [x] Stub ベースの 2-round 検証テスト
- [x] Resume テスト（4 checkpoint 地点から再開）
- [x] Compatibility shim テスト（import / chat / token / embedding fail-fast）

## Phase 1B: Planner + Evaluator 自動化

> 目標: factor 1個、1ラウンド、完全自律で完走。

- [x] Planner サブエージェント実装（TraceView → hypothesis.json + experiment.json）
- [x] Evaluator サブエージェント実装（run_result.json → feedback.json）
- [x] qlib-rd-loop スキル実装（全体ループ制御）
- [x] qlib-factor-implement スキル実装（Codex 用ガイドライン）
- [ ] End-to-end 1ラウンド完走テスト（実 Qlib 環境依存 — Phase 3 で実施）

## Phase 2: Claude 系ランタイムへの中核移行

- [x] llm_conf.py 設定更新（chat_model→Claude, token_limit→200k, API key→Anthropic, legacy 設定削除）
- [x] deprec.py 削除（491行の deprecated OpenAI/Azure/Llama2/GCR バックエンド）
- [x] pydantic_ai.py の LiteLLM bridge を Claude モデル対応に整理（PROVIDER_TO_ENV_MAP に anthropic 追加）
- [x] tiktoken → LiteLLM token counter（finetune/scen/utils.py）
- [x] embedding を Voyage voyage-3 に移行（llm_conf.py + embedding.py + finetune conf）
- [x] LangChain 依存整理（pypdf 直接使用、langchain/langchain-community 削除）

## Phase 3: 完全移行・公開準備

- [x] Docker 環境更新（kaggle_environment.yaml: openai→anthropic, tiktoken/langchain 削除済み）
- [x] RD-Agent-with-Claudex CLAUDE.md 作成（アーキテクチャ、Adapter 層、Artifact 構造）
- [x] ドキュメント更新（README に Anthropic 設定例追加、installation_and_configuration.rst 更新）
- [x] 公開準備（LICENSE MIT 確認済、.gitignore に .claude/ .env 除外済み）
- [x] Qlib-with-Claudex CLAUDE.md 作成（データセットアップ、バックテスト手順）
- [x] CI/CD パイプライン整備（adapter-tests + lint-openai-allowlist ジョブ追加）
- [x] 新規スキル作成（qlib-hypothesis-gen, qlib-experiment-eval, qlib-artifact-inspect）

## Phase 4: レガシー削除

- [x] deprec.py 削除済み（Phase 2.1 で実施）
- [x] __init__.py から DeprecBackend import 削除済み
- [x] llm_conf.py から Azure/Llama2/GCR/DeepSeek 設定削除済み（134→72行）
- [x] base.py の OpenAI 固有例外を litellm 汎用例外に置換（`openai.APITimeoutError` → `litellm.Timeout`）
- [x] `import openai` / `import tiktoken` が rdagent/ 内でゼロ件
- [x] 既存セッション保存再開機構の廃止（`use_pickle_session` フラグで制御可能に。Claudex adapter は `False` で artifact SSOT に一本化）
- [x] requirements.txt から openai/litellm/pydantic-ai を削除（`requirements/llm.txt` に optional extra として隔離。`pip install rdagent[llm]` で復元可能）
- [x] pydantic-ai の OpenAI extra を optional 化（llm extra に移動。全 import を try/except ガード済み）

---

## Phase Files

- [phase-1A.md](docs/plans/phase-1A.md)
- [phase-1B.md](docs/plans/phase-1B.md)
- [phase-2.md](docs/plans/phase-2.md)
- [phase-3.md](docs/plans/phase-3.md)
- [phase-4.md](docs/plans/phase-4.md)
