# OpenAI API 依存箇所レポート

## 概要

| リポジトリ | OpenAI依存度 | 状況 |
|---|---|---|
| **Qlib-with-Claudex** | ほぼなし | `finco`モジュールは過去に存在したが現HEAD未収録。RD-Agentに移行済み |
| **RD-Agent-with-Claudex** | 非常に重い | 100+箇所。3層のLLM抽象レイヤーが存在 |

---

## Qlib-with-Claudex

### 現状: OpenAI依存なし

- 現在のHEADにはOpenAI関連コードが存在しない
- 過去の`qlib/finco/`モジュール（`llm.py`, `conf.py`, `cli.py`）はgit履歴にのみ存在
- `pyproject.toml`, `setup.py`にもOpenAI関連パッケージなし
- Azure Blob Storage連携（MLflow用）はあるが、OpenAI APIとは無関係

### 改造方針
- **CLAUDE.md / スキル / フック整備のみ** で対応可能
- コード変更は不要

---

## RD-Agent-with-Claudex

### 依存の3層構造

```
Layer 1: LiteLLM (現デフォルト)
  └── rdagent/oai/backend/litellm.py
  └── LiteLLMAPIBackend クラス

Layer 2: Pydantic-AI (新規・一部コンポーネント)
  └── rdagent/oai/backend/pydantic_ai.py
  └── pydantic_ai.models.openai.OpenAIChatModel

Layer 3: 直接OpenAI SDK (deprecated)
  └── rdagent/oai/backend/deprec.py
  └── openai.ChatCompletion, openai.AzureOpenAI
```

### コアファイル一覧

| ファイル | 依存内容 | 改造難度 |
|---|---|---|
| `rdagent/oai/llm_conf.py` | デフォルトモデル名(`gpt-4-turbo`), API Key設定 | 低 |
| `rdagent/oai/backend/litellm.py` | LiteLLM経由のchat/embedding呼び出し | 低（LiteLLMはClaude対応済み） |
| `rdagent/oai/backend/deprec.py` | 直接OpenAI SDK呼び出し、Azure対応 | 中（削除 or Claude SDK置換） |
| `rdagent/oai/backend/pydantic_ai.py` | Pydantic-AI + OpenAIChatModel | 中（AnthropicModel に差替） |
| `rdagent/oai/backend/base.py` | 基底クラス、エラーハンドリング | 低 |
| `rdagent/oai/backend/__init__.py` | バックエンド選択 | 低 |
| `rdagent/components/agent/base.py` | Pydantic-AI Agent初期化 | 低 |

### 設定・環境変数

| 変数 | 用途 | 対応 |
|---|---|---|
| `OPENAI_API_KEY` | API認証 | `ANTHROPIC_API_KEY` に置換 |
| `USE_AZURE` | Azure OpenAI切替 | 削除 |
| `AZURE_API_BASE` | Azure エンドポイント | 削除 |
| `MODEL` | モデル名 | `claude-sonnet-4-20250514` 等に |

### パッケージ依存 (requirements.txt)

| パッケージ | 行 | 対応 |
|---|---|---|
| `openai` | L10 | 削除 or 残す（LiteLLM内部依存） |
| `litellm>=1.73` | L11 | 残す（Claude対応済み） |
| `langchain` | L22 | 要検討 |
| `langchain-community` | L23 | 要検討 |
| `pydantic-ai-slim[mcp,openai,prefect]` | L75 | `[mcp,anthropic,prefect]` に変更 |

### モデル参照箇所

| ファイル | 現在値 | 置換先 |
|---|---|---|
| `rdagent/oai/llm_conf.py:15` | `gpt-4-turbo` | `claude-sonnet-4-20250514` |
| `rdagent/oai/llm_conf.py:16` | `text-embedding-3-small` | Voyage等に要検討 |
| `rdagent/scenarios/finetune/scen/utils.py:18` | `gpt-3.5-turbo`(tokenizer) | `tiktoken`互換の対応要 |
| `rdagent/scenarios/finetune/benchmark/benchmark.py:10` | `gpt-4` | `claude-sonnet-4-20250514` |

### トークナイゼーション

- `tiktoken`（OpenAI専用）を使用 → Anthropicの`anthropic-tokenizer`等に要置換
- `deprec.py`の`_get_encoder()`メソッドが該当

### Docker/CI

- `kaggle_environment.yaml`: `openai==1.48.0` をピン留め → 削除 or 更新
- Dockerfile: OpenAI `mle-bench`リポをクローン → 要検討

---

## 改造の優先順位（推奨）

### Phase 1: 最小限で動く状態
1. `llm_conf.py` のデフォルトモデルをClaude系に変更
2. LiteLLMバックエンドはそのまま活用（既にClaude対応）
3. 環境変数を`ANTHROPIC_API_KEY`に対応

### Phase 2: Claude Code統合
4. `deprec.py` を削除 or Claude SDKバックエンドに置換
5. `pydantic_ai.py` を AnthropicModel に差替
6. CLAUDE.md / スキル / フック整備
7. サブエージェント / Codex 連携のワークフロー設計

### Phase 3: 完全移行
8. tiktoken → Anthropicトークナイザ
9. embeddingをVoyage等に移行
10. LangChain依存の整理
11. Docker/CI環境の更新
12. ドキュメント整備・公開準備
