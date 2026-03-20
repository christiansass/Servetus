#!/usr/bin/env bash
# Servetus Pre-Commit Security Check
# Blocks commits containing device fingerprint data in staged files.
# Install: ln -sf ../../10-System/pre-commit-check.sh .git/hooks/pre-commit

set -euo pipefail

FAIL=0

# Patterns that indicate real device fingerprint data
# Format: "pattern" "description"
declare -a PATTERNS=(
  # MAC address: xx:xx:xx:xx:xx:xx (not the placeholder aa:bb:cc:dd:ee:ff)
  "[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}"
  # Private IPs with specific host octets (not .x placeholders)
  "10\.[0-9]+\.[0-9]+\.[1-9][0-9]*"
  "192\.168\.[0-9]+\.[1-9][0-9]*"
  "172\.(1[6-9]|2[0-9]|3[0-1])\.[0-9]+\.[1-9][0-9]*"
  # /Users/<name>/ paths (macOS home dirs with real usernames)
  "/Users/[a-zA-Z][a-zA-Z0-9_-]+/"
)

PLACEHOLDER_EXCEPTIONS=(
  "aa:bb:cc:dd:ee:ff"   # approved MAC placeholder
  "/Users/username/"    # approved path placeholder
)

# Only check staged files (not the full working tree)
STAGED=$(git diff --cached --name-only --diff-filter=ACM 2>/dev/null || true)

if [[ -z "$STAGED" ]]; then
  exit 0
fi

for FILE in $STAGED; do
  # Skip binary files and gitkeep
  [[ "$FILE" == *.gitkeep ]] && continue
  [[ "$FILE" == *.png || "$FILE" == *.jpg || "$FILE" == *.jpeg || "$FILE" == *.gif ]] && continue
  [[ "$FILE" == *.zip || "$FILE" == *.mp3 || "$FILE" == *.mp4 ]] && continue
  # Skip the pre-commit script itself and the security spec (they contain the patterns as examples)
  [[ "$FILE" == "10-System/pre-commit-check.sh" ]] && continue
  [[ "$FILE" == "Toolkit/security-scrub-protocol.md" ]] && continue

  for PATTERN in "${PATTERNS[@]}"; do
    MATCHES=$(git diff --cached -- "$FILE" | grep "^+" | grep -v "^+++" | grep -E "$PATTERN" || true)
    if [[ -n "$MATCHES" ]]; then
      # Check against known safe placeholders
      SAFE=0
      for EXCEPTION in "${PLACEHOLDER_EXCEPTIONS[@]}"; do
        if echo "$MATCHES" | grep -q "$EXCEPTION"; then
          SAFE=1
          break
        fi
      done
      if [[ $SAFE -eq 0 ]]; then
        echo ""
        echo "  SECURITY BLOCK — device fingerprint data detected"
        echo "  File:    $FILE"
        echo "  Pattern: $PATTERN"
        echo "  Line(s):"
        echo "$MATCHES" | sed 's/^/    /'
        echo ""
        echo "  Scrub before committing. See Toolkit/security-scrub-protocol.md"
        echo ""
        FAIL=1
      fi
    fi
  done
done

if [[ $FAIL -ne 0 ]]; then
  echo "  Commit blocked. Fix the above and try again."
  exit 1
fi

exit 0
