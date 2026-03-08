# Qlib_FX リポジトリ作成 実装計画

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 株式版 Claudex リポジトリを FX 用にフォークし、FX 移行レポートに従って編集を開始できる状態にする

**Architecture:** `/Users/roz/Desktop/Qlib_FX/` に独立親リポジトリを作成。`Qlib-with-Claudex/` と `RD-Agent-with-Claudex/` を除外対象を省いてコピーし、`Qlib_FX-with-Claudex/` / `RD-Agent_FX-with-Claudex/` にリネーム。docs をコピーし株式版を archive 移動。CLAUDE.md / Plans.md を FX 用に新規作成。

**Tech Stack:** bash (rsync, git), markdown

**Design Doc:** [2026-03-08-fx-fork-design.md](2026-03-08-fx-fork-design.md)
**Migration Spec:** [FX移行レポート.md](FX移行レポート.md)

---

### Task 1: 親ディレクトリ作成 + git init

**Files:**
- Create: `/Users/roz/Desktop/Qlib_FX/`
- Create: `/Users/roz/Desktop/Qlib_FX/.gitignore`

**Step 1: ディレクトリ作成と git 初期化**

```bash
mkdir -p /Users/roz/Desktop/Qlib_FX
cd /Users/roz/Desktop/Qlib_FX
git init
```

**Step 2: .gitignore 作成**

```gitignore
# Subprojects (managed separately)
Qlib_FX-with-Claudex/
RD-Agent_FX-with-Claudex/

# Claude Code state
.claude/state/
.claude/sessions/
.claude/logs/
.claude/memory/
.claude/agent-memory/

# OS
.DS_Store

# Python
__pycache__/
*.pyc
.venv/
*.egg-info/

# Generated data
git_ignore_folder/
```

**Step 3: 検証**

```bash
ls -la /Users/roz/Desktop/Qlib_FX/.git/
cat /Users/roz/Desktop/Qlib_FX/.gitignore
```

Expected: `.git/` ディレクトリが存在し、`.gitignore` が上記内容。

---

### Task 2: Qlib_FX-with-Claudex をコピー

**Files:**
- Create: `/Users/roz/Desktop/Qlib_FX/Qlib_FX-with-Claudex/` (rsync from Qlib-with-Claudex)

**Step 1: rsync でコピー（.git 除外）**

```bash
rsync -a \
  --exclude='.git/' \
  --exclude='.DS_Store' \
  --exclude='__pycache__/' \
  /Users/roz/Desktop/Qlib/Qlib-with-Claudex/ \
  /Users/roz/Desktop/Qlib_FX/Qlib_FX-with-Claudex/
```

**Step 2: サブリポで git init**

```bash
cd /Users/roz/Desktop/Qlib_FX/Qlib_FX-with-Claudex
git init
git remote add upstream https://github.com/microsoft/qlib.git
```

**Step 3: 検証**

```bash
du -sh /Users/roz/Desktop/Qlib_FX/Qlib_FX-with-Claudex/
ls /Users/roz/Desktop/Qlib_FX/Qlib_FX-with-Claudex/qlib/
git -C /Users/roz/Desktop/Qlib_FX/Qlib_FX-with-Claudex remote -v
```

Expected: ~28MB、`qlib/` ディレクトリ存在、upstream リモート設定済み。

---

### Task 3: RD-Agent_FX-with-Claudex をコピー

**Files:**
- Create: `/Users/roz/Desktop/Qlib_FX/RD-Agent_FX-with-Claudex/` (rsync from RD-Agent-with-Claudex)

**Step 1: rsync でコピー（大型ファイル除外）**

```bash
rsync -a \
  --exclude='.git/' \
  --exclude='.venv/' \
  --exclude='git_ignore_folder/' \
  --exclude='.pytest_cache/' \
  --exclude='.DS_Store' \
  --exclude='__pycache__/' \
  /Users/roz/Desktop/Qlib/RD-Agent-with-Claudex/ \
  /Users/roz/Desktop/Qlib_FX/RD-Agent_FX-with-Claudex/
```

**Step 2: サブリポで git init**

```bash
cd /Users/roz/Desktop/Qlib_FX/RD-Agent_FX-with-Claudex
git init
git remote add upstream https://github.com/microsoft/RD-Agent.git
```

**Step 3: 検証**

```bash
du -sh /Users/roz/Desktop/Qlib_FX/RD-Agent_FX-with-Claudex/
ls /Users/roz/Desktop/Qlib_FX/RD-Agent_FX-with-Claudex/rdagent/
git -C /Users/roz/Desktop/Qlib_FX/RD-Agent_FX-with-Claudex remote -v
# .venv が除外されていることを確認
ls /Users/roz/Desktop/Qlib_FX/RD-Agent_FX-with-Claudex/.venv/ 2>&1 | head -1
```

Expected: ~50MB 以下（.venv/git_ignore_folder 除外で大幅削減）、`rdagent/` 存在、upstream 設定済み、`.venv` は「No such file or directory」。

---

### Task 4: docs ディレクトリのコピーと archive 整理

**Files:**
- Create: `/Users/roz/Desktop/Qlib_FX/docs/` (copy from Qlib/docs)
- Create: `/Users/roz/Desktop/Qlib_FX/docs/plans/archive/`

**Step 1: docs をコピー**

```bash
rsync -a \
  --exclude='.DS_Store' \
  /Users/roz/Desktop/Qlib/docs/ \
  /Users/roz/Desktop/Qlib_FX/docs/
```

**Step 2: 株式版設計ドキュメントを archive に移動**

以下のファイルは株式版（China A-shares）の設計ドキュメント。FX リポジトリでは参照用に archive に退避する。

```bash
mkdir -p /Users/roz/Desktop/Qlib_FX/docs/plans/archive
cd /Users/roz/Desktop/Qlib_FX/docs/plans

# 株式版の Phase ドキュメント
mv phase-1A.md phase-1B.md phase-2.md phase-3.md phase-4.md archive/

# 株式版の設計ドキュメント
mv 基本方針.md OpenAI依存箇所レポート.md ClaudeCode置換設計.md Adapter詳細設計.md archive/

# FX fork design doc も株式→FX の移行プロセスなので archive
mv 2026-03-08-fx-fork-design.md 2026-03-08-fx-fork-impl.md archive/
```

**Step 3: 検証**

```bash
ls /Users/roz/Desktop/Qlib_FX/docs/plans/
ls /Users/roz/Desktop/Qlib_FX/docs/plans/archive/
ls /Users/roz/Desktop/Qlib_FX/docs/skills/
ls /Users/roz/Desktop/Qlib_FX/docs/subagents/
```

Expected:
- `docs/plans/`: `FX移行レポート.md` と `archive/` のみ
- `docs/plans/archive/`: 株式版ドキュメント群
- `docs/skills/`: 5 つのスキルファイル（後で FX 化）
- `docs/subagents/`: 3 つのサブエージェント定義（後で FX 化）

---

### Task 5: 親リポの CLAUDE.md 作成

**Files:**
- Create: `/Users/roz/Desktop/Qlib_FX/CLAUDE.md`

**Step 1: CLAUDE.md を作成**

```markdown
# Qlib_FX-with-Claudex / RD-Agent_FX-with-Claudex

Microsoft Qlib と RD-Agent をフォークし、FX（外国為替）トレーディング研究に特化した OSS。
LLM 依存を Claude Code + サブエージェント + Codex で置換。

## Project Structure

```
Qlib_FX/
├── Qlib_FX-with-Claudex/        # microsoft/qlib フォーク（FX データ基盤）
├── RD-Agent_FX-with-Claudex/     # microsoft/RD-Agent フォーク（FX R&D エージェント）
└── docs/
    ├── plans/FX移行レポート.md   # 変更仕様書（39 件 + 新規 4 件）
    ├── skills/                   # スキル定義
    └── subagents/                # サブエージェント定義
```

## Key Architecture

**制御の反転**: Claude Code が Python/Qlib を道具として FX シグナル研究を自律実行。

**Option B 方針**: Qlib のデータ基盤（HDF5 + Expression Engine）は利用し、執行/会計/評価は FX 専用に独立実装。

### Adapter 層

| スロット | Adapter | 詳細 |
|---|---|---|
| hypothesis_gen | ClaudeCodeFactorHypothesisGenAdapter | FX シグナル仮説生成 |
| hypothesis2experiment | ClaudeCodeFactorH2EAdapter | 仮説→実験仕様 |
| coder | ClaudeCodeFactorCoderAdapter | Codex で FX シグナルコード生成 |
| runner | FXRunner（新規） | FX バックテスト（スプレッド/スワップ/レバレッジ対応） |
| summarizer | ClaudeCodeFactorSummarizerAdapter | Sharpe/PnL/DD 評価・フィードバック |

## FX 固有設計

- **主要評価指標**: Sharpe Ratio（IC は Panel FX 時の補助指標）
- **データカラム**: bid/ask OHLC, mid OHLC, spread, tick_volume, swap_long/short
- **Session Cut**: NY Close 基準（17:00 EST/EDT、DST 対応）
- **Annualization**: 周期依存パラメータ（日足 260、時間足 6,240、分足 374,400）

## Design Documents

- [FX移行レポート](docs/plans/FX移行レポート.md) — 変更仕様書
- [archive/](docs/plans/archive/) — 株式版設計ドキュメント群

## Conventions

- ドキュメントは簡潔な日本語
- ライセンス: MIT 継承
- ブランド名: `_FX-with-Claudex`
- FX-0〜FX-5 のフェーズ制
```

**Step 2: 検証**

```bash
head -5 /Users/roz/Desktop/Qlib_FX/CLAUDE.md
```

Expected: `# Qlib_FX-with-Claudex` で始まる。

---

### Task 6: Qlib_FX-with-Claudex の CLAUDE.md 作成

**Files:**
- Modify: `/Users/roz/Desktop/Qlib_FX/Qlib_FX-with-Claudex/CLAUDE.md` (overwrite stock version)

**Step 1: FX 用 CLAUDE.md で上書き**

```markdown
# Qlib_FX-with-Claudex

Microsoft Qlib fork for FX (foreign exchange) quantitative research with Claude Code orchestration.

## Overview

Qlib のデータ基盤（HDF5 + Expression Engine）を FX データに適用するフォーク。Qlib backtest 系（exchange.py, position.py, report.py）は改修せず、FX 専用 runner で代替する（Option B）。

## Key Paths

- `qlib/` — Core Qlib library
- `qlib/constant.py` — `REG_FX` リージョン追加対象
- `qlib/data/data.py` — CalendarProvider / InstrumentProvider（FX 対応対象）
- `qlib/utils/time.py` — DST / Session Cut 対応対象
- `qlib/contrib/data/handler.py` — FX handler 新規追加対象
- `qlib/contrib/evaluate.py` — Annualization scaler パラメータ化対象
- `scripts/data_collector/fx/` — FX データコレクター（新規作成）

## Data Setup (FX)

```bash
# FX データ収集（Phase FX-1 で実装）
python scripts/data_collector/fx/collect_fx.py --pairs USDJPY,EURUSD,GBPUSD --freq 1h

# Qlib 初期化（FX リージョン）
python -c "import qlib; qlib.init(provider_uri='~/.qlib/qlib_data/fx_data', region_type='fx')"
```

## FX Data Columns

| カラム | 説明 |
|--------|------|
| `$bid_open, $bid_close, $bid_high, $bid_low` | Bid 側 OHLC |
| `$ask_open, $ask_close, $ask_high, $ask_low` | Ask 側 OHLC |
| `$mid_open, $mid_close, $mid_high, $mid_low` | Mid（計算用） |
| `$spread` | Ask - Bid |
| `$tick_volume` | Tick volume（注: 集中市場出来高ではない） |
| `$swap_long, $swap_short` | スワップポイント（日次） |

## Don't Touch (Option B)

- `qlib/backtest/exchange.py` — 株式前提のまま放置
- `qlib/backtest/position.py` — 同上
- `qlib/backtest/report.py` — 同上
- `qlib/workflow/record_temp.py` — 252 日前提のまま

## Conventions

- MIT license (inherited from Microsoft Qlib)
- FX data directory: `~/.qlib/qlib_data/fx_data/`
```

**Step 2: 検証**

```bash
head -3 /Users/roz/Desktop/Qlib_FX/Qlib_FX-with-Claudex/CLAUDE.md
grep "REG_FX" /Users/roz/Desktop/Qlib_FX/Qlib_FX-with-Claudex/CLAUDE.md
```

Expected: `# Qlib_FX-with-Claudex` で始まり、`REG_FX` が含まれる。

---

### Task 7: RD-Agent_FX-with-Claudex の CLAUDE.md 作成

**Files:**
- Modify: `/Users/roz/Desktop/Qlib_FX/RD-Agent_FX-with-Claudex/CLAUDE.md` (overwrite stock version)

**Step 1: FX 用 CLAUDE.md で上書き**

```markdown
# RD-Agent_FX-with-Claudex

Microsoft RD-Agent fork: FX signal research with Claude Code + subagents + Codex.

## Architecture

**Control Inversion**: Claude Code orchestrates Python/Qlib as tools for FX signal discovery.

RDLoop 5-slot adapter pattern:

| Slot | Adapter | Component |
|------|---------|-----------|
| hypothesis_gen | ClaudeCodeFactorHypothesisGenAdapter | Planner subagent |
| hypothesis2experiment | ClaudeCodeFactorH2EAdapter | Planner subagent |
| coder | ClaudeCodeFactorCoderAdapter | Codex |
| runner | FXRunner（新規） | FX backtester |
| summarizer | ClaudeCodeFactorSummarizerAdapter | Evaluator subagent |

## Key Paths

- `rdagent/adapters/factor/` — Adapter layer（FX 対応編集対象）
- `rdagent/scenarios/qlib/` — Qlib scenario（FX 用語に書換え対象）
- `rdagent/scenarios/fx/` — FX scenario（新規作成: runner, handler）
- `rdagent/oai/backend/` — LLM backends（変更なし）
- `rdagent/core/` — Data structures（変更なし）
- `test/adapters/` — テスト群（FX メトリクス対応）

## Artifact Structure

```
.claude/artifacts/rdloop/<run_id>/
  trace.json
  round_<N>/
    hypothesis.json
    experiment.json
    run_result.json     # FX schema: sharpe_ratio primary, ic nullable
    feedback.json
    implementations/
      factor.py         # FX signal code
```

## Primary Metric: Sharpe Ratio

株式版の IC (Information Coefficient) から Sharpe Ratio に主指標を変更。
IC は Panel FX 時の補助診断指標として nullable で残す。

## Configuration

Default: `LiteLLMAPIBackend` with `anthropic/claude-sonnet-4-20250514`.
Set `ANTHROPIC_API_KEY` environment variable.

## Testing

```bash
cd RD-Agent_FX-with-Claudex
source .venv/bin/activate  # Phase FX-1 で再作成
pytest test/adapters/ -v
```

## Conventions

- Documentation in concise Japanese
- MIT license
- Brand: `_FX-with-Claudex`
- Primary scope: FX signal scenario
```

**Step 2: 検証**

```bash
head -3 /Users/roz/Desktop/Qlib_FX/RD-Agent_FX-with-Claudex/CLAUDE.md
grep "FXRunner" /Users/roz/Desktop/Qlib_FX/RD-Agent_FX-with-Claudex/CLAUDE.md
grep "Sharpe" /Users/roz/Desktop/Qlib_FX/RD-Agent_FX-with-Claudex/CLAUDE.md
```

Expected: `# RD-Agent_FX-with-Claudex`、`FXRunner`、`Sharpe` が含まれる。

---

### Task 8: Plans.md 作成（FX フェーズ）

**Files:**
- Create: `/Users/roz/Desktop/Qlib_FX/Plans.md`

**Step 1: FX 用 Plans.md を作成**

FX移行レポートの Phase FX-0〜FX-5 をチェックリスト形式で展開する。

```markdown
# Plans — Qlib_FX-with-Claudex Migration

FX（外国為替）対応への移行計画。全体仕様は [FX移行レポート](docs/plans/FX移行レポート.md) を参照。

- `Qlib_FX-with-Claudex/`: Layer 1 データ基盤
- `RD-Agent_FX-with-Claudex/`: Layer 2-3 シナリオ・Adapter
- `docs/`: Layer 4 スキル・サブエージェント・テスト

## Phase FX-0: 設計確定（コード変更なし）

> 目標: FX 移行の前提となる 6 設計判断を確定し、文書化。

- [ ] 取引モデル定義（決済慣行、コスト、スワップ、レバレッジ、Session Cut）
- [ ] 主要評価指標確定（Sharpe 主判定、IC 補助、Hit Rate / PF / DD）
- [ ] データソース選定（MT5 / OANDA / Dukascopy / HistData）
- [ ] データ周期選定（tick / 1min / 1h / daily）
- [ ] run_result.json schema 確定（schema_version, status, primary_metric, secondary_metrics, meta）
- [ ] FX handler 特徴量リスト設計（bid/ask OHLC, spread, tick_volume, swap）

**完了条件**: 6 項目 + schema + 特徴量リストが文書化されレビュー済み。

## Phase FX-1: データ基盤 + Schema + Runner Stub

> 目標: FX データを HDF5 に格納し `qlib.init(region="fx")` で読み込み可能に。Runner stub が schema 準拠 JSON を出力。

- [ ] FX scenario ディレクトリ作成（N1: `rdagent/scenarios/fx/`）
- [ ] FX データコレクター新規作成（Layer 1 #8, N4）
- [ ] FX handler 新規作成（Layer 1 #6）
- [ ] CalendarProvider + Session Cut 対応（Layer 1 #2, #5）
- [ ] InstrumentProvider 通貨ペアユニバース対応（Layer 1 #3）
- [ ] REG_FX リージョン追加（Layer 1 #1）
- [ ] qlib.init() FX 対応（Layer 1 #4）
- [ ] Annualization scaler パラメータ化（Layer 1 #7）
- [ ] FX runner stub 作成（N2 骨格: run_result schema 準拠ダミー出力）

**完了条件**: FX データ HDF5 読込可能 + runner stub が schema 準拠 JSON 出力。

## Phase FX-2: シナリオ設定 + プロンプト + 評価系

> 目標: prompts/YAML が FX 用語に統一。feedback.py が runner stub 出力を正しくパース・評価。

- [ ] prompts.yaml 両方を FX 用語に書換え（Layer 2 #15, #16）
- [ ] conf_baseline.yaml 系を FX 設定に（Layer 2 #9, #10）
- [ ] generate.py FX データ対応（Layer 2 #11）
- [ ] utils.py FX 対応（Layer 2 #13）
- [ ] factor_experiment.py FX コンテキスト（Layer 2 #14）
- [ ] README.md データ形式更新（Layer 2 #12）
- [ ] feedback.py 評価指標変更（Layer 2 #18）
- [ ] factor_runner.py 更新（Layer 2 #17）
- [ ] conf.py 期間更新（Layer 2 #19）

**完了条件**: prompts/YAML FX 統一 + feedback.py が runner stub 出力を正しく評価。

## Phase FX-3: サブエージェント + Adapter

> 目標: subagent 定義と adapter コードが FX 対応。trace_view が primary_metric でソート。

- [ ] docs/subagents/planner.md FX 化（Layer 3 #20）
- [ ] docs/subagents/evaluator.md FX 化（Layer 3 #21）
- [ ] docs/subagents/coder.md FX 化（Layer 3 #22）
- [ ] adapters/factor/planner.py FX 化（Layer 3 #23）
- [ ] adapters/factor/evaluator.py Sharpe ベース化（Layer 3 #24）
- [ ] adapters/factor/trace_view.py primary_metric パラメータ化（Layer 3 #25）
- [ ] adapters/factor/hypothesis_gen.py FX 例（Layer 3 #26）
- [ ] adapters/factor/coder.py FX テンプレート（Layer 3 #27）
- [ ] adapters/factor/h2e.py FX 例（Layer 3 #28）
- [ ] adapters/factor/summarizer.py FX 用語（Layer 3 #29）

**完了条件**: subagent + adapter FX 対応完了 + trace_view primary_metric ソート動作確認。

## Phase FX-4: スキル・テスト・ドキュメント

> 目標: テスト green + skill/ドキュメントが FX 用語統一。

- [ ] docs/skills/ 4 ファイル FX 化（Layer 4 #30〜33）
- [ ] test/adapters/test_planner_evaluator.py FX 化（Layer 4 #34）
- [ ] test/adapters/test_adapters.py FX 化（Layer 4 #35）
- [ ] test/adapters/test_trace_view.py パラメータ化（Layer 4 #36）
- [ ] test/adapters/test_resume.py パラメータ化（Layer 4 #37）
- [ ] docs/plans/Adapter詳細設計.md IC 例更新（Layer 4 #38）
- [ ] docs/plans/ClaudeCode置換設計.md TraceView 例更新（Layer 4 #39）

**完了条件**: `test/adapters/` 全テスト green + ドキュメント FX 用語統一。

## Phase FX-5: 本番 Backtester + E2E

> 目標: 実 FX データで RD ループ 1 周完走。

- [ ] FX runner stub → 本番実装（スプレッド、スワップ、レバレッジ）
- [ ] FX handler 本番実装（N3: RD-Agent scenario 用ラッパー）
- [ ] FX scenario ディレクトリ本番モジュール整備
- [ ] E2E 統合テスト（実 FX データ使用）

**完了条件**: 実 FX データで 1 周完走。Sharpe/PnL/DD が正しく計算。

---

## Phase Files

- [FX移行レポート.md](docs/plans/FX移行レポート.md)
- [archive/](docs/plans/archive/) — 株式版ドキュメント
```

**Step 2: 検証**

```bash
grep -c "\- \[ \]" /Users/roz/Desktop/Qlib_FX/Plans.md
grep "FX-0" /Users/roz/Desktop/Qlib_FX/Plans.md | head -1
```

Expected: チェックボックス総数が FX 移行レポートと整合、`Phase FX-0` セクションが存在。

---

### Task 9: .claude/ 最小構成の作成

**Files:**
- Create: `/Users/roz/Desktop/Qlib_FX/.claude/settings.local.json`

**Step 1: .claude ディレクトリと最小設定を作成**

```bash
mkdir -p /Users/roz/Desktop/Qlib_FX/.claude
```

```json
{
  "permissions": {
    "allow": [],
    "deny": []
  }
}
```

> 注: skills/ や subagents/ は `.claude/` 内には作成しない。docs/skills/ と docs/subagents/ が SSOT。Phase FX-3〜4 で FX 用に編集する。

**Step 2: 検証**

```bash
ls /Users/roz/Desktop/Qlib_FX/.claude/
```

Expected: `settings.local.json` のみ。

---

### Task 10: 初回コミット

**Step 1: 全体サイズ確認**

```bash
du -sh /Users/roz/Desktop/Qlib_FX/ --exclude='Qlib_FX-with-Claudex' --exclude='RD-Agent_FX-with-Claudex'
du -sh /Users/roz/Desktop/Qlib_FX/
```

Expected: サブリポ除外で数 MB、全体で ~50MB。

**Step 2: 親リポのファイルをステージング**

```bash
cd /Users/roz/Desktop/Qlib_FX
git add .gitignore CLAUDE.md Plans.md docs/ .claude/
git status
```

Expected: サブリポ（`Qlib_FX-with-Claudex/`, `RD-Agent_FX-with-Claudex/`）は .gitignore で除外。docs/ と設定ファイルのみステージング。

**Step 3: 初回コミット**

```bash
git commit -m "Initial setup: Qlib_FX repository for FX trading research

Fork of Claudex series (Qlib-with-Claudex / RD-Agent-with-Claudex).
Option B: Use Qlib data infrastructure, build independent FX execution/evaluation.
Stock-version design docs archived in docs/plans/archive/.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

**Step 4: サブリポの初回コミット**

```bash
cd /Users/roz/Desktop/Qlib_FX/Qlib_FX-with-Claudex
git add -A
git commit -m "Initial import from Qlib-with-Claudex (fresh history for FX fork)

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"

cd /Users/roz/Desktop/Qlib_FX/RD-Agent_FX-with-Claudex
git add -A
git commit -m "Initial import from RD-Agent-with-Claudex (fresh history for FX fork)

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

**Step 5: 検証**

```bash
git -C /Users/roz/Desktop/Qlib_FX log --oneline
git -C /Users/roz/Desktop/Qlib_FX/Qlib_FX-with-Claudex log --oneline
git -C /Users/roz/Desktop/Qlib_FX/RD-Agent_FX-with-Claudex log --oneline
```

Expected: 各リポに 1 コミットずつ。

---

### Task 11: 最終検証

**Step 1: ディレクトリ構造の確認**

```bash
find /Users/roz/Desktop/Qlib_FX -maxdepth 2 -type d | sort | head -30
```

Expected: 設計書の最終構造と一致:
```
Qlib_FX/
├── .claude/
├── .git/
├── Qlib_FX-with-Claudex/
│   ├── .git/
│   └── qlib/
├── RD-Agent_FX-with-Claudex/
│   ├── .git/
│   └── rdagent/
└── docs/
    ├── plans/
    │   ├── archive/
    │   └── FX移行レポート.md
    ├── skills/
    └── subagents/
```

**Step 2: 除外確認**

```bash
# これらが存在しないことを確認
test -d /Users/roz/Desktop/Qlib_FX/RD-Agent_FX-with-Claudex/.venv && echo "FAIL: .venv exists" || echo "OK: .venv excluded"
test -d /Users/roz/Desktop/Qlib_FX/RD-Agent_FX-with-Claudex/git_ignore_folder && echo "FAIL: git_ignore_folder exists" || echo "OK: git_ignore_folder excluded"
```

**Step 3: CLAUDE.md 内容確認**

```bash
head -1 /Users/roz/Desktop/Qlib_FX/CLAUDE.md
head -1 /Users/roz/Desktop/Qlib_FX/Qlib_FX-with-Claudex/CLAUDE.md
head -1 /Users/roz/Desktop/Qlib_FX/RD-Agent_FX-with-Claudex/CLAUDE.md
```

Expected: 各ファイルが FX 用のタイトルで始まる（株式版の内容ではない）。

---

## 次のステップ

Task 1〜11 を完了すると `/Users/roz/Desktop/Qlib_FX/` が FX 開発可能な状態になる。
その後は `Plans.md` の Phase FX-0 から順に FX移行レポートに従って実装を進める。

Phase FX-0 は設計確定（コード変更なし）のため、別の実装計画として切り出す。
