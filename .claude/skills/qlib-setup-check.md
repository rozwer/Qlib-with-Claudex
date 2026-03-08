---
name: qlib-setup-check
description: Verify that all prerequisites for running the Qlib R&D loop are met. Use when starting a new session or before running the loop.
---

# Qlib R&D Loop Setup Verification

Verify the environment, data, and tools required before running the R&D loop.

## Checklist

Run the following checks sequentially via Bash and display the results.

### 1. Python Virtual Environment

```bash
cd RD-Agent-with-Claudex && source .venv/bin/activate
python --version  # Python 3.12 required
```

**On failure**: `uv venv .venv --python 3.12 && uv pip install -e .`

### 2. Qlib Installation

```bash
python -c "import qlib; print(f'qlib {qlib.__version__}')"
```

**On failure**: `uv pip install -e ../Qlib-with-Claudex/`

### 3. Qlib Data

```bash
ls ~/.qlib/qlib_data/cn_data/calendars/day.txt && \
  echo "Data exists" && \
  head -1 ~/.qlib/qlib_data/cn_data/calendars/day.txt && \
  tail -1 ~/.qlib/qlib_data/cn_data/calendars/day.txt
```

**On failure**:
```bash
cd Qlib-with-Claudex/scripts
python get_data.py qlib_data --name qlib_data_simple \
  --target_dir ~/.qlib/qlib_data/cn_data --region cn
```

### 4. Key Python Packages

```bash
python -c "
import pandas, numpy, tables
print(f'pandas {pandas.__version__}')
print(f'numpy {numpy.__version__}')
print(f'pytables {tables.__version__}')
"
```

**On failure**: `uv pip install tables`

### 5. Codex CLI (optional — subagent fallback available)

```bash
which codex && codex --version
```

**On failure**: Not critical. The R&D loop will use a Claude subagent for code generation instead.
To install: `bun install -g @anthropic-ai/codex` or `npm install -g @anthropic-ai/codex`

### 6. Adapter Tests

```bash
cd RD-Agent-with-Claudex && pytest test/adapters/ -v --tb=short 2>&1 | tail -5
```

**On failure**: Review test error output and fix

## Output Format

Display results for each check in the following table:

```
| # | Check Item | Status | Details |
|---|------------|--------|---------|
| 1 | Python venv | OK | 3.12.x |
| 2 | Qlib | OK | 0.9.8.dev27 |
| 3 | Qlib data | OK | 2005-01-04 to 2021-06-11 |
| 4 | pytables | OK | 3.x.x |
| 5 | Codex CLI | OK / FALLBACK | 0.97.0 or "subagent mode" |
| 6 | Adapter tests | OK | 38 passed, 1 skipped |
```

If all checks pass, display "R&D loop is ready to run."
If any check fails, provide remediation steps.
