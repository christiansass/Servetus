#!/usr/bin/env python3
"""
Servetus User Picker
--------------------
Reads 08-Witnesses/ for files where cli_access.granted: true.
Displays the Servetus splash screen + an interactive numbered list on /dev/tty.
Outputs the selected username (actor_id, lowercased) to stdout.

The keyring is entirely manual — no account is on the list unless
csass explicitly set cli_access.granted: true in their witness file.

Usage (called by ~/bin/servetus):
    USERNAME=$(python3 10-System/user-picker.py /path/to/vault)
"""

import re
import sys
from pathlib import Path


# ── ANSI palette — Tron / grid aesthetic ─────────────────────────────────────

RESET    = "\033[0m"
BOLD     = "\033[1m"
DIM      = "\033[2m"

# Electric cyan — primary neon
CYAN     = "\033[38;5;51m"
# Slightly cooler cyan for text
CYAN2    = "\033[38;5;45m"
# Deep grid blue — structural lines
GRID     = "\033[38;5;27m"
# Bright white — user names
WHITE    = "\033[97m"
# Soft amber — subtle accent on prompt
AMBER    = "\033[38;5;220m"


# ── ASCII logo ────────────────────────────────────────────────────────────────

LOGO = (
    "  ███████ ███████ ██████  ██   ██ ███████ ████████ ██    ██ ███████\n"
    "  ██      ██      ██   ██ ██   ██ ██         ██    ██    ██ ██     \n"
    "  ███████ █████   ██████   ██ ██  █████      ██    ██    ██ ███████\n"
    "       ██ ██      ██  ██   ██ ██  ██         ██    ██    ██      ██\n"
    "  ███████ ███████ ██   ██   ███   ███████    ██     ██████  ███████\n"
)

TAGLINE   = "  reality · sovereignty · truth"
GRID_LINE = "  " + "╌" * 65


# ── Frontmatter parser ────────────────────────────────────────────────────────

def parse_frontmatter(text: str) -> dict:
    """Extract key-value pairs from YAML frontmatter without a YAML library."""
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    fm = text[3:end]

    result = {}

    # title — top-level or nested under identity:
    m = re.search(r'^title:\s*["\']?(.+?)["\']?\s*$', fm, re.M)
    if not m:
        m = re.search(r'^\s+title:\s*["\']?(.+?)["\']?\s*$', fm, re.M)
    if m:
        result["title"] = m.group(1).strip().strip("\"'")

    # trust_tier (flat or under servitus:)
    m = re.search(r'^trust_tier:\s*["\']?(\S+)["\']?', fm, re.M)
    if m:
        result["trust_tier"] = m.group(1).strip().strip("\"'")

    # subject.actor_id  (indented under subject:)
    m = re.search(r'^\s+actor_id:\s*["\']?(\S+)["\']?', fm, re.M)
    if m:
        result["actor_id"] = m.group(1).strip().strip("\"'")

    # talk_id (flat field — fallback username source)
    m = re.search(r'^talk_id:\s*["\']?(\S+)["\']?', fm, re.M)
    if m:
        result["talk_id"] = m.group(1).strip().strip("\"'")

    # nc_account (explicit override — takes priority)
    m = re.search(r'^nc_account:\s*["\']?(\S+)["\']?', fm, re.M)
    if m:
        result["nc_account"] = m.group(1).strip().strip("\"'")

    # cli_access.granted
    cli_block = re.search(r'^cli_access:\s*\n((?:[ \t]+.+\n?)*)', fm, re.M)
    if cli_block:
        block = cli_block.group(1)
        m = re.search(r'granted:\s*(true|false)', block, re.I)
        if m:
            result["cli_granted"] = m.group(1).lower() == "true"
        m = re.search(r'granted_date:\s*["\']?(.+?)["\']?\s*$', block, re.M)
        if m:
            result["cli_granted_date"] = m.group(1).strip().strip("\"'")
    # Also handle single-line: cli_access: true
    elif re.search(r'^cli_access:\s*true', fm, re.M | re.I):
        result["cli_granted"] = True

    return result


def resolve_username(fm: dict) -> str:
    """Return the best available username for this witness record."""
    # Priority: explicit nc_account > subject.actor_id > talk_id
    for key in ("nc_account", "actor_id", "talk_id"):
        if fm.get(key):
            return fm[key].lower()
    return ""


# ── Load keyring from witness files ───────────────────────────────────────────

def load_keyring(vault: Path) -> list:
    """Scan 08-Witnesses/ and return records where cli_access.granted is true."""
    witnesses_dir = vault / "08-Witnesses"
    if not witnesses_dir.exists():
        return []

    users = []
    for path in sorted(witnesses_dir.glob("*.md")):
        if path.name.startswith("_"):
            continue
        try:
            text = path.read_text(errors="replace")
        except Exception:
            continue

        fm = parse_frontmatter(text)
        if not fm.get("cli_granted"):
            continue

        username = resolve_username(fm)
        title = fm.get("title", path.stem)
        trust = fm.get("trust_tier", "")
        granted_date = fm.get("cli_granted_date", "")

        if not username:
            continue  # no usable username — skip

        users.append({
            "username":     username,
            "name":         title,
            "trust_tier":   trust,
            "granted_date": granted_date,
            "witness":      path.name,
        })

    # self tier first, then alphabetical by name
    users.sort(key=lambda u: (0 if u["trust_tier"] == "self" else 1, u["name"]))
    return users


# ── Splash + picker ───────────────────────────────────────────────────────────

def show_splash(tty, users: list):
    """Write logo, tagline, and user list to tty."""
    tty.write("\n")
    tty.write(f"{CYAN}{BOLD}{LOGO}{RESET}")
    tty.write(f"{CYAN2}{DIM}{TAGLINE}{RESET}\n")
    tty.write(f"{GRID}{GRID_LINE}{RESET}\n")
    tty.write("\n")

    if len(users) == 1:
        u = users[0]
        tty.write(
            f"  {CYAN2}session for{RESET}  "
            f"{BOLD}{WHITE}{u['name']}{RESET}  "
            f"{DIM}({u['username']}){RESET}\n\n"
        )
        return

    tty.write(f"  {BOLD}{WHITE}WHO IS USING SERVETUS?{RESET}\n\n")
    for i, u in enumerate(users, 1):
        tier = f"  {CYAN2}{DIM}[{u['trust_tier']}]{RESET}" if u["trust_tier"] else ""
        tty.write(
            f"  {GRID}{i}.{RESET}  "
            f"{BOLD}{WHITE}{u['name']}{RESET}  "
            f"{CYAN2}{DIM}({u['username']}){RESET}"
            f"{tier}\n"
        )
    tty.write(f"\n  {AMBER}›{RESET} ")


def pick_user(users: list, default_username: str = "") -> str:
    """
    Display splash + numbered list to /dev/tty, return selected username to stdout.
    Default (Enter) = first user (self tier).
    """
    if not users:
        return default_username or "csass"

    try:
        tty_out = open("/dev/tty", "w")
        tty_in  = open("/dev/tty", "r")
    except (OSError, IOError):
        return users[0]["username"]

    show_splash(tty_out, users)
    tty_out.flush()

    if len(users) == 1:
        tty_out.close()
        tty_in.close()
        return users[0]["username"]

    try:
        raw = tty_in.readline().strip()
    except Exception:
        raw = ""

    tty_out.write("\n")
    tty_out.flush()
    tty_out.close()
    tty_in.close()

    if not raw:
        return users[0]["username"]

    if raw.isdigit():
        idx = int(raw) - 1
        if 0 <= idx < len(users):
            return users[idx]["username"]

    # Typed a username directly
    for u in users:
        if u["username"] == raw.lower():
            return u["username"]

    return users[0]["username"]


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    vault = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent
    users = load_keyring(vault)

    if not users:
        # Keyring empty — fall back silently so the session still opens
        print("csass")
        return

    selected = pick_user(users)
    print(selected)


if __name__ == "__main__":
    main()
