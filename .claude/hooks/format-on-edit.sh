#!/usr/bin/env bash
# PostToolUse hook: format the file Claude just edited so diffs stay clean.
# Never blocks: formatting problems surface later in `make lint`.
file=$(jq -r '.tool_input.file_path // empty')
[ -z "$file" ] || [ ! -f "$file" ] && exit 0

case "$file" in
  *.py)
    command -v ruff >/dev/null && ruff format --quiet "$file" && ruff check --fix --quiet "$file"
    ;;
  */frontend/src/*.ts|*/frontend/src/*.tsx|*/frontend/src/*.css|*/frontend/src/*.json)
    npx --no-install --prefix "$CLAUDE_PROJECT_DIR/frontend" prettier --write --log-level warn "$file"
    ;;
esac
exit 0
