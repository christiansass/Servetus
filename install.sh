#!/usr/bin/env bash
# =============================================================================
# Servetus One-Line Installer
# =============================================================================
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/christiansass/Servetus/main/install.sh | bash
#
# Or clone first:
#   git clone https://github.com/christiansass/Servetus.git
#   bash Servetus/install.sh
# =============================================================================

set -e

REPO="https://github.com/christiansass/Servetus.git"

echo ""
echo "  ╔═══════════════════════════════╗"
echo "  ║      SERVETUS  INSTALLER      ║"
echo "  ╚═══════════════════════════════╝"
echo ""

# ---------------------------------------------------------------------------
# Prerequisites
# ---------------------------------------------------------------------------
for cmd in python3 git; do
    command -v "$cmd" >/dev/null 2>&1 || {
        echo "Error: '$cmd' is required but not found. Install it and re-run."
        exit 1
    }
done

# ---------------------------------------------------------------------------
# Obsidian root
# ---------------------------------------------------------------------------
echo "Path to your Obsidian root folder (e.g. ~/Nextcloud/Obsidian):"
read -r OBSIDIAN_ROOT
OBSIDIAN_ROOT="${OBSIDIAN_ROOT/#\~/$HOME}"

if [[ ! -d "$OBSIDIAN_ROOT" ]]; then
    echo "Error: Directory not found: $OBSIDIAN_ROOT"
    exit 1
fi

VAULT_PATH="$OBSIDIAN_ROOT/Servetus"

# ---------------------------------------------------------------------------
# Clone or update vault
# ---------------------------------------------------------------------------
if [[ -d "$VAULT_PATH/.git" ]]; then
    echo ""
    echo "Updating existing Servetus vault at $VAULT_PATH..."
    git -C "$VAULT_PATH" pull
else
    echo ""
    echo "Cloning Servetus into $VAULT_PATH..."
    git clone "$REPO" "$VAULT_PATH"
fi

# ---------------------------------------------------------------------------
# Ensure sibling Inbox/Claude/ exists
# ---------------------------------------------------------------------------
mkdir -p "$OBSIDIAN_ROOT/Inbox/Claude"
echo "Inbox ready: $OBSIDIAN_ROOT/Inbox/Claude"

# ---------------------------------------------------------------------------
# Run the detailed installer
# ---------------------------------------------------------------------------
echo ""
bash "$VAULT_PATH/Toolkit/local/install.sh"
