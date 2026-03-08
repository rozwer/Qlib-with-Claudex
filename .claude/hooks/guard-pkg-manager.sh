#!/usr/bin/env bash
# Guard: pip/npm/yarn/npx/pnpm -> uv/bun/mise
# PreToolUse hook for Bash tool — reads tool input from stdin JSON

set -euo pipefail

INPUT=$(cat)
TOOL=$(echo "$INPUT" | jq -r '.tool_name // empty')

# Only check Bash commands
[[ "$TOOL" != "Bash" ]] && exit 0

CMD=$(echo "$INPUT" | jq -r '.tool_input.command // empty')
[[ -z "$CMD" ]] && exit 0

# Extract the first token of each piped/chained command
# Matches: pip, pip3, python -m pip, npm, npx, yarn, pnpm
check_command() {
  local cmd="$1"

  # pip / pip3 / python -m pip
  if echo "$cmd" | grep -qE '(^|[;&|]\s*)(pip3?|python3?\s+-m\s+pip)\s+(install|uninstall|freeze|download)'; then
    echo '{"decision":"block","reason":"pip は使用禁止です。代わりに uv を使ってください:\n  uv add <package>        # 依存追加\n  uv pip install <pkg>    # 直接インストール\n  uv sync                 # lockfile から同期"}'
    exit 0
  fi

  # npm
  if echo "$cmd" | grep -qE '(^|[;&|]\s*)npm\s+(install|i|ci|uninstall|remove|rm|update|run|exec|init|create)'; then
    echo '{"decision":"block","reason":"npm は使用禁止です。代わりに bun を使ってください:\n  bun add <package>       # 依存追加\n  bun install             # lockfile から同期\n  bun run <script>        # スクリプト実行\n  bunx <cmd>              # npx 相当"}'
    exit 0
  fi

  # yarn
  if echo "$cmd" | grep -qE '(^|[;&|]\s*)yarn(\s+(add|remove|install|run|exec|create)|\s*$)'; then
    echo '{"decision":"block","reason":"yarn は使用禁止です。代わりに bun を使ってください:\n  bun add <package>       # 依存追加\n  bun install             # lockfile から同期\n  bun run <script>        # スクリプト実行"}'
    exit 0
  fi

  # pnpm
  if echo "$cmd" | grep -qE '(^|[;&|]\s*)pnpm\s+(add|install|i|remove|rm|run|exec|create)'; then
    echo '{"decision":"block","reason":"pnpm は使用禁止です。代わりに bun を使ってください:\n  bun add <package>       # 依存追加\n  bun install             # lockfile から同期\n  bun run <script>        # スクリプト実行"}'
    exit 0
  fi

  # npx
  if echo "$cmd" | grep -qE '(^|[;&|]\s*)npx\s+'; then
    echo '{"decision":"block","reason":"npx は使用禁止です。代わりに bunx を使ってください:\n  bunx <command>          # npx 相当"}'
    exit 0
  fi

  # gem install (bonus: mise manages ruby)
  if echo "$cmd" | grep -qE '(^|[;&|]\s*)gem\s+install'; then
    echo '{"decision":"block","reason":"gem install は使用禁止です。mise でランタイム管理してください:\n  mise use ruby@<ver>     # Ruby バージョン管理\n  mise exec -- gem install <pkg>"}'
    exit 0
  fi
}

check_command "$CMD"

# If no match, allow (exit silently)
exit 0
