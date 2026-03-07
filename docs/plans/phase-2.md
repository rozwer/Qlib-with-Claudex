# Phase 2: Claude 系ランタイムへの中核移行

作成日: 2026-03-07
起点: Phase 1B の自動ループ完走（LiteLLM 経由で Claude が動作する状態）
目的: 主要な実行経路を Claude 系ランタイムに寄せ、OpenAI 前提の設定・SDK・tokenizer 依存を段階的に縮小する。完全な dead code 削除と最終監査は Phase 4 で実施する。
依存: Phase 1B 完了

実装スコープ:
- 主対象は `RD-Agent-with-Claudex/`
- `Qlib-with-Claudex/` はこのフェーズでは原則ノータッチ
- 親 repo の `docs/plans/` は進捗に合わせて随時更新

---

## レビュー反映事項

- `rdagent/oai/backend/base.py` は現時点で `openai` 例外型に依存しているため、Phase 2 の時点では「OpenAI 依存の完全排除」ではなく「主要経路の移行」と定義する。
- `pydantic_ai.py` は現状 `OpenAIChatModel` + `LiteLLMProvider` 構成で動いている。`AnthropicModel` に `LiteLLMProvider` をそのまま渡せる前提は置かず、まずは LiteLLM bridge を壊さず Claude モデルへ寄せる案を標準とする。
- LangChain 置換時は `PyPDFLoader` だけでなく Azure Document Intelligence 用のページ数取得コードも `pypdf.PdfReader` に寄せる。
- `OPENAI_API_KEY` 非依存で主要経路が動くことは Phase 2 の目標に含めるが、`openai` パッケージや `pydantic-ai-slim[openai]` extra の最終削除は Phase 4 の受け入れ条件に集約する。

---

## Phase 2.1: deprec.py 削除

`rdagent/oai/backend/deprec.py`（491行）は直接 `openai.AzureOpenAI` / `openai.OpenAI` を呼び出す deprecated バックエンド。
Llama2 / GCR / Azure DeepSeek / Azure OpenAI / 直 OpenAI の5分岐を1クラスに詰め込んでおり保守困難。
デフォルトバックエンドは `LiteLLMAPIBackend`（`llm_conf.py:13`）であり、LiteLLM + ClaudeCodeAPIBackend が全ユースケースをカバーするため**削除**する。
インポート元: `rdagent/oai/backend/__init__.py:1`。

削除対象の環境変数: `USE_AZURE`, `CHAT_USE_AZURE`, `EMBEDDING_USE_AZURE`, `CHAT_AZURE_API_BASE`, `CHAT_AZURE_API_VERSION`, `EMBEDDING_AZURE_*`, `*_TOKEN_PROVIDER`, `MANAGED_IDENTITY_CLIENT_ID`, Llama2/GCR/DeepSeek 関連（計20+設定）。

`llm_conf.py` から削除する設定フィールド（約80行分）:

```
use_azure, chat_use_azure, embedding_use_azure,
chat_use_azure_token_provider, embedding_use_azure_token_provider,
managed_identity_client_id,
chat_azure_api_base, chat_azure_api_version,
embedding_azure_api_base, embedding_azure_api_version,
use_llama2, llama2_ckpt_dir, llama2_tokenizer_path, llams2_max_batch_size,
use_gcr_endpoint, gcr_endpoint_type,
llama2_70b_*, llama3_70b_*, phi2_*, phi3_4k_*, phi3_128k_*,
gcr_endpoint_temperature, gcr_endpoint_top_p, gcr_endpoint_do_sample, gcr_endpoint_max_token,
chat_use_azure_deepseek, chat_azure_deepseek_endpoint, chat_azure_deepseek_key
```

### タスク

| ID | 内容 | Status |
|---|---|---|
| 2.1.1 | `deprec.py` を削除 | TODO |
| 2.1.2 | `__init__.py` から `DeprecBackend` の import を削除 | TODO |
| 2.1.3 | `llm_conf.py` から Azure / Llama2 / GCR / DeepSeek 関連設定を削除（約80行） | TODO |
| 2.1.4 | `ConvManager` クラスを `base.py` または独立ユーティリティに移動（必要なら） | TODO |
| 2.1.5 | ドキュメント更新: `installation_and_configuration.rst` から Azure 設定セクション削除 | TODO |

---

## Phase 2.2: pydantic_ai.py LiteLLM bridge の Claude 対応

`pydantic_ai.py` は現在 `OpenAIChatModel` + `LiteLLMProvider` でモデル構築し、`components/agent/base.py` の `PAIAgent` が使用している。

- 直ちに `AnthropicModel` へ差し替える前提は置かず、まずは `PAIAgent` が `anthropic/...` モデル名で正常動作する bridge を確立する
- provider は当面 `LiteLLMProvider` を維持し、LiteLLM backend が返す model/provider と整合させる
- `PROVIDER_TO_ENV_MAP` は `anthropic` を含む形へ更新し、OpenAI 固有の分岐を縮小する
- `openai_reasoning_effort` は bridge 実装の実 API に不要なら削除するが、検証なしの先行削除はしない

標準案:

```python
# preferred in Phase 2
from pydantic_ai.models.openai import OpenAIChatModel, OpenAIChatModelSettings
from pydantic_ai.providers.litellm import LiteLLMProvider

def get_agent_model() -> OpenAIChatModel:
    # selected_model は anthropic/claude-sonnet-4-20250514 のような LiteLLM 名
    settings = OpenAIChatModelSettings(max_tokens=..., temperature=...)
    return OpenAIChatModel(
        selected_model,
        provider=LiteLLMProvider(api_base=api_base, api_key=api_key),
        settings=settings,
    )
```

代替案:
- pydantic-ai 側に LiteLLM 用のより適切な抽象が確認できた場合のみ、その方式へ移行する
- その検証結果は Phase 2 の成果物に残し、Phase 4 の最終削除判断に使う

### タスク

| ID | 内容 | Status |
|---|---|---|
| 2.2.1 | `pydantic_ai.py`: `anthropic` provider を `PROVIDER_TO_ENV_MAP` に追加 | TODO |
| 2.2.2 | `pydantic_ai.py`: `selected_model=anthropic/...` で `PAIAgent` が動くことを確認 | TODO |
| 2.2.3 | `pydantic_ai.py`: `openai_reasoning_effort` 等の OpenAI 固有 settings を実利用ベースで整理 | TODO |
| 2.2.4 | LiteLLM bridge 代替案の feasibility spike を記録 | TODO |
| 2.2.5 | `components/agent/base.py` の動作確認テスト | TODO |

---

## Phase 2.3: tiktoken -> LiteLLM token counter

tiktoken 使用箇所は3つ: (1) `deprec.py:238` — Phase 2.1 削除で解消、(2) `finetune/scen/utils.py:9,89-93` — `_compute_column_stats()` で `gpt-3.5-turbo` トークナイザ使用 -> `litellm.token_counter()` に置換、(3) `utils/__init__.py:158` — コメントのみ。
`oai/utils/embedding.py` は既に `litellm.token_counter()` を使用しており変更不要。

### タスク

| ID | 内容 | Status |
|---|---|---|
| 2.3.1 | `finetune/scen/utils.py`: tiktoken import 削除、`litellm.encode` / `litellm.token_counter` に置換 | TODO |
| 2.3.2 | `finetune/scen/utils.py`: `_TOKENIZER_MODEL` を Claude 系 LiteLLM モデル名に更新 | TODO |
| 2.3.3 | `requirements.txt`: `tiktoken` 行を削除 | TODO |
| 2.3.4 | `kaggle_environment.yaml:333`: `tiktoken==0.7.0` を削除 | TODO |

---

## Phase 2.4: Embedding 移行

デフォルト `text-embedding-3-small`（`llm_conf.py:16`）を Voyage AI `voyage-3` に変更。
LiteLLM が既にサポート済み（`litellm.embedding(model="voyage/voyage-3", ...)`）。
変更箇所: `llm_conf.py:16`, `oai/utils/embedding.py` に `"voyage-3": 32000` 追加, `.devcontainer/env:22`, `app/finetune/llm/conf.py:101`, 環境変数 `VOYAGE_API_KEY` 追加。

### タスク

| ID | 内容 | Status |
|---|---|---|
| 2.4.1 | `llm_conf.py`: デフォルト embedding_model を `voyage/voyage-3` に変更 | TODO |
| 2.4.2 | `oai/utils/embedding.py`: Voyage モデルのトークン制限を追加 | TODO |
| 2.4.3 | `health_check.py`: embedding テストを Voyage 対応に更新 | TODO |
| 2.4.4 | `.devcontainer/env`, ドキュメントの embedding 設定を更新 | TODO |
| 2.4.5 | embedding の結合テスト（類似度計算の精度確認） | TODO |

---

## Phase 2.5: LangChain 依存整理

`langchain-community` は PDF 読み込み（`PyPDFLoader`, `PyPDFDirectoryLoader`）のみに使用。LLM/Agent/Chain 機能は未使用。
呼び出し元: `document_reader.py`, `factor_from_report.py`, `model_coder/task_loader.py`, `qlib/pdf_loader.py`。
`PyPDFLoader` は内部で `pypdf` を使用するため、直接 `pypdf` に置換。関数シグネチャは互換性のため維持。

置換イメージ:

```python
# before
from langchain_community.document_loaders import PyPDFDirectoryLoader, PyPDFLoader

# after — pypdf 直接使用、SimpleDocument dataclass で Document 互換
from pypdf import PdfReader

def load_documents_by_langchain(path: str) -> list:  # シグネチャ維持
    p = Path(path)
    files = sorted(p.rglob("*.pdf")) if p.is_dir() else [p]
    docs = []
    for f in files:
        for page in PdfReader(str(f)).pages:
            docs.append(SimpleDocument(page_content=page.extract_text() or "", metadata={"source": str(f)}))
    return docs
```

### タスク

| ID | 内容 | Status |
|---|---|---|
| 2.5.1 | `document_reader.py`: `langchain_community` -> `pypdf` 直接使用に置換 | TODO |
| 2.5.2 | `load_documents_by_langchain` / `process_documents_by_langchain` の関数シグネチャは維持（呼び出し元3箇所の互換性） | TODO |
| 2.5.3 | `requirements.txt`: `langchain`, `langchain-community` を削除、`pypdf` が既にあるか確認 | TODO |
| 2.5.4 | `kaggle_environment.yaml:154-157`: langchain 関連パッケージを削除 | TODO |

---

## Phase 2.6: llm_conf.py 設定更新

モデル名: `gpt-4-turbo` -> `anthropic/claude-sonnet-4-20250514`（llm_conf.py:15）, `chat_token_limit: 100000` -> `200000`（Claude 上限）, `finetune/benchmark/benchmark.py:10` の `gpt-4` も同様。
API キー: デフォルトの chat 経路は `OPENAI_API_KEY` 非依存にする。設定名の全面改名は Phase 4 の削除計画と整合を見ながら進める。

### タスク

| ID | 内容 | Status |
|---|---|---|
| 2.6.1 | `llm_conf.py`: `chat_model` デフォルトを Claude に変更 | TODO |
| 2.6.2 | `llm_conf.py`: `chat_token_limit` を 200000 に変更 | TODO |
| 2.6.3 | `llm_conf.py`: API キーフィールド名を `anthropic_api_key` 系に変更 | TODO |
| 2.6.4 | `llm_conf.py`: OpenAI Base URL 関連フィールドを削除 | TODO |
| 2.6.5 | `health_check.py`, `conf.py` 等の `OPENAI_API_KEY` 参照を更新 | TODO |
| 2.6.6 | `.devcontainer/env`: `OPENAI_API_KEY` -> `ANTHROPIC_API_KEY` | TODO |
| 2.6.7 | `finetune/benchmark/benchmark.py`: モデル名を Claude に更新 | TODO |
| 2.6.8 | `test/oai/test_llm_connectivity.py:7`: テスト用キー設定を更新 | TODO |

---

## 受け入れ条件

- [ ] `OPENAI_API_KEY` 未設定でも主要経路（LiteLLM backend, pydantic-ai bridge, factor_from_report を除く通常ループ）が動作する
- [ ] `PAIAgent` が LiteLLM bridge 経由で Claude モデルを使って動作する
- [ ] Embedding が `voyage/voyage-3` で動作し、類似度計算テストが通過する
- [ ] `llm_conf.py` のデフォルト設定のみで Claude + Voyage が動作する
- [ ] PDF 読み込み（factor_from_report）が langchain なしで動作する
- [ ] OpenAI 固有コードの最終削除タスクが Phase 4 に明確に残されている

---

## 実装順序

Phase 2.6（llm_conf.py 設定更新）-> 2.1（deprec.py 削除）-> 2.3（tiktoken 削除）-> 2.4（embedding 移行）-> 2.5（LangChain 整理）-> 2.2（pydantic-ai bridge 整理）。
2.2 は設定更新と残存依存の整理が済んだ後に着手した方が検証しやすい。

---

## 実装対象ファイル一覧

| ファイル | 操作 |
|---|---|
| `rdagent/oai/backend/deprec.py` | **DELETE** |
| `rdagent/oai/backend/__init__.py` | modify: DeprecBackend import 削除 |
| `rdagent/oai/backend/pydantic_ai.py` | modify: AnthropicModel 差替 |
| `rdagent/oai/llm_conf.py` | modify: モデル名・API キー・Azure 設定削除 |
| `rdagent/oai/utils/embedding.py` | modify: Voyage トークン制限追加 |
| `rdagent/components/agent/base.py` | verify: 動作確認のみ |
| `rdagent/components/document_reader/document_reader.py` | modify: pypdf 直接使用 |
| `rdagent/scenarios/finetune/scen/utils.py` | modify: tiktoken -> litellm |
| `rdagent/scenarios/finetune/benchmark/benchmark.py` | modify: モデル名 |
| `rdagent/app/utils/health_check.py` | modify: API キー参照 |
| `rdagent/app/finetune/llm/conf.py` | modify: embedding_models |
| `rdagent/components/coder/finetune/conf.py` | modify: OPENAI_API_KEY 参照 |
| `requirements.txt` | modify: パッケージ削除・変更 |
| `.devcontainer/env` | modify: 環境変数 |
| `rdagent/scenarios/data_science/sing_docker/kaggle_environment.yaml` | modify: tiktoken・langchain 削除 |
| `docs/installation_and_configuration.rst` | modify: Azure セクション削除、Anthropic 設定追加 |
| `test/oai/test_llm_connectivity.py` | modify: テスト用キー |
| `test/oai/test_embedding_and_similarity.py` | modify: Voyage 対応 |
