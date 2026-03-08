#!/usr/bin/env bash
# Guard: Protect source_data.h5 from accidental deletion or overwrite
# source_data.h5 is the input market data — regeneration is expensive

set -euo pipefail

INPUT=$(cat)
CMD=$(echo "$INPUT" | jq -r '.tool_input.command // empty')
[[ -z "$CMD" ]] && exit 0

# Block rm of source_data.h5
if echo "$CMD" | grep -qE 'rm\s+.*source_data\.h5'; then
  echo '{"decision":"block","reason":"source_data.h5 の削除は禁止です。\nこのファイルは Qlib から生成された市場データで、再生成にはコストがかかります。\n本当に削除が必要な場合は、手動で実行してください。"}'
  exit 0
fi

# Block overwriting source_data.h5 with cp/mv (but allow to_hdf which creates it)
if echo "$CMD" | grep -qE '(cp|mv)\s+.*\s+.*source_data\.h5'; then
  echo '{"decision":"block","reason":"source_data.h5 の上書きは禁止です。\nこのファイルは Qlib から生成された市場データです。\n新しいデータが必要な場合は prepare_source_data.py を使用してください。"}'
  exit 0
fi

exit 0
