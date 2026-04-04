#!/usr/bin/env python3
"""
standup-summary-today.py — One-shot watcher for 2026-04-03 standup.

Polls the transcription queue state until Recording 2026-04-03 08-14-38.mp3
is marked ok, reads the artifact, summarizes with Claude, and posts to
Binary Ranch Standup (tnft3avs).

Usage:
  python3 10-System/standup-summary-today.py
"""

import base64
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

VAULT_ROOT   = Path(__file__).parent.parent
ENV_FILE     = VAULT_ROOT / "config" / "nextcloud.env"
STATE_FILE   = Path(__file__).parent / ".transcription-queue-state.json"
TARGET_KEY   = "Recording 2026-04-03 08-14-38.mp3"   # partial match
BR_STANDUP   = "tnft3avs"
POLL_INTERVAL = 30


# ── Config ────────────────────────────────────────────────────────────────────

def load_env() -> dict:
    env = {}
    for line in ENV_FILE.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    return env


# ── Talk ─────────────────────────────────────────────────────────────────────

def send_talk_message(env: dict, room_token: str, message: str):
    url  = f"{env['NEXTCLOUD_URL']}/ocs/v2.php/apps/spreed/api/v1/chat/{room_token}"
    b64  = base64.b64encode(f"{env['NEXTCLOUD_USER']}:{env['NEXTCLOUD_APP_PASSWORD']}".encode()).decode()
    body = json.dumps({"message": message}).encode()
    req  = urllib.request.Request(
        url, data=body, method="POST",
        headers={"Authorization": f"Basic {b64}", "OCS-APIREQUEST": "true",
                 "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        print(f"[talk] Posted to {room_token}: HTTP {r.status}")


# ── Claude API ───────────────────────────────────────────────────────────────

def summarize(api_key: str, transcript: str) -> str:
    url  = "https://api.anthropic.com/v1/messages"
    body = json.dumps({
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 512,
        "messages": [{
            "role": "user",
            "content": (
                "You are summarizing a Binary Ranch standup meeting transcript. "
                "Write a concise standup summary in plain text (no markdown headers, "
                "no bullet symbols — just short paragraphs or a clean list). "
                "Cover: what was discussed, any decisions made, blockers, and next steps. "
                "Keep it under 300 words.\n\n"
                f"TRANSCRIPT:\n{transcript[:12000]}"
            ),
        }],
    }).encode()
    req = urllib.request.Request(
        url, data=body, method="POST",
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        resp = json.loads(r.read())
    return resp["content"][0]["text"].strip()


# ── State polling ─────────────────────────────────────────────────────────────

def find_completed_entry(state: dict):
    for key, val in state.get("processed", {}).items():
        if TARGET_KEY in key and val.get("status") == "ok":
            return val
    return None


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    env = load_env()
    api_key = env.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise SystemExit("ANTHROPIC_API_KEY not found in nextcloud.env")

    print(f"Watching for: {TARGET_KEY}")
    print(f"Polling every {POLL_INTERVAL}s …\n")

    while True:
        state = json.loads(STATE_FILE.read_text()) if STATE_FILE.exists() else {}
        entry = find_completed_entry(state)

        if entry:
            artifact_rel = entry.get("artifact", "")
            print(f"Transcription complete. Artifact: {artifact_rel}")

            artifact_path = VAULT_ROOT / artifact_rel
            if not artifact_path.exists():
                print(f"Artifact not synced yet, waiting… ({artifact_path})")
                time.sleep(POLL_INTERVAL)
                continue

            transcript = artifact_path.read_text(encoding="utf-8", errors="replace")
            # Strip frontmatter — content starts after second ---
            parts = transcript.split("---", 2)
            body = parts[2].strip() if len(parts) >= 3 else transcript

            print("Summarizing with Claude…")
            summary = summarize(api_key, body)
            print(f"\nSummary:\n{summary}\n")

            msg = f"Standup summary (2026-04-03)\n\n{summary}"
            send_talk_message(env, BR_STANDUP, msg)
            print("Done.")
            return

        print(f"[{time.strftime('%H:%M:%S')}] Still in progress, checking again in {POLL_INTERVAL}s…")
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
