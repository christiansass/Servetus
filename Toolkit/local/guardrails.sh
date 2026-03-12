#!/usr/bin/env bash
# =============================================================================
# Servetus Guardrails Hook — Hard Stops Only
# =============================================================================
# Claude Code PreToolUse hook on Bash tool calls.
#
# This script enforces Rule 3 (CLAUDE.md): operations with no recovery path.
# It does NOT replace the behavioral protocol in Rules 1 and 2 — those require
# Claude to propose and explain before acting, which is a conversational rule.
#
# Exit 0  → allow
# Exit 2  → block (stdout message shown to user before the call is rejected)
#
# Receives JSON on stdin: { "tool_name": "Bash", "tool_input": { "command": "..." } }
# =============================================================================

set -euo pipefail

INPUT=$(cat)

COMMAND=$(python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get('tool_input', {}).get('command', ''))
except Exception:
    print('')
" <<< "$INPUT" 2>/dev/null || echo "")

[[ -z "$COMMAND" ]] && exit 0

block() {
    echo "HARD STOP [Servetus guardrails]: $1"
    echo ""
    echo "  Command : $COMMAND"
    echo ""
    echo "This operation is not executable by Claude. Run it manually if intended."
    exit 2
}

# History rewriting — no recovery once pushed
if echo "$COMMAND" | grep -qE 'git (filter-branch|filter-repo)'; then
    block "git history rewriting is a manual-only operation."
fi

exit 0
