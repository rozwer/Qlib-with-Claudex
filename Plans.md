# Qlib-with-Claudex — Project Plans

## 全体ゴール

Microsoft Qlib + RD-Agent の OpenAI 依存を Claude Code + Codex に完全置換し、
自律的なファクター R&D ループを実現する。

---

## Phase 1: 基盤構築 ✅ COMPLETE

OpenAI → Claude/LiteLLM 置換、Adapter 層構築、テスト整備。

- [x] **1A** Adapter 層実装（5 slot）+ 38 unit tests
- [x] **1B** Skills / Subagents 定義（6 skills, 3 subagents）
- [x] **1B** Codex CLI 統合（`codex exec --full-auto`）

## Phase 2: LLM バックエンド整理 ✅ COMPLETE

- [x] Claude をデフォルトバックエンドに設定
- [x] tiktoken / langchain 依存削除
- [x] deprec.py 削除
- [x] llm_conf.py 簡素化（134→72 行）

## Phase 3: インフラ・ドキュメント ✅ COMPLETE

- [x] Docker 対応
- [x] CLAUDE.md × 2（親リポ + 子リポ）
- [x] CI 設定
- [x] 5 skill 定義文書

## Phase 4: クリーンアップ 🔶 PARTIAL

- [x] base.py 修正
- [ ] **4-1** dump/load 削除（15+ files across 5 scenarios）
- [ ] **4-2** openai パッケージ直接参照の除去（litellm 依存は残す）

## Phase 5: R&D ループ実戦検証 🔶 IN PROGRESS

5 ラウンド実行済み。IC 閾値（0.03）未達だが、ワークフロー自体は動作確認済み。

- [x] **5-1** 環境構築（Qlib データ + venv + source_data.h5）
- [x] **5-2** 5 ラウンド実行（CSI300 Simple Data, 50 銘柄）
- [x] **5-3** データ品質検証システム追加（data_quality.json）
- [x] **5-4** IC 計算スクリプトの堅牢化（reset_index + merge + loop）
- [x] **5-5** 教訓のスキル・サブエージェント反映
  - groupby.transform() 強制
  - NaN カラム事前チェック
  - vwap フォールバック（typical price）
- [x] **5-6** Plan テンプレート導入（`.claude/templates/rdloop-plan.md`）
- [ ] **5-7** IC > 0.03 達成ファクターの探索（次回実行）
- [ ] **5-8** 全銘柄（714）での検証
- [ ] **5-9** バックテスト期間拡大（2005-2021）

## Phase 6: リポジトリ公開 ✅ COMPLETE

- [x] **6-1** 親リポ作成・push（rozwer/Qlib-with-Claudex）
- [x] **6-2** 子リポ作成・push（qlib-with-claudex-sub, RD-Agent-with-Claudex）
- [x] **6-3** README 作成（親 + 子 × 2）
- [x] **6-4** .gitignore 整備（runtime dirs, settings.local.json）
- [x] **6-5** 共有パーミッション設定（settings.json）

## Phase 7: FX 移行 📋 PLANNED

為替（FX）データへの対応拡張。

- [ ] **7-1** FX データソース選定・取得パイプライン
- [ ] **7-2** FX 向け scenario adapter
- [ ] **7-3** FX 固有ファクター仮説テンプレート
- [ ] **7-4** 実戦検証

> 詳細: `docs/plans/2026-03-08-fx-fork-design.md`

---

## 残課題サマリ

| 優先度 | タスク | Phase |
|--------|--------|-------|
| High | IC > 0.03 ファクター探索 | 5-7 |
| High | dump/load 削除 | 4-1 |
| Medium | 全銘柄検証 | 5-8 |
| Medium | openai 直接参照除去 | 4-2 |
| Low | FX 移行 | 7 |

## R&D ループ実行結果（参考）

| Round | Factor | IC | Decision |
|-------|--------|------|----------|
| 0 | volume_price_divergence_20d | 0.011 | rejected |
| 1 | volume_surprise_reversal_5d | 0.002 | rejected |
| 2 | volatility_contraction_ratio_5d20d | 0.001 | rejected |
| 3 | vwap_deviation_dual_momentum_10d40d | -0.014 | rejected |
| 4 | asymmetric_volume_gk_normalized_20d | 0.006 | rejected |
