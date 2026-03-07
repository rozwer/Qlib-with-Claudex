# Phase 4: レガシー削除

作成日: 2026-03-07
起点: Phase 3 の公開準備完了
目的: OpenAI 専用コードとレガシー機構を完全に削除し、コードベースをクリーンにする。
依存: Phase 3 完了

実装スコープ:
- 主対象は `RD-Agent-with-Claudex/`
- `Qlib-with-Claudex/` は公開用補助ファイルの最終整理のみ
- Phase 2 で残した bridge/互換層の最終判断をここで行う

---

## レビュー反映事項

- `LoopBase` 本体は `rdagent/utils/workflow/loop.py` にあり、`rdagent/components/workflow/rd_loop.py` は RDLoop 実装側。削除対象の主座標は `utils/workflow/loop.py` に直す。
- `dump()` / `load()` は `rd_loop` 以外にも `data_science/loop.py` や CLI/ログ表示ユーティリティから参照されている。Phase 4.1 は call site 棚卸しを先に置く現行順で正しいが、対象範囲を workflow 配下に限定しない。
- `pydantic_ai.py` は Phase 2 で Anthropic 化しても残存 utility になる可能性があるため、削除は「不要になった場合のみ」とする。
- 既存ユーザー向け migration script はすぐ archive せず、少なくとも 1 リリース分は `scripts/legacy/` に残す前提にする。
- compatibility shim の完全除去は全 call site 移行が前提で、Phase 4 の受け入れ条件からは外す。代わりに「残っていても薄い互換層に縮退していること」を求める。

---

## Phase 4.1: セッション保存再開機構の廃止

### 現状の問題

LoopBase (`rdagent/utils/workflow/loop.py`) は `dump()` / `load()` メソッドで
ループ状態をシリアライズして保存・復元する。Phase 1 で artifact ベースの
`trace.json` + `manifest.json` を SSOT として導入したため、2 系統の状態管理が並存している。

- **レガシー系**: `LoopBase.dump()` がループカウンタ・Trace・Hypothesis を丸ごとシリアライズ
- **artifact 系**: `.claude/artifacts/rdloop/<run_id>/round_<N>/` に構造化 JSON を出力

二重状態は不整合の温床であり、Phase 4 でレガシー系を完全廃止する。

### 移行手順

| # | Task | 内容 | Status |
|---|------|------|--------|
| 4.1.1 | dump/load 呼び出し箇所の棚卸し | `rdagent/`, `rdagent/app/`, `rdagent/log/` を対象に全参照を列挙 | cc:TODO |
| 4.1.2 | artifact resume の網羅性検証 | dump/load が保存する全フィールドが artifact JSON でカバーされているか確認 | cc:TODO |
| 4.1.3 | LoopBase.dump() 削除 | メソッド本体を削除、呼び出し側を artifact 書込みに置換 | cc:TODO |
| 4.1.4 | LoopBase.load() 削除 | メソッド本体を削除、呼び出し側を artifact 読込みに置換 | cc:TODO |
| 4.1.5 | シリアライズファイル生成の除去 | レガシーのセッションファイル出力呼び出しを削除 | cc:TODO |
| 4.1.6 | CLI セッション引数の更新 | `--resume-session` 等のフラグが session file を参照している場合、artifact パスに変更 | cc:TODO |
| 4.1.7 | セッションファイル掃除ロジック削除 | 古いセッションファイルを掃除するユーティリティがあれば除去 | cc:TODO |
| 4.1.8 | マイグレーションスクリプト作成 | 既存 session → artifact JSON 変換ツールを `scripts/legacy/migrate_session.py` に配置 | cc:TODO |

### 後方互換

既存ユーザーがレガシーセッションを持っている場合に備え、マイグレーションスクリプトを提供する。
スクリプトは少なくとも 1 リリース分 `scripts/legacy/` に残し、その後の削除可否を判定する。

---

## Phase 4.2: rdagent/oai/ OpenAI 専用コードと bridge の最終整理

### 削除対象ファイル

| ファイル | 理由 |
|----------|------|
| `rdagent/oai/backend/deprec.py` | 直接 OpenAI SDK 呼び出し。Phase 2 で死活コード化済み |
| `rdagent/oai/backend/pydantic_ai.py` | LiteLLM bridge。Phase 2 の方式次第で書換 or 削除 |

### 修正対象ファイル（削除せず書き換え）

| ファイル | 修正内容 |
|----------|----------|
| `rdagent/oai/backend/__init__.py` | deprecated backend の import 文を除去 |
| `rdagent/oai/backend/base.py` | OpenAI 固有のエラーハンドリング (`openai.RateLimitError` 等) を汎用例外に置換 |
| `rdagent/oai/llm_conf.py` | `gpt-4-turbo` デフォルト値、Azure endpoint 設定を削除。Claude/Anthropic 設定のみ残す |

### タスク表

| # | Task | 内容 | Status |
|---|------|------|--------|
| 4.2.1 | deprec.py の参照確認 | import パスが他ファイルから参照されていないことを確認 | cc:TODO |
| 4.2.2 | deprec.py 削除 | ファイルを削除 | cc:TODO |
| 4.2.3 | pydantic_ai.py / PAIAgent の置換判定 | bridge を残すか、別実装に置換するかを決定 | cc:TODO |
| 4.2.4 | bridge 最終処理 | 判定結果に応じて `pydantic_ai.py` を簡素化 or 削除 | cc:TODO |
| 4.2.5 | __init__.py 整理 | deprecated import を除去 | cc:TODO |
| 4.2.6 | base.py 修正 | OpenAI 固有例外を汎用化 | cc:TODO |
| 4.2.7 | llm_conf.py 修正 | OpenAI/Azure 設定を除去、Claude 設定のみ保持 | cc:TODO |
| 4.2.8 | 残存参照の grep 監査 | `grep -rn "openai\|gpt-\|azure" rdagent/` で漏れを検出 | cc:TODO |
| 4.2.9 | import グラフ検証 | 削除モジュールへの import パスが残っていないことを確認 | cc:TODO |

---

## Phase 4.3: requirements.txt クリーンアップ

### 削除候補パッケージ

| パッケージ | 判断 |
|------------|------|
| `openai` | 削除。ただし LiteLLM と残存 bridge の依存を事前検証 |
| `pydantic-ai-slim[openai]` | bridge 置換完了後に削除。未置換なら先に agent 層を整理 |
| `tiktoken` | Anthropic tokenizer に置換済みなら削除。未使用確認が必要 |

### LiteLLM と openai の関係

LiteLLM は `openai` を optional dependency として持つ。Anthropic プロバイダのみ使用する場合、
`openai` パッケージなしで import 可能か検証が必要。

検証手順:
1. `pip uninstall openai` 実行
2. `python -c "from litellm import completion"` で import エラーの有無を確認
3. Anthropic provider で実際に completion を呼び出し動作確認
4. import エラーが出る場合、LiteLLM の該当コードを確認し issue を報告

### タスク表

| # | Task | 内容 | Status |
|---|------|------|--------|
| 4.3.1 | LiteLLM openai 依存の検証 | openai なしで LiteLLM の Anthropic provider が動くか確認 | cc:TODO |
| 4.3.2 | openai パッケージ削除 | 検証通過後 requirements.txt から除去 | cc:TODO |
| 4.3.3 | pydantic-ai-slim extra 整理 | bridge 置換完了後に `[openai]` extra を除去 | cc:TODO |
| 4.3.4 | tiktoken 使用箇所確認 | `grep -rn tiktoken rdagent/` で残存利用を確認 | cc:TODO |
| 4.3.5 | tiktoken 削除 | 未使用確認後 requirements.txt から除去 | cc:TODO |
| 4.3.6 | pip install 検証 | クリーン環境で `pip install -r requirements.txt` が成功することを確認 | cc:TODO |
| 4.3.7 | テスト実行 | 全テストスイートを削除後の依存で通す | cc:TODO |

---

## Phase 4.4: 最終検証

| # | Task | 内容 | Status |
|---|------|------|--------|
| 4.4.1 | 全回帰テスト | `pytest` フルスイート実行 | cc:TODO |
| 4.4.2 | grep 監査 | `grep -rn "openai" rdagent/` — コメント・ドキュメント説明文以外でゼロ件 | cc:TODO |
| 4.4.3 | import グラフ分析 | `importlib` / `ast` で循環 import・壊れたパスがないことを確認 | cc:TODO |
| 4.4.4 | Docker ビルド | クリーン requirements で Docker image をビルド・起動 | cc:TODO |
| 4.4.5 | E2E ループテスト | factor シナリオで RDLoop を 3 ラウンド実行し、正常完走を確認 | cc:TODO |
| 4.4.6 | 性能比較 | 移行前後でラウンド所要時間・メモリ使用量を比較し回帰がないことを確認 | cc:TODO |

---

## Phase 4.5: クリーンアップ

| # | Task | 内容 | Status |
|---|------|------|--------|
| 4.5.1 | 互換 shim 縮退 | 全呼び出し元が移行済みなら除去、未移行なら最小互換層まで縮退 | cc:TODO |
| 4.5.2 | マイグレーションスクリプト整理 | `scripts/legacy/migrate_session.py` の残置期間と削除条件を決定 | cc:TODO |
| 4.5.3 | CLAUDE.md 更新 | 移行関連の注記を削除、最終アーキテクチャを反映 | cc:TODO |
| 4.5.4 | 設計ドキュメント最終整理 | Phase 1-4 のドキュメントに完了ステータスを記載 | cc:TODO |
| 4.5.5 | CHANGELOG 記載 | Breaking changes（session format、削除モジュール）を明記 | cc:TODO |

---

## 受け入れ条件

- [ ] `rdagent/oai/` に OpenAI 専用コードが残っていない
- [ ] `requirements.txt` に `openai`, `tiktoken` がない
- [ ] `pydantic-ai-slim[openai]` extra が不要化していれば削除済み。残す場合は optional feature として隔離・文書化されている
- [ ] `grep -rn "openai" rdagent/` がコメント・ドキュメント以外でゼロ件
- [ ] `LoopBase.dump()` / `load()` が削除されている
- [ ] レガシーのセッションファイル生成がない
- [ ] artifact ベースの resume が全シナリオで動作する
- [ ] Docker ビルドがクリーン requirements で成功する
- [ ] E2E factor シナリオが 3 ラウンド正常完走する
- [ ] 全テストスイートがパスする
- [ ] 互換 shim が不要なら除去、必要なら最小互換層に縮退している

---

## 実装対象ファイル

| ファイル | 操作 | 備考 |
|----------|------|------|
| `rdagent/oai/backend/deprec.py` | **DELETE** | OpenAI SDK 直接呼び出し |
| `rdagent/oai/backend/pydantic_ai.py` | MODIFY or DELETE | bridge として縮退させるか最終判定 |
| `rdagent/oai/backend/__init__.py` | MODIFY | deprecated import 除去 |
| `rdagent/oai/backend/base.py` | MODIFY | OpenAI 固有例外を汎用化 |
| `rdagent/oai/llm_conf.py` | MODIFY | OpenAI/Azure 設定除去 |
| `rdagent/utils/workflow/loop.py` | MODIFY | LoopBase.dump()/load() 削除 |
| `rdagent/components/workflow/rd_loop.py` | MODIFY | artifact resume に合わせて呼び出し側調整 |
| `requirements.txt` | MODIFY | openai, tiktoken 除去 |
| `setup.py` / `pyproject.toml` | MODIFY | 依存リスト同期 |
| `Dockerfile` | MODIFY | 不要パッケージ除去の反映 |
| `scripts/legacy/migrate_session.py` | CREATE | session → artifact 変換 |
| `CLAUDE.md` | MODIFY | 移行注記を削除 |

---

## リスクと対策

| リスク | 影響 | 対策 |
|--------|------|------|
| **LiteLLM / pydantic-ai bridge の openai 依存** | `openai` パッケージや extra を一気に消すと agent 層が壊れる可能性 | 4.2.3 と 4.3.1 を連動させ、bridge 置換後に削除する |
| **既存ユーザーの session ファイル** | レガシーセッションが読めなくなる | マイグレーションスクリプト提供 + CHANGELOG で Breaking Change 明記 |
| **サードパーティプラグインの rdagent.oai 依存** | 削除モジュールを import しているプラグインが壊れる | `rdagent.oai.backend.deprec` に `raise ImportError("Removed in v2. Use ClaudeCodeAPIBackend.")` のスタブを一時的に残す選択肢を検討 |
| **積極的削除による import 破損** | 想定外の間接 import が壊れる | 4.4.3 の import グラフ分析を削除前に実施し、安全な削除順序を決定 |
| **tiktoken の隠れ依存** | rdagent 以外のコード（テストユーティリティ等）が tiktoken を使用 | grep 範囲をリポジトリ全体に拡大して確認 |
