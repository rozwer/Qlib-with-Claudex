#!/usr/bin/env bash
# Guard: Block inline Python (-c / heredoc) that imports qlib
# macOS defaults to spawn for multiprocessing, causing qlib to fail
# Must use script files with multiprocessing.set_start_method("fork", force=True)

set -euo pipefail

INPUT=$(cat)
CMD=$(echo "$INPUT" | jq -r '.tool_input.command // empty')
[[ -z "$CMD" ]] && exit 0

# Detect python -c with qlib import
if echo "$CMD" | grep -qE 'python3?\s+-c\s+.*import\s+(qlib|multiprocessing)'; then
  echo '{"decision":"block","reason":"macOS では python -c でのqlib/multiprocessing使用は禁止です。\nスクリプトファイルに保存して実行してください:\n  1. /tmp/script.py に保存\n  2. multiprocessing.set_start_method(\"fork\", force=True) を先頭に記述\n  3. python /tmp/script.py で実行"}'
  exit 0
fi

# Detect heredoc/stdin Python with qlib
if echo "$CMD" | grep -qE '(python3?\s*<<|cat.*\|\s*python3?)' && echo "$CMD" | grep -qE '(import\s+qlib|from\s+qlib)'; then
  echo '{"decision":"block","reason":"macOS では stdin/heredoc 経由のqlib実行は禁止です。\nスクリプトファイルに保存して実行してください:\n  1. /tmp/script.py に保存\n  2. multiprocessing.set_start_method(\"fork\", force=True) を先頭に記述\n  3. python /tmp/script.py で実行"}'
  exit 0
fi

exit 0
