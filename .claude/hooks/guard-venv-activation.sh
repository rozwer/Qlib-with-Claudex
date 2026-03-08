#!/usr/bin/env bash
# Guard: Ensure RD-Agent venv is activated when running python/pytest
# in RD-Agent-with-Claudex directory or artifact directories

set -euo pipefail

INPUT=$(cat)
CMD=$(echo "$INPUT" | jq -r '.tool_input.command // empty')
[[ -z "$CMD" ]] && exit 0

# Check if command runs python/pytest in RD-Agent or artifact context
# but does NOT activate the venv first
needs_venv=false

# Pattern: cd to RD-Agent dir + python/pytest without source .venv/bin/activate
if echo "$CMD" | grep -qE 'RD-Agent-with-Claudex' && echo "$CMD" | grep -qE '(python3?|pytest)\s' && ! echo "$CMD" | grep -qE 'source\s+.*\.venv/bin/activate'; then
  needs_venv=true
fi

# Pattern: running factor.py or calc_ic.py without venv activation
if echo "$CMD" | grep -qE '(python3?)\s+.*(factor\.py|calc_ic\.py)' && ! echo "$CMD" | grep -qE 'source\s+.*\.venv/bin/activate'; then
  needs_venv=true
fi

# Exception: python -c with simple imports (no qlib needed)
if echo "$CMD" | grep -qE 'python3?\s+-c\s+"import\s+(json|os|sys|pathlib)'; then
  needs_venv=false
fi

# Exception: py_compile (syntax check only, no runtime deps)
if echo "$CMD" | grep -qE 'py_compile'; then
  needs_venv=false
fi

if [[ "$needs_venv" == "true" ]]; then
  echo '{"decision":"block","reason":"RD-Agent の venv が有効化されていません。\n以下のように venv を有効化してから実行してください:\n  cd RD-Agent-with-Claudex && source .venv/bin/activate && python ...\n\nまたは:\n  source /Users/roz/Desktop/Qlib/RD-Agent-with-Claudex/.venv/bin/activate && python ..."}'
  exit 0
fi

exit 0
