#!/usr/bin/env bash
# Runs ruff on any Python file Claude just wrote or edited.
# If ruff fails, injects the errors back so Claude auto-fixes before moving on.

FILE=$(jq -r '.tool_input.file_path // empty')

# Only act on Python files
[[ "$FILE" == *.py ]] && [ -n "$FILE" ] || exit 0

OUTPUT=$(uv run ruff check "$FILE" 2>&1)
[ $? -eq 0 ] && exit 0

jq -n --arg ctx "Ruff check failed on $FILE — fix these issues before continuing:\n\n$OUTPUT" \
  '{"hookSpecificOutput":{"hookEventName":"PostToolUse","additionalContext":$ctx}}'
