#!/usr/bin/env bash
# =============================================================================
# Servetus Local Installer
# =============================================================================
# Deploys the Servetus AI router to ~/bin/servetus on this machine.
#
# What it does:
#   1. Confirms you're running Servetus with Nextcloud (required for WebDAV/CalDAV)
#   2. Finds your Nextcloud root
#   3. Confirms the Servetus vault path within it
#   4. Writes a configured router to ~/bin/servetus
#   5. Ensures ~/bin is on your PATH
#
# Usage:
#   bash install.sh
# =============================================================================

set -e

BOLD='\033[1m'
DIM='\033[2m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

SERVETUS_SUBPATH="Obsidian/Servetus"
INSTALL_DIR="$HOME/bin"
INSTALL_TARGET="$INSTALL_DIR/servetus"

echo ""
echo -e "${BOLD}Servetus Local Installer${NC}"
echo "──────────────────────────────────────────"
echo ""

# ---------------------------------------------------------------------------
# 1. Nextcloud check
# ---------------------------------------------------------------------------
echo -e "${BOLD}Are you running Servetus with Nextcloud?${NC} [Y/n]"
echo -e "${DIM}(Nextcloud is required for WebDAV and CalDAV features)${NC}"
read -r nc_answer
nc_answer="${nc_answer:-Y}"

if [[ "$nc_answer" =~ ^[Nn] ]]; then
    echo ""
    echo -e "${YELLOW}Note: Without Nextcloud, WebDAV and CalDAV features will not be available."
    echo -e "Router and local logging will still work.${NC}"
    echo ""
    echo "Enter the full path to your Servetus vault:"
    read -r VAULT_ROOT
    VAULT_ROOT="${VAULT_ROOT/#\~/$HOME}"
    if [[ ! -d "$VAULT_ROOT" ]]; then
        echo -e "${RED}Error: Directory not found: $VAULT_ROOT${NC}"
        exit 1
    fi
else
    # ---------------------------------------------------------------------------
    # 2. Find Nextcloud root
    # ---------------------------------------------------------------------------
    echo ""
    echo -e "${BOLD}Finding Nextcloud...${NC}"
    echo ""

    # Standard Nextcloud sync locations (Linux + macOS)
    CANDIDATES=()

    # Check common locations (Linux + macOS)
    for candidate in \
        "$HOME/Nextcloud" \
        "$HOME/Documents/Nextcloud" \
        "$HOME/Cloud" \
        "$HOME/Library/CloudStorage/Nextcloud-Nextcloud" \
        "$HOME/Library/CloudStorage/Nextcloud" \
        "/mnt/Cloud/Nextcloud" \
        "/mnt/cloud/Nextcloud" \
        "/media/$USER/Cloud/Nextcloud"
    do
        if [[ -d "$candidate" ]]; then
            CANDIDATES+=("$candidate")
        fi
    done

    # Also search /mnt/* for any folder named Nextcloud (Linux)
    while IFS= read -r -d '' found; do
        # Avoid duplicates
        already=false
        for c in "${CANDIDATES[@]}"; do
            [[ "$c" == "$found" ]] && already=true && break
        done
        $already || CANDIDATES+=("$found")
    done < <(find /mnt -maxdepth 3 -type d -name "Nextcloud" -print0 2>/dev/null)

    NC_ROOT=""

    if [[ ${#CANDIDATES[@]} -eq 0 ]]; then
        echo -e "${YELLOW}Could not find Nextcloud automatically.${NC}"
    elif [[ ${#CANDIDATES[@]} -eq 1 ]]; then
        echo -e "Found: ${GREEN}${CANDIDATES[0]}${NC}"
        echo -e "Use this? [Y/n]"
        read -r confirm
        confirm="${confirm:-Y}"
        if [[ "$confirm" =~ ^[Yy] ]]; then
            NC_ROOT="${CANDIDATES[0]}"
        fi
    else
        echo "Found multiple Nextcloud locations:"
        for i in "${!CANDIDATES[@]}"; do
            echo "  $((i+1))) ${CANDIDATES[$i]}"
        done
        echo ""
        echo "Enter number (or 0 to enter manually):"
        read -r choice
        if [[ "$choice" =~ ^[1-9][0-9]*$ ]] && (( choice <= ${#CANDIDATES[@]} )); then
            NC_ROOT="${CANDIDATES[$((choice-1))]}"
        fi
    fi

    if [[ -z "$NC_ROOT" ]]; then
        echo "Enter the full path to your Nextcloud folder:"
        read -r NC_ROOT
        NC_ROOT="${NC_ROOT/#\~/$HOME}"
        if [[ ! -d "$NC_ROOT" ]]; then
            echo -e "${RED}Error: Directory not found: $NC_ROOT${NC}"
            exit 1
        fi
    fi

    # ---------------------------------------------------------------------------
    # 3. Confirm Servetus sub-path within Nextcloud
    # ---------------------------------------------------------------------------
    echo ""
    DEFAULT_VAULT="$NC_ROOT/$SERVETUS_SUBPATH"
    echo -e "Servetus vault path: ${GREEN}$DEFAULT_VAULT${NC}"
    echo "Is this correct? [Y/n] (or enter a different sub-path within Nextcloud)"
    read -r vault_confirm
    vault_confirm="${vault_confirm:-Y}"

    if [[ "$vault_confirm" =~ ^[Yy] ]]; then
        VAULT_ROOT="$DEFAULT_VAULT"
    elif [[ "$vault_confirm" =~ ^[Nn] ]]; then
        echo "Enter the sub-path within $NC_ROOT (e.g. Notes/Servetus):"
        read -r subpath
        VAULT_ROOT="$NC_ROOT/$subpath"
    else
        # They typed a path directly
        VAULT_ROOT="$NC_ROOT/$vault_confirm"
    fi

    if [[ ! -d "$VAULT_ROOT" ]]; then
        echo -e "${RED}Error: Vault directory not found: $VAULT_ROOT${NC}"
        exit 1
    fi
fi

echo ""
echo -e "Vault confirmed: ${GREEN}$VAULT_ROOT${NC}"

# ---------------------------------------------------------------------------
# 4. Deploy router
# ---------------------------------------------------------------------------
echo ""
echo -e "${BOLD}Deploying router...${NC}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROUTER_SRC="$SCRIPT_DIR/router.py"

if [[ ! -f "$ROUTER_SRC" ]]; then
    echo -e "${RED}Error: router.py not found at $ROUTER_SRC${NC}"
    exit 1
fi

mkdir -p "$INSTALL_DIR"

# Write the launcher script (shell wrapper that calls the installed router.py)
ROUTER_DEST="$INSTALL_DIR/servetus_router.py"

# Substitute __VAULT_ROOT__ token with the real path
sed "s|__VAULT_ROOT__|$VAULT_ROOT|g" "$ROUTER_SRC" > "$ROUTER_DEST"
chmod 755 "$ROUTER_DEST"

# Write the thin shell launcher (Ollama router)
cat > "$INSTALL_TARGET" <<LAUNCHER
#!/usr/bin/env bash
exec python3 "$ROUTER_DEST" "\$@"
LAUNCHER
chmod 755 "$INSTALL_TARGET"

# Write the Claude Code launcher — shows launch brief, runs claude, captures session on exit
SC_TARGET="$INSTALL_DIR/sc"
cat > "$SC_TARGET" <<SCLAUNCHER
#!/usr/bin/env bash
# Servetus Claude — context picker, launch brief, Claude Code, session capture
#
# Usage:
#   sc                     — interactive room picker
#   sc "T-Mobile Arc"      — skip picker, set room directly
#   sc "Dev" --resume xyz  — room label + claude args
cd "$VAULT_ROOT" || exit 1

RESUME_ID=""

# If a room arg was passed explicitly (non-flag), use it and skip the menu.
# Otherwise, launch the interactive context picker.
if [[ -n "\$1" && "\${1:0:2}" != "--" ]]; then
    export SERVETUS_ROOM="\$1"
    shift
else
    # launch-menu.py writes display to /dev/tty, outputs two lines to stdout:
    #   line 1: room label (may be empty)
    #   line 2: resume session ID (may be empty)
    MENU_OUTPUT=\$(python3 "$VAULT_ROOT/10-System/launch-menu.py" "$VAULT_ROOT")
    export SERVETUS_ROOM=\$(printf '%s' "\$MENU_OUTPUT" | head -1)
    RESUME_ID=\$(printf '%s' "\$MENU_OUTPUT" | sed -n '2p')
fi

# Show gauge cluster + write ~/.servetus_session.json (includes room)
python3 "$VAULT_ROOT/10-System/launch-brief.py" "$VAULT_ROOT"

# Start inbox watcher in background — announces new files as they arrive
python3 "$VAULT_ROOT/10-System/inbox-watcher.py" &
WATCHER_PID=\$!
trap "kill \$WATCHER_PID 2>/dev/null" EXIT INT TERM

# Launch Claude Code — resume prior session if one was selected
if [[ -n "\$RESUME_ID" ]]; then
    claude --resume "\$RESUME_ID" "\$@"
else
    claude "\$@"
fi

# Stop watcher
kill "\$WATCHER_PID" 2>/dev/null
wait "\$WATCHER_PID" 2>/dev/null

# Capture artifact (session-close reads SERVETUS_ROOM from env)
echo ""
echo "[servetus] Session ended. Capturing artifact..."
python3 "$VAULT_ROOT/10-System/session-close.py"

# Clear session state
rm -f "\$HOME/.servetus_session.json"
SCLAUNCHER
chmod 755 "$SC_TARGET"

# Also install servetus-claude as a named alias for sc (keeps sc for backwards compat)
SC_NAMED_TARGET="$INSTALL_DIR/servetus-claude"
ln -sf "$SC_TARGET" "$SC_NAMED_TARGET" 2>/dev/null || cp "$SC_TARGET" "$SC_NAMED_TARGET"
chmod 755 "$SC_NAMED_TARGET"

echo -e "  router          → ${GREEN}$ROUTER_DEST${NC}"
echo -e "  launcher        → ${GREEN}$INSTALL_TARGET${NC}"
echo -e "  claude (sc)     → ${GREEN}$SC_TARGET${NC}  (auto-captures session on exit)"
echo -e "  claude (named)  → ${GREEN}$SC_NAMED_TARGET${NC}  (same as sc)"

# ---------------------------------------------------------------------------
# 5. Ensure ~/bin is on PATH
# ---------------------------------------------------------------------------
echo ""
SHELL_RC=""
OS_TYPE="$(uname -s)"

if [[ "$OS_TYPE" == "Darwin" ]]; then
    # macOS: Terminal.app and iTerm2 open login shells — use .zprofile
    # .zshrc is not sourced by login shells on macOS
    case "$SHELL" in
        */zsh)  SHELL_RC="$HOME/.zprofile" ;;
        */bash) SHELL_RC="$HOME/.bash_profile" ;;
        *)      SHELL_RC="$HOME/.profile" ;;
    esac
else
    # Linux / WSL: terminals open interactive (non-login) shells — use .zshrc / .bashrc
    case "$SHELL" in
        */zsh)  SHELL_RC="$HOME/.zshrc" ;;
        */bash) SHELL_RC="$HOME/.bashrc" ;;
        *)      SHELL_RC="$HOME/.profile" ;;
    esac
fi

if echo "$PATH" | grep -q "$INSTALL_DIR"; then
    echo -e "~/bin is already on PATH."
else
    echo -e "${YELLOW}~/bin is not on your PATH.${NC}"
    echo "Add it to $SHELL_RC? [Y/n]"
    read -r path_confirm
    path_confirm="${path_confirm:-Y}"
    if [[ "$path_confirm" =~ ^[Yy] ]]; then
        echo "" >> "$SHELL_RC"
        echo '# Servetus local tools' >> "$SHELL_RC"
        echo 'export PATH="$HOME/bin:$PATH"' >> "$SHELL_RC"
        echo -e "  Added to ${GREEN}$SHELL_RC${NC}"
        echo -e "  ${DIM}Run: source $SHELL_RC  (or open a new terminal)${NC}"
    else
        echo -e "  ${YELLOW}Skipped. Add ~/bin to PATH manually to use 'servetus' command.${NC}"
    fi
fi

# ---------------------------------------------------------------------------
# 6. Install Servetus statusline for Claude Code
# ---------------------------------------------------------------------------
echo ""
echo -e "${BOLD}Setting up Servetus statusline...${NC}"

STATUSLINE_SRC="$VAULT_ROOT/10-System/statusline.sh"
STATUSLINE_DEST="$HOME/.claude/statusline.sh"

if [[ -f "$STATUSLINE_SRC" ]]; then
    cp "$STATUSLINE_SRC" "$STATUSLINE_DEST"
    chmod +x "$STATUSLINE_DEST"

    # Write statusLine into ~/.claude/settings.json (statusLine object format required)
    CLAUDE_SETTINGS="$HOME/.claude/settings.json"
    python3 - <<PYEOF
import json, pathlib
p = pathlib.Path("$CLAUDE_SETTINGS")
try:
    s = json.loads(p.read_text()) if p.exists() and p.stat().st_size > 2 else {}
except Exception:
    s = {}
s.pop("statusCommand", None)  # remove deprecated key if present
s["statusLine"] = {"type": "command", "command": "$STATUSLINE_DEST"}
p.parent.mkdir(parents=True, exist_ok=True)
p.write_text(json.dumps(s, indent=2) + "\n")
PYEOF

    echo -e "  statusline → ${GREEN}$STATUSLINE_DEST${NC}"
    echo -e "  settings   → ${GREEN}$CLAUDE_SETTINGS${NC}  (statusLine set)"
else
    echo -e "  ${YELLOW}statusline.sh not found at $STATUSLINE_SRC — skipping${NC}"
fi

# ---------------------------------------------------------------------------
# 8. Copy config templates if not already present
# ---------------------------------------------------------------------------
CONFIG_DIR="$VAULT_ROOT/config"
mkdir -p "$CONFIG_DIR"

for tpl in pii_map.json router_config.json; do
    SRC="$SCRIPT_DIR/$tpl"
    DEST="$CONFIG_DIR/$tpl"
    if [[ -f "$SRC" && ! -f "$DEST" ]]; then
        cp "$SRC" "$DEST"
        echo -e "  config   → ${GREEN}$DEST${NC}"
    fi
done

# ---------------------------------------------------------------------------
# 9. Deploy guardrails hook
# ---------------------------------------------------------------------------
echo ""
echo -e "${BOLD}Deploying guardrails hook...${NC}"

CLAUDE_DIR="$VAULT_ROOT/.claude"
SETTINGS_FILE="$CLAUDE_DIR/settings.local.json"
GUARDRAILS_SCRIPT="$VAULT_ROOT/Toolkit/local/guardrails.sh"

mkdir -p "$CLAUDE_DIR"

# Write settings.local.json with correct vault-absolute path
cat > "$SETTINGS_FILE" <<SETTINGS
{
  "permissions": {
    "allow": [
      "Bash(python3:*)",
      "Bash(zip:*)"
    ]
  },
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "bash $GUARDRAILS_SCRIPT"
          }
        ]
      }
    ]
  }
}
SETTINGS

chmod 644 "$SETTINGS_FILE"
echo -e "  guardrails → ${GREEN}$SETTINGS_FILE${NC}"
echo -e "  script     → ${GREEN}$GUARDRAILS_SCRIPT${NC}"

# ---------------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------------
echo ""
echo -e "${GREEN}${BOLD}Installation complete.${NC}"
echo ""
echo "  Ollama router   : servetus"
echo "  One-off query   : servetus \"your question here\""
echo "  Route to Claude : servetus \"@claude your question\""
echo "  Claude Code     : sc   (launches Claude + auto-captures session on exit)"
echo ""
echo -e "${DIM}Edit $CONFIG_DIR/pii_map.json to add PII entities to anonymize.${NC}"
echo -e "${DIM}Edit $CONFIG_DIR/router_config.json to change model or default route.${NC}"
echo ""
