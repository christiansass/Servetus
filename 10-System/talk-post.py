#!/usr/bin/env python3
"""
talk-post.py — One-shot Talk room poster.

Usage:
    python3 10-System/talk-post.py --room <token> --file <message_file>
    python3 10-System/talk-post.py --room tnft3avs --file 10-System/standup-draft.md

Reads credentials from config/nextcloud.env.
Requires NEXTCLOUD_URL, NEXTCLOUD_USER, NEXTCLOUD_APP_PASSWORD.
"""

import argparse
import base64
import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path

VAULT_ROOT = Path(__file__).parent.parent
ENV_PATH   = VAULT_ROOT / "config" / "nextcloud.env"


def load_env(path: Path) -> dict:
    env = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            env[k.strip()] = v.strip()
    return env


def make_headers(user: str, password: str) -> dict:
    b64 = base64.b64encode(f"{user}:{password}".encode()).decode()
    return {"Authorization": f"Basic {b64}", "OCS-APIREQUEST": "true"}


def post_message(base_url: str, headers: dict, room_token: str, message: str) -> dict:
    data = urllib.parse.urlencode({"message": message}).encode()
    req  = urllib.request.Request(
        f"{base_url}/ocs/v2.php/apps/spreed/api/v1/chat/{room_token}?format=json",
        data=data,
        headers={**headers, "Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())


def main():
    parser = argparse.ArgumentParser(description="Post a message to a Nextcloud Talk room.")
    parser.add_argument("--room", required=True, help="Talk room token")
    parser.add_argument("--file", required=True, help="Path to message file (plain text / markdown)")
    args = parser.parse_args()

    if not ENV_PATH.exists():
        print(f"ERROR: env file not found at {ENV_PATH}", file=sys.stderr)
        sys.exit(1)

    env = load_env(ENV_PATH)

    # Per-node secrets (e.g. NEXTCLOUD_APP_PASSWORD) are intentionally NOT stored
    # in the vault env file — that file is synced across all nodes. Each node sets
    # its own credential via the system environment (~/.zshenv, systemd EnvironmentFile,
    # etc.). System env takes precedence; vault env provides the shared non-secret keys.
    for key in ("NEXTCLOUD_URL", "NEXTCLOUD_USER", "NEXTCLOUD_APP_PASSWORD"):
        if key in os.environ:
            env[key] = os.environ[key]
        elif key not in env:
            print(f"ERROR: {key} missing — set it in ~/.zshenv or your node's EnvironmentFile", file=sys.stderr)
            sys.exit(1)

    message_path = Path(args.file)
    if not message_path.is_absolute():
        message_path = VAULT_ROOT / message_path
    if not message_path.exists():
        print(f"ERROR: message file not found: {message_path}", file=sys.stderr)
        sys.exit(1)

    message = message_path.read_text().strip()
    if not message:
        print("ERROR: message file is empty", file=sys.stderr)
        sys.exit(1)

    headers = make_headers(env["NEXTCLOUD_USER"], env["NEXTCLOUD_APP_PASSWORD"])
    result  = post_message(env["NEXTCLOUD_URL"], headers, args.room, message)

    status = result.get("ocs", {}).get("meta", {}).get("statuscode", "?")
    print(f"Posted to room {args.room} — status {status}")
    if status not in (200, 201):
        print(json.dumps(result, indent=2))
        sys.exit(1)

    # Self-unload the LaunchAgent so it doesn't repeat tomorrow.
    plist = Path.home() / "Library/LaunchAgents/com.servetus.standup-post.plist"
    if plist.exists():
        os.system(f"launchctl unload {plist}")
        plist.unlink()
        print("LaunchAgent unloaded and removed.")


if __name__ == "__main__":
    main()
