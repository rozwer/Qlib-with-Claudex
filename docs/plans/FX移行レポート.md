# FX移行 変更箇所レポート

Claudex シリーズを最終的に FX（外国為替）対応に寄せるための変更箇所一覧。

## 概要

変更は 4 レイヤー・既存 39 件 + 新規 4 件。方針は **Option B: Qlib のデータ/特徴量基盤は利用、執行/会計/評価は独立実装**。

### 前提: 研究対象タイプ

FX 移行にあたり、対象を明確にする:

| タイプ | 説明 | IC の扱い |
|--------|------|-----------|
| **Panel FX**（多通貨横断） | 複数ペアのクロスセクション研究 | 補助診断指標として残す |
| **Single-pair TS**（単一ペア時系列） | 1ペアの時系列売買 | IC 不要、Sharpe/PnL 中心 |

→ 本レポートでは **Panel FX** を主対象とし、IC は補助指標として温存する。

---

## 事前に確定すべき設計判断（6項目）

実装着手前に以下を確定する。これが決まらないと Layer 2〜4 の書換えが二度手間になる。

### 1. Qlib フォーク深度

| Option | 内容 | 工数 | 推奨 |
|--------|------|------|------|
| A | Qlib コアのカレンダー/ポジション/Exchange を直接改修 | 大 | — |
| **B** | **Qlib のデータ基盤（HDF5 + Expression Engine）だけ借り、執行/会計/評価は独立実装** | 中 | **推奨** |

Option B の場合、Qlib backtest 系（exchange.py, position.py, report.py 等）は**改修せず放置**。代わりに FX 専用の runner/backtester を新規作成する。

### 2. 主要評価指標

| 指標 | 役割 | 株式での対応 |
|------|------|-------------|
| **Sharpe Ratio** | 主判定指標 | IC |
| Hit Rate | 方向予測精度 | Rank IC |
| Profit Factor | 総利益/総損失 | Annualized Return |
| Maximum Drawdown | リスク管理 | Max Drawdown（同じ） |
| IC | **補助診断**（Panel FX 時のみ） | IC（主指標だった） |

### 3. データソース

| 候補 | 特徴 |
|------|------|
| MetaTrader 5 API | 国内 FX ブローカー対応、ティック〜日足 |
| OANDA API | REST API、過去データ豊富 |
| Dukascopy | 高品質ティックデータ、無料 |
| HistData.com | 過去データ CSV、無料 |

### 4. データ周期

tick / 1min / 1h / daily のどれをメインにするか。RD ループの iteration 速度に直結。

### 5. FX 取引モデル定義

株式と根本的に異なる以下を先に制度定義として固定する:

| 項目 | 株式（現状） | FX で必要な定義 |
|------|-------------|----------------|
| 決済慣行 | T+1 | スポット T+2 / CFD 型は即時。どちらを採用するか |
| 取引コスト | 手数料率 0.05%/0.15% | **Bid/Ask スプレッド** + スリッページ |
| スワップ/ロールオーバー | なし | **水曜3日分、tom-next、ブローカー差**。PnL に大きく影響 |
| レバレッジ/証拠金 | なし（現物） | **必要証拠金、ロスカット水準**。account とは別物 |
| 値幅制限 | 9.5%（A株） | なし |
| Volume の意味 | 集中市場出来高 | **Tick volume**（ベンダー依存、流動性指標として弱い） |
| 口座通貨換算 | 不要（CNY 建て） | クロスペアは **pip value 換算** が必要 |

### 6. 日足の切り方（Session Cut）

| 方式 | 説明 |
|------|------|
| NY Close 基準 | 業界標準。17:00 New York time（EST/EDT）で日足を切る |
| UTC 基準 | シンプルだがスワップ計算と不整合 |
| DST 処理 | 米国 DST で EST ↔ EDT が年2回切替。カレンダーに波及 |

→ `Qlib-with-Claudex/qlib/utils/time.py` に直接影響。

---

## Layer 1: Qlib コア

### Option B で改修するファイル（データ基盤のみ）

| # | ファイル | 変更内容 | 影響度 |
|---|---------|---------|--------|
| 1 | `Qlib-with-Claudex/qlib/constant.py` | `REG_FX` リージョン追加 | 中 |
| 2 | `Qlib-with-Claudex/qlib/data/data.py` | `CalendarProvider` — 24h/5d 連続取引カレンダー + Session Cut 対応 | 高 |
| 3 | `Qlib-with-Claudex/qlib/data/data.py` | `InstrumentProvider` — 通貨ペアユニバース定義追加 | 高 |
| 4 | `Qlib-with-Claudex/qlib/config.py` | `qlib.init()` で FX リージョン・provider_uri 対応 | 中 |
| 5 | `Qlib-with-Claudex/qlib/utils/time.py` | DST 処理、Session Cut 基準時刻 | 中 |
| 6 | `Qlib-with-Claudex/qlib/contrib/data/handler.py` | **FX 専用 handler 新規追加**（Alpha158 は株式特徴量。放置すると株式ラベルで学習する事故が起きる） | **高** |
| 7 | `Qlib-with-Claudex/qlib/contrib/evaluate.py` | Annualization scaler 252→FX 用（パラメータ化） | 中 |
| 8 | `Qlib-with-Claudex/scripts/data_collector/` | FX データコレクター新規作成 | 高 |

### Option B で触らないファイル（Qlib backtest 系）

以下は改修せず、FX 専用 runner/backtester で代替する:

- `Qlib-with-Claudex/qlib/backtest/exchange.py` — 株式前提のまま放置
- `Qlib-with-Claudex/qlib/backtest/position.py` — 同上
- `Qlib-with-Claudex/qlib/backtest/report.py` — 同上
- `Qlib-with-Claudex/qlib/backtest/__init__.py` — 同上
- `Qlib-with-Claudex/qlib/workflow/record_temp.py` — 252日前提のまま（evaluate.py のパラメータ化で対応）

### 新規作成ファイル

| # | ファイル（案） | 内容 |
|---|---------------|------|
| N1 | `RD-Agent-with-Claudex/rdagent/scenarios/fx/` | FX シナリオディレクトリ（新規） |
| N2 | `RD-Agent-with-Claudex/rdagent/scenarios/fx/fx_runner.py` | FX 専用 backtester（スプレッドコスト、スワップ、レバレッジ対応） |
| N3 | `RD-Agent-with-Claudex/rdagent/scenarios/fx/fx_handler.py` | FX 特徴量 handler（bid/ask OHLC、スプレッド、tick volume）。注: Qlib 側 `contrib/data/handler.py` の FX handler は DataHandler 基底クラスを継承し Qlib Expression Engine 用。こちらは RD-Agent scenario 用のラッパーで、実験ワークスペースへのデータ供給を担当 |
| N4 | `Qlib-with-Claudex/scripts/data_collector/fx/` | FX データ収集スクリプト |

### データカラム設計

株式: `$open, $close, $high, $low, $volume, $factor`
FX（案）:

| カラム | 説明 |
|--------|------|
| `$bid_open, $bid_close, $bid_high, $bid_low` | Bid 側 OHLC |
| `$ask_open, $ask_close, $ask_high, $ask_low` | Ask 側 OHLC |
| `$mid_open, $mid_close, $mid_high, $mid_low` | Mid（計算用） |
| `$spread` | Ask - Bid（平均または Close 時点） |
| `$tick_volume` | Tick volume（注: 集中市場出来高ではない） |
| `$swap_long, $swap_short` | スワップポイント（日次） |

### Annualization Scaler

株式: 252 営業日/年（ハードコード箇所）
- `Qlib-with-Claudex/qlib/contrib/evaluate.py`
- `Qlib-with-Claudex/qlib/workflow/record_temp.py`
- `RD-Agent-with-Claudex/rdagent/scenarios/qlib/developer/factor_runner.py`

FX: 周期依存のためパラメータ化が必要
- 日足: 約 260 日
- 時間足: 24 × 260 = 6,240
- 分足: 60 × 24 × 260 = 374,400

---

## Layer 2: RD-Agent シナリオ設定

RD-Agent が Qlib を呼び出す部分。中国 A 株がハードコードされている。

| # | ファイル | 変更内容 | 影響度 |
|---|---------|---------|--------|
| 9 | `RD-Agent-with-Claudex/rdagent/scenarios/qlib/experiment/factor_template/conf_baseline.yaml` | `market: csi300` → FX ペアユニバース、`benchmark: SH000300` 撤廃、`limit_threshold: 0.095` 撤廃、コスト → スプレッド、`label` → FX リターン定義。**Alpha158 参照を FX handler に差替え** | 高 |
| 10 | 同 `conf_combined_factors.yaml`, `conf_combined_factors_sota_model.yaml` | 同上 | 高 |
| 11 | `RD-Agent-with-Claudex/rdagent/scenarios/qlib/experiment/factor_data_template/generate.py` | `provider_uri` → FX データ、`fields` → FX カラム、`freq` → マルチ周期対応 | 高 |
| 12 | `RD-Agent-with-Claudex/rdagent/scenarios/qlib/experiment/factor_data_template/README.md` | データ形式説明を FX 用に更新 | 低 |
| 13 | `RD-Agent-with-Claudex/rdagent/scenarios/qlib/experiment/utils.py` | `generate_data_folder_from_qlib()` の `daily_pv.h5` 前提を FX 対応に | 中 |
| 14 | `RD-Agent-with-Claudex/rdagent/scenarios/qlib/experiment/factor_experiment.py` | `QlibFactorScenario` — FX 用コンテキスト読み込みに切替 | 中 |
| 15 | `RD-Agent-with-Claudex/rdagent/scenarios/qlib/prompts.yaml` | 「China A-share market」→「FX market」、全プロンプトのドメイン用語書換え | 高 |
| 16 | `RD-Agent-with-Claudex/rdagent/scenarios/qlib/experiment/prompts.yaml` | **二重管理注意**: `factor_experiment.py` が実際に参照するのはこちら。同様に FX 用語に書換え | **高** |
| 17 | `RD-Agent-with-Claudex/rdagent/scenarios/qlib/developer/factor_runner.py` | IC 類似度の重複除去、DatasetH 切替、252 日 annualization | 中 |
| 18 | `RD-Agent-with-Claudex/rdagent/scenarios/qlib/developer/feedback.py` | 評価指標 `IC, excess_return, max_drawdown` → Sharpe, PnL, hit rate（IC は補助で残す） | 高 |
| 19 | `RD-Agent-with-Claudex/rdagent/app/qlib_rd_loop/conf.py` | train/valid/test 期間を FX データに合わせて変更 | 中 |

### 注意: prompts.yaml の二重管理

`rdagent/scenarios/qlib/prompts.yaml` と `rdagent/scenarios/qlib/experiment/prompts.yaml` の両方が存在し、`factor_experiment.py` が参照するのは後者。**片方だけ直すと挙動が揃わない**。

---

## Layer 3: サブエージェント定義 + Adapter 層

サブエージェント定義はプロンプトの設計意図を記述するドキュメント。実行時に参照されるのは YAML/template 側だが、設計変更はここを起点に行い、Adapter コードと YAML を追従させる。

### サブエージェント定義（設計起点 — 先に変更）

| # | ファイル | 変更内容 | 影響度 |
|---|---------|---------|--------|
| 20 | `docs/subagents/planner.md` | 利用可能カラム → FX カラム（bid/ask/spread/tick_volume）。「ファクター仮説」→「FX シグナル仮説」 | 高 |
| 21 | `docs/subagents/evaluator.md` | 判定基準「IC > SOTA IC かつ IC > 0.03」→ **Sharpe > SOTA Sharpe かつ Sharpe > 0.5**（案）。入力メトリクスも変更。IC は補助表示として残す | 高 |
| 22 | `docs/subagents/coder.md` | `source_data.h5` カラム前提を FX 向けに。tick volume の注意事項追記 | 中 |

### Adapter 実装コード（サブエージェント定義に追従）

| # | ファイル | 変更内容 | 影響度 |
|---|---------|---------|--------|
| 23 | `RD-Agent-with-Claudex/rdagent/adapters/factor/planner.py` | System prompt → 「quantitative FX researcher」 | 中 |
| 24 | `RD-Agent-with-Claudex/rdagent/adapters/factor/evaluator.py` | 判定基準 → Sharpe ベース、`"IC"` ハードコード除去（パラメータ化） | 高 |
| 25 | `RD-Agent-with-Claudex/rdagent/adapters/factor/trace_view.py` | `_build_observation()` のメトリクス抽出をパラメータ化（IC → primary_metric 設定で切替可能に） | 中 |
| 26 | `RD-Agent-with-Claudex/rdagent/adapters/factor/hypothesis_gen.py` | Stub 例 → FX 用例（carry, trend following, vol regime 等） | 低 |
| 27 | `RD-Agent-with-Claudex/rdagent/adapters/factor/coder.py` | コードテンプレート → FX シグナル例 | 低 |
| 28 | `RD-Agent-with-Claudex/rdagent/adapters/factor/h2e.py` | タスク例 → FX シグナル例 | 低 |
| 29 | `RD-Agent-with-Claudex/rdagent/adapters/factor/summarizer.py` | 観測例 → FX 評価用語 | 低 |

---

## Layer 4: スキル定義・設計ドキュメント・テスト

| # | ファイル | 変更内容 | 影響度 |
|---|---------|---------|--------|
| 30 | `docs/skills/qlib-hypothesis-gen.md` | 仮説カテゴリ → FX 用（Carry / Trend / Vol Regime / Macro / Cross-pair） | 中 |
| 31 | `docs/skills/qlib-factor-implement.md` | 入力カラム → FX、IC 閾値 → Sharpe 閾値、パターン例書換え | 中 |
| 32 | `docs/skills/qlib-experiment-eval.md` | Decision Criteria → FX 指標ベース（Sharpe 主判定 + IC 補助） | 中 |
| 33 | `docs/skills/qlib-rd-loop.md` | 「factor discovery」→「FX signal discovery」 | 低 |
| 34 | `RD-Agent-with-Claudex/test/adapters/test_planner_evaluator.py` | テストデータ → FX 例 | 低 |
| 35 | `RD-Agent-with-Claudex/test/adapters/test_adapters.py` | メトリクス → FX 指標 | 低 |
| 36 | `RD-Agent-with-Claudex/test/adapters/test_trace_view.py` | IC 前提のテスト → パラメータ化メトリクス対応 | 低 |
| 37 | `RD-Agent-with-Claudex/test/adapters/test_resume.py` | IC 前提の resume テスト → 同上 | 低 |
| 38 | `docs/plans/Adapter詳細設計.md` | テスト仕様の IC 例 | 低 |
| 39 | `docs/plans/ClaudeCode置換設計.md` | TraceView 例の IC 関連 | 低 |

---

## リスクと落とし穴

| # | リスク | 詳細 | 対策 |
|---|--------|------|------|
| R1 | **Alpha158 依存の見落とし** | 表面的に FX カラムへ変えても、内部で株式特徴量・ラベルで学習する事故 | FX 専用 handler を必ず作成し、Alpha158 参照を完全に差替え |
| R2 | **prompts.yaml 二重管理** | 2つの prompts.yaml のうち片方だけ直して挙動不一致 | 両ファイルを同時に更新。可能なら一本化 |
| R3 | **メトリクス schema 崩壊** | IC を消すと trace_view、resume、artifact 比較、feedback が連鎖的に壊れる | IC は補助指標として残しつつ、primary_metric をパラメータ化 |
| R4 | **年率換算のサイレント誤報** | 252 がハードコードされた箇所が複数。FX で使うと過小/過大評価 | evaluate.py + factor_runner.py をパラメータ化。record_temp.py は Option B で使用しないため放置 |
| R5 | **Option B の中途半端化** | 独自 backtester を作りつつ Qlib backtest も大改修すると保守負債が倍増 | 「触らないファイル」リストを厳守 |
| R6 | **Tick volume の誤用** | 株式の volume と同列に扱うと流動性特徴量が無意味に | Coder / skill 定義に tick volume の注意事項を明記 |

---

## run_result 最小 schema（案）

Phase FX-0 で確定する `run_result.json` の最小 schema。現行は IC 前提で密結合しているため、FX 用に再設計が必要。

```json
{
  "schema_version": "1.0.0",
  "status": "success",
  "primary_metric": {
    "name": "sharpe_ratio",
    "value": 1.23
  },
  "secondary_metrics": {
    "hit_rate": 0.54,
    "profit_factor": 1.8,
    "max_drawdown": -0.05,
    "ic": null,
    "annualized_return": 0.12
  },
  "meta": {
    "pairs": ["USDJPY", "EURUSD", "GBPUSD"],
    "period": "2020-01-01/2024-12-31",
    "frequency": "1h",
    "annualization_scaler": 6240,
    "cost_model": "spread"
  }
}
```

補足:
- `status`: `"success"` / `"failed"` / `"timeout"` のいずれか。失敗系の Resume/評価制御に必須
- `schema_version`: FX 導入時の互換性管理用。既存 artifact 設計の versioned schema に準拠
- `secondary_metrics.ic`: **null 許容**。Panel FX では数値、Single-pair TS では null

この schema を `feedback.py`、`trace_view.py`、`evaluator.py`、テスト群が共通参照する。

---

## 変更の優先順位（推奨実行順）

### Phase FX-0: 設計確定（コード変更なし）

1. 設計判断 6 項目を確定（取引モデル、評価指標、データソース、周期、Session Cut、Panel/Single-pair）
2. **データ契約・評価指標・run_result schema** を文書化（上記 schema 案を確定）
3. FX 専用 handler の特徴量リスト設計

### Phase FX-1: データ基盤 + Schema + 最小 Runner Stub

4. **FX scenario ディレクトリ作成**（新規 N1: `rdagent/scenarios/fx/`）— runner stub の置き場として先に作成
5. FX データコレクター新規作成（Layer 1 #8）
6. FX handler / loader 新規作成（Layer 1 #6）
7. CalendarProvider + Session Cut 対応（Layer 1 #2, #5）
8. Annualization scaler パラメータ化（Layer 1 #7）
9. **最小 FX runner stub** — run_result schema に準拠したダミー出力を返す stub を作成（新規 N2 の骨格）。FX-2/FX-3 の検証をダミーデータで回せるようにする

### Phase FX-2: シナリオ設定 + プロンプト + 評価系

9. prompts.yaml **両方** を FX 用語に書換え（Layer 2 #15, #16）
10. conf_baseline.yaml 系を FX 設定に（Layer 2 #9, #10）
11. feedback.py の評価指標変更（Layer 2 #18）— runner stub の出力で検証
12. factor_runner.py / conf.py 更新（Layer 2 #17, #19）

### Phase FX-3: サブエージェント + Adapter

13. docs/subagents/ の 3 ファイル書換え（Layer 3 #20〜22）
14. adapters/factor/ の実装コード追従（Layer 3 #23〜29）— runner stub + feedback.py で E2E 疎通確認

### Phase FX-4: スキル・テスト・ドキュメント

15. docs/skills/ 更新（Layer 4 #30〜33）
16. テストデータ FX 化（Layer 4 #34〜37）
17. 設計ドキュメント整合（Layer 4 #38〜39）

### Phase FX-5: 本番 Backtester

18. FX runner stub → 本番実装に昇格（スプレッドコスト、スワップ、レバレッジ対応）
19. FX scenario ディレクトリ拡張整備（N1 は FX-1 で作成済み。ここでは本番用モジュール群を追加）
20. E2E 統合テスト（実データ使用）

### 各 Phase の完了条件

| Phase | 完了条件 |
|-------|---------|
| FX-0 | 設計判断 6 項目 + run_result schema + 特徴量リストが文書化され、レビュー済み |
| FX-1 | FX データが HDF5 に格納され、`qlib.init(region="fx")` で読み込み可能。runner stub が schema 準拠の JSON を出力 |
| FX-2 | prompts/YAML が FX 用語に統一。feedback.py が runner stub 出力を正しくパース・評価 |
| FX-3 | subagent 定義と adapter コードが FX 対応。trace_view が primary_metric でソート表示 |
| FX-4 | 影響範囲の対象テスト green（`test/adapters/` 配下）。skill/ドキュメントが FX 用語に統一 |
| FX-5 | 実 FX データで RD ループ 1 周が完走。Sharpe/PnL/DD が正しく計算される |
