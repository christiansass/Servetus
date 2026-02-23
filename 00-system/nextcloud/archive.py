"""
Session archival — files ephemeral conversations to the Sovereign tier.

Takes a session transcript (from Claude, or any ephemeral source),
formats it as a Servetus daily log, and uploads to Nextcloud via WebDAV.

This makes ephemeral collaboration repeatable:
1. Work with Claude (transient tier)
2. Archive the session to Nextcloud (sovereign tier)
3. Next session, pull context from the archive
"""

from datetime import datetime
from pathlib import Path
from typing import Optional

from .config import load_config, VAULT_ROOT
from .webdav import WebDAVClient


def build_session_log(
    content: str,
    session_id: str = "",
    source: str = "claude-code",
    tags: Optional[list] = None,
) -> str:
    """
    Format a session transcript as a Servetus daily log entry.

    Follows the frontmatter schema from Toolkit/S00.01-02-00.
    """
    now = datetime.now()
    date_iso = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M")
    pretty = now.strftime("%B %d, %Y")

    if tags is None:
        tags = ["session-log", "ephemeral-archive"]

    tag_str = ", ".join(tags)

    return f"""---
type: daily-log
date: {date_iso}
title: "Session Archive — {pretty} {time_str}"
source: {source}
session_id: "{session_id}"
status: draft
trust_tier: sovereign
tags: [{tag_str}]
---

# Session Archive — {pretty} {time_str}

## Source
- **Platform:** {source}
- **Session ID:** {session_id}
- **Archived at:** {date_iso} {time_str}
- **Trust tier:** Sovereign (Nextcloud only)

## Transcript

{content.strip()}
""".rstrip() + "\n"


def archive_session(
    content: str,
    session_id: str = "",
    source: str = "claude-code",
    upload: bool = True,
) -> Path:
    """
    Archive a session to the vault and optionally upload to Nextcloud.

    1. Writes the session log to 02-daily-logs/ (local vault)
    2. Uploads to Nextcloud via WebDAV (Sovereign tier)

    Returns the local path of the archived file.
    """
    now = datetime.now()
    filename = now.strftime("%Y-%m-%d") + f"--session-{source}--{now.strftime('%H%M')}.md"
    log_dir = VAULT_ROOT / "02-daily-logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    log_content = build_session_log(
        content=content,
        session_id=session_id,
        source=source,
    )

    log_path = log_dir / filename
    log_path.write_text(log_content, encoding="utf-8")
    print(f"  Session archived locally: {log_path}")

    if upload:
        config = load_config()
        if config is None:
            print("  Nextcloud not configured — local archive only.")
            print("  To enable: copy 00-system/nextcloud/nextcloud.yaml.example → config/nextcloud.yaml")
            return log_path

        client = WebDAVClient(config)
        if client.test_connection():
            if client.upload(log_path):
                print(f"  Uploaded to Nextcloud: {config.remote_root}/02-daily-logs/{filename}")
            else:
                print("  Upload failed — file saved locally only.")
        else:
            print("  Nextcloud unreachable — file saved locally only.")

    return log_path
