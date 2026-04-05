#!/usr/bin/env python3
"""
Servetus Credential Rotation
Rotates the Nextcloud app password on a schedule.
Servetus generates its own replacement key, updates the env file, revokes the old one.

Run: python3 10-System/rotate-credentials.py
Scheduled: weekly via cron or Servetus scheduler
"""

import os
import re
import sys
import json
import requests
import logging
from datetime import datetime, timezone
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────
VAULT_ROOT   = Path(__file__).parent.parent
ENV_FILE     = VAULT_ROOT / "config" / "nextcloud.env"
LOG_FILE     = VAULT_ROOT / "10-System" / "credential-rotation.log"

# ── Logging ────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout),
    ]
)
log = logging.getLogger("rotate-credentials")

# ── Load env ───────────────────────────────────────────────────────────────
def load_env(path: Path) -> dict:
    env = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, val = line.partition("=")
                env[key.strip()] = val.strip()
    return env

def write_env(path: Path, env: dict, new_password: str):
    with open(path) as f:
        content = f.read()
    content = re.sub(
        r"^NEXTCLOUD_APP_PASSWORD=.*$",
        f"NEXTCLOUD_APP_PASSWORD={new_password}",
        content,
        flags=re.MULTILINE
    )
    with open(path, "w") as f:
        f.write(content)

# ── Nextcloud API ──────────────────────────────────────────────────────────
def nc_session(url: str, user: str, password: str) -> requests.Session:
    s = requests.Session()
    s.auth = (user, password)
    s.headers.update({
        "OCS-APIRequest": "true",
        "Accept": "application/json",
    })
    return s

def create_app_password(session: requests.Session, url: str, label: str) -> str:
    """Create a new app password and return it."""
    resp = session.post(
        f"{url}/ocs/v2.php/apps/user_apppassword/api/v1/token",
        data={"name": label},
    )
    resp.raise_for_status()
    data = resp.json()
    token = data.get("ocs", {}).get("data", {}).get("token")
    if not token:
        raise ValueError(f"No token in response: {data}")
    return token

def list_app_passwords(session: requests.Session, url: str) -> list:
    """List all app passwords for the current user."""
    resp = session.get(f"{url}/ocs/v2.php/apps/user_apppassword/api/v1/token")
    resp.raise_for_status()
    data = resp.json()
    return data.get("ocs", {}).get("data", {}).get("tokens", [])

def revoke_app_password(session: requests.Session, url: str, token_id: int):
    """Revoke an app password by its ID."""
    resp = session.delete(
        f"{url}/ocs/v2.php/apps/user_apppassword/api/v1/token/{token_id}"
    )
    resp.raise_for_status()

# ── Main ───────────────────────────────────────────────────────────────────
def main():
    log.info("=== Servetus credential rotation starting ===")

    # Load current credentials
    env = load_env(ENV_FILE)
    nc_url      = env.get("NEXTCLOUD_URL", "").rstrip("/")
    nc_user     = env.get("NEXTCLOUD_USER")
    nc_password = env.get("NEXTCLOUD_APP_PASSWORD")

    if not all([nc_url, nc_user, nc_password]):
        log.error("Missing NEXTCLOUD_URL, NEXTCLOUD_USER, or NEXTCLOUD_APP_PASSWORD in env")
        sys.exit(1)

    session = nc_session(nc_url, nc_user, nc_password)

    # Step 1 — List existing app passwords so we know what to revoke
    log.info("Fetching existing app passwords...")
    try:
        existing = list_app_passwords(session, nc_url)
        log.info(f"Found {len(existing)} existing app password(s)")
    except Exception as e:
        log.error(f"Failed to list app passwords: {e}")
        sys.exit(1)

    # Step 2 — Generate new app password
    ts    = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    label = f"servetus-auto-{ts}"
    log.info(f"Generating new app password: {label}")
    try:
        new_password = create_app_password(session, nc_url, label)
        log.info("New app password generated successfully")
    except Exception as e:
        log.error(f"Failed to generate new app password: {e}")
        sys.exit(1)

    # Step 3 — Write new password to env file BEFORE revoking old one
    log.info("Writing new password to env file...")
    try:
        write_env(ENV_FILE, env, new_password)
        log.info("Env file updated")
    except Exception as e:
        log.error(f"Failed to update env file: {e}")
        log.error("New password was generated but NOT written — manual intervention required")
        log.error(f"New password label: {label} — revoke old passwords manually via Nextcloud UI")
        sys.exit(1)

    # Step 4 — Switch session to new password
    session = nc_session(nc_url, nc_user, new_password)

    # Step 5 — Revoke old app passwords (everything except the one we just created)
    revoked = 0
    for token in existing:
        token_id   = token.get("id")
        token_name = token.get("name", "")
        try:
            revoke_app_password(session, nc_url, token_id)
            log.info(f"Revoked old app password: [{token_id}] {token_name}")
            revoked += 1
        except Exception as e:
            log.warning(f"Failed to revoke [{token_id}] {token_name}: {e}")

    log.info(f"Revoked {revoked} old app password(s)")
    log.info("=== Rotation complete ===")

    # Step 6 — Post confirmation to Christian's 1:1 (self room)
    try:
        confirm_msg = (
            f"🔑 Credential rotation complete — {ts}\n"
            f"New app password active: `{label}`\n"
            f"Old passwords revoked: {revoked}\n"
            f"Next rotation: in 7 days"
        )
        resp = session.post(
            f"{nc_url}/ocs/v2.php/apps/spreed/api/v1/chat/cufo8jwd",
            data={"message": confirm_msg, "replyTo": 0},
        )
        if resp.status_code in (200, 201):
            log.info("Confirmation posted to Christian 1:1")
        else:
            log.warning(f"Could not post confirmation to Talk: {resp.status_code}")
    except Exception as e:
        log.warning(f"Confirmation post failed: {e}")

if __name__ == "__main__":
    main()
