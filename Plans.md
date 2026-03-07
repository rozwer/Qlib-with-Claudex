# Plans — Qlib-with-Claudex Migration

## Phase 1A: Adapter 検証（deterministic stub）

> 目標: Adapter 層が正しく動くことを検証。実 Qlib/Docker は使わない。

- [ ] Artifact ディレクトリ構造の実装（`.claude/artifacts/rdloop/<run_id>/round_<N>/`）
- [ ] ClaudeCodeAPIBackend compatibility shim 実装（chat/token/embedding 三分割）
- [ ] ClaudeCodeFactorHypothesisGenAdapter 実装
- [ ] ClaudeCodeFactorH2EAdapter 実装
- [ ] ClaudeCodeFactorCoderAdapter 実装
- [ ] ClaudeCodeFactorSummarizerAdapter 実装
- [ ] Stub ベースの 2-round 検証テスト
- [ ] Resume テスト（4 checkpoint 地点から再開）
- [ ] Compatibility shim テスト（import / chat / token / embedding fail-fast）

## Phase 1B: Planner + Evaluator 自動化

> 目標: factor 1個、1ラウンド、完全自律で完走。

- [ ] Planner サブエージェント実装（TraceView → hypothesis.json + experiment.json）
- [ ] Evaluator サブエージェント実装（run_result.json → feedback.json）
- [ ] qlib-rd-loop スキル実装（全体ループ制御）
- [ ] qlib-factor-implement スキル実装（Codex 用ガイドライン）
- [ ] End-to-end 1ラウンド完走テスト

## Phase 2: Claude Code 統合深化

- [ ] deprec.py 削除 or Claude SDK バックエンド置換
- [ ] pydantic_ai.py を AnthropicModel に差替
- [ ] tiktoken → Anthropic トークナイザ
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
- [ ] requirements.txt から openai, pydantic-ai-slim[openai] 削除
