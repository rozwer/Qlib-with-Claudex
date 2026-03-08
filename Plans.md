# Qlib-with-Claudex — Project Plans

## Goal

Replace OpenAI dependencies in Microsoft Qlib + RD-Agent with Claude Code + Codex,
enabling autonomous factor R&D loops.

---

## Phase 1: Foundation ✅ COMPLETE

OpenAI → Claude/LiteLLM replacement, Adapter layer, tests.

- [x] **1A** Adapter layer (5 slots) + 38 unit tests
- [x] **1B** Skills / Subagents definitions (6 skills, 3 subagents)
- [x] **1B** Codex CLI integration (`codex exec --full-auto`)

## Phase 2: LLM Backend Cleanup ✅ COMPLETE

- [x] Set Claude as default backend
- [x] Remove tiktoken / langchain dependencies
- [x] Delete deprec.py
- [x] Simplify llm_conf.py (134→72 lines)

## Phase 3: Infrastructure & Documentation ✅ COMPLETE

- [x] Docker support
- [x] CLAUDE.md × 2 (parent + child repos)
- [x] CI configuration
- [x] 5 skill definition documents

## Phase 4: Cleanup 🔶 PARTIAL

- [x] base.py fix
- [ ] **4-1** Remove dump/load (15+ files across 5 scenarios)
- [ ] **4-2** Remove direct openai package references (litellm dependency stays)

## Phase 5: R&D Loop Validation 🔶 IN PROGRESS

5 rounds executed. IC threshold (0.03) not met, but workflow confirmed working.

- [x] **5-1** Environment setup (Qlib data + venv + source_data.h5)
- [x] **5-2** Execute 5 rounds (CSI300 Simple Data, 50 instruments)
- [x] **5-3** Add data quality validation system (data_quality.json)
- [x] **5-4** Harden IC calculation script (reset_index + merge + loop)
- [x] **5-5** Reflect lessons in skills/subagents
  - Enforce groupby.transform()
  - Pre-check NaN columns
  - vwap fallback (typical price)
- [x] **5-6** Introduce plan template (`.claude/templates/rdloop-plan.md`)
- [ ] **5-7** Find factor with IC > 0.03 (next run)
- [ ] **5-8** Validate with all instruments (714)
- [ ] **5-9** Extend backtest period (2005-2021)

## Phase 6: Repository Publication ✅ COMPLETE

- [x] **6-1** Create & push parent repo (rozwer/Qlib-with-Claudex)
- [x] **6-2** Create & push child repos (qlib-with-claudex-sub, RD-Agent-with-Claudex)
- [x] **6-3** Create READMEs (parent + 2 children)
- [x] **6-4** Configure .gitignore (runtime dirs, settings.local.json)
- [x] **6-5** Shared permissions (settings.json)

## Phase 7: FX Migration 📋 PLANNED

Extend to FX (foreign exchange) data.

- [ ] **7-1** FX data source selection & acquisition pipeline
- [ ] **7-2** FX scenario adapter
- [ ] **7-3** FX-specific factor hypothesis templates
- [ ] **7-4** Validation

> Details: `docs/plans/2026-03-08-fx-fork-design.md`

---

## Open Issues

| Priority | Task | Phase |
|----------|------|-------|
| High | Find factor with IC > 0.03 | 5-7 |
| High | Remove dump/load | 4-1 |
| Medium | Full instrument validation | 5-8 |
| Medium | Remove direct openai references | 4-2 |
| Low | FX migration | 7 |

## R&D Loop Results (Reference)

| Round | Factor | IC | Decision |
|-------|--------|------|----------|
| 0 | volume_price_divergence_20d | 0.011 | rejected |
| 1 | volume_surprise_reversal_5d | 0.002 | rejected |
| 2 | volatility_contraction_ratio_5d20d | 0.001 | rejected |
| 3 | vwap_deviation_dual_momentum_10d40d | -0.014 | rejected |
| 4 | asymmetric_volume_gk_normalized_20d | 0.006 | rejected |
