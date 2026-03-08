# Coder Subagent (Codex CLI)

Responsible for generating factor implementation code in the Factor RD loop.
Invokes **Codex CLI** via the Bash tool.

## Role

Generates a Qlib-compatible factor.py based on the factor specification in experiment.json.

## Invocation Method

```bash
codex exec --full-auto -C <workspace_path> \
  "Generate <workspace_path>/factor.py based on the following factor specification.

   Specification:
   $(cat <artifact_dir>/round_<N>/experiment.json)

   Implementation rules:
   - Read from source_data.h5 using pd.read_hdf (key='data')
   - columns: open, close, high, low, volume, vwap / MultiIndex: (instrument, datetime) order
   - Write to result.h5 with key='data' (Series, name is factor_name)
   - Use groupby(level='instrument').transform() for per-instrument calculations (apply is prohibited as it causes index corruption)
   - No look-ahead bias (use only shift, rolling)
   - Handle NaN/inf with replace([np.inf, -np.inf], np.nan)
   - The output Series index must exactly match the input DataFrame index
   - Check notna().sum() > 0 before using any column in case it is entirely NaN"
```

## CLI Options

| Option | Value | Description |
|--------|-------|-------------|
| `exec` | - | Non-interactive mode |
| `--full-auto` | - | No approval required + workspace-write sandbox |
| `-C` | workspace path | Working directory (write-enabled) |

## Input

- **experiment.json**: Factor specification (factor_name, formulation, variables)
- The contents of experiment.json are inlined into the prompt

## Output Files

- `round_<N>/implementations/factor.py` — Executable factor computation code

## Notes

- Codex uses its own Python environment (Python 3.14, no tables/pytables)
- **Execution** of factor.py must be done in the RD-Agent venv (`cd RD-Agent-with-Claudex && source .venv/bin/activate`)
- In `--full-auto` mode, Codex autonomously runs `py_compile` and dummy data tests to detect bugs
- Codex reads existing files to learn patterns, so previous rounds' factor.py files serve as references

## Issues Discovered in Practice and Countermeasures

| Issue | Countermeasure |
|-------|----------------|
| `groupby.apply()` corrupts index, resulting in all NaN | Use `groupby.transform()` instead |
| MultiIndex order is (instrument, datetime) | Use `groupby(level=0)` or `groupby(level="instrument")` consistently |
| Column (e.g., vwap) is entirely NaN | Check `notna().sum() > 0` before use. Fall back to alternative calculations (e.g., typical price) |
| tables not installed in Codex environment | Syntax verification only via `py_compile`. Real data verification is done in the venv |

## Implementation Guidelines

Follow `.claude/skills/qlib-factor-implement.md`. Key points:

- Read from `source_data.h5`, write to `result.h5`
- Handle MultiIndex (datetime, instrument) correctly
- Avoid look-ahead bias (`.shift(N)` with N > 0, `.rolling()` only)
- Handle NaN / inf appropriately
- Must be valid Python syntax
