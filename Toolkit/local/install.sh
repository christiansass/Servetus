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

# Write the thin shell launcher
cat > "$INSTALL_TARGET" <<LAUNCHER
#!/usr/bin/env bash
exec python3 "$ROUTER_DEST" "\$@"
LAUNCHER
chmod 755 "$INSTALL_TARGET"

echo -e "  router   → ${GREEN}$ROUTER_DEST${NC}"
echo -e "  launcher → ${GREEN}$INSTALL_TARGET${NC}"

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
# 6. Copy config templates if not already present
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
# Done
# ---------------------------------------------------------------------------
echo ""
echo -e "${GREEN}${BOLD}Installation complete.${NC}"
echo ""
echo "  Start a session : servetus"
echo "  One-off query   : servetus \"your question here\""
echo "  Route to Claude : servetus \"@claude your question\""
echo ""
echo -e "${DIM}Edit $CONFIG_DIR/pii_map.json to add PII entities to anonymize.${NC}"
echo -e "${DIM}Edit $CONFIG_DIR/router_config.json to change model or default route.${NC}"
echo ""
