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

- [ ] Planner サブエージェント実装（TraceView → hypothesis.json + experiment.json）
- [ ] Evaluator サブエージェント実装（run_result.json → feedback.json）
- [ ] qlib-rd-loop スキル実装（全体ループ制御）
- [ ] qlib-factor-implement スキル実装（Codex 用ガイドライン）
- [ ] End-to-end 1ラウンド完走テスト

## Phase 2: Claude 系ランタイムへの中核移行

- [ ] deprec.py 削除 or Claude SDK バックエンド置換
- [ ] pydantic_ai.py の LiteLLM bridge を Claude モデル対応に整理
- [ ] tiktoken → LiteLLM token counter
- [ ] embedding を Voyage 等に移行
- [ ] LangChain 依存整理

## Phase 3: 完全移行・公開準備

- [ ] Docker/CI 環境更新（kaggle_environment.yaml 等）
- [ ] Qlib-with-Claudex 側の CLAUDE.md / スキル / フック整備
- [ ] ドキュメント整備
- [ ] 公開準備（README, LICENSE 確認, CI/CD）

## Phase 4: レガシー削除

- [ ] 既存セッション保存再開機構の廃止（artifact SSOT に一本化）
- [ ] rdagent/oai/ の OpenAI 専用コード完全削除
- [ ] requirements.txt から openai, tiktoken を削除
- [ ] pydantic-ai の OpenAI extra を不要化できれば削除、残すなら optional bridge として隔離

---

## Phase Files

- [phase-1A.md](docs/plans/phase-1A.md)
- [phase-1B.md](docs/plans/phase-1B.md)
- [phase-2.md](docs/plans/phase-2.md)
- [phase-3.md](docs/plans/phase-3.md)
- [phase-4.md](docs/plans/phase-4.md)
