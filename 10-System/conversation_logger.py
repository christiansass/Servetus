#!/usr/bin/env python3
"""
conversation_logger.py — Append Talk messages to daily room log files.

Writes to: 02-Memories/YYYY-MM-DD-talk-<room-slug>-log.md
One file per room per day. Thread-safe. Append-only after creation.

Called from talk-webhook.py after each incoming message and each bot reply.
"""

import re
import threading
from datetime import datetime
from pathlib import Path

VAULT_ROOT   = Path(__file__).parent.parent
MEMORIES_DIR = VAULT_ROOT / "02-Memories"

# Per-file locks so concurrent rooms don't interleave writes
_file_locks: dict = {}
_locks_lock = threading.Lock()

MONTH_NAMES = {
    1: "January", 2: "February", 3: "March", 4: "April",
    5: "May", 6: "June", 7: "July", 8: "August",
    9: "September", 10: "October", 11: "November", 12: "December",
}


def _get_lock(path: Path) -> threading.Lock:
    with _locks_lock:
        if path not in _file_locks:
            _file_locks[path] = threading.Lock()
        return _file_locks[path]


def _slugify(text: str, max_len: int = 40) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text[:max_len]


def _log_path(room_name: str, dt: datetime) -> Path:
    today = dt.strftime("%Y-%m-%d")
    slug  = _slugify(room_name)
    return MEMORIES_DIR / f"{today}-talk-{slug}-log.md"


def _build_frontmatter(room_name: str, room_token: str, dt: datetime) -> str:
    today = dt.strftime("%Y-%m-%d")
    ts    = dt.strftime("%Y-%m-%dT%H:%M:00-05:00")
    slug  = f"{today}-talk-{_slugify(room_name)}-log"
    rid   = f"SV-{today.replace('-', '')}-NOW-CST-LOG"
    room_slug = _slugify(room_name)

    return (
        "---\n"
        "servitus:\n"
        "  schema_version: 2\n"
        "  system_version: 0.2.1\n"
        "  record_type: daily_log\n"
        "  pipeline_stage: distilled\n"
        "  status: active\n"
        "  intent: capture\n"
        "\n"
        "identity:\n"
        f'  title: "{room_name} \u2014 Talk Log \u2014 {today}"\n'
        f'  slug: "{slug}"\n'
        f'  record_id: "{rid}"\n'
        "\n"
        "time:\n"
        f'  created_at: "{ts}"\n'
        '  timezone: "America/Chicago"\n'
        '  source_range: "today"\n'
        "\n"
        "source:\n"
        f'  room_token: "{room_token}"\n'
        f'  room_name: "{room_name}"\n'
        "  surface: talk\n"
        "\n"
        "tags:\n"
        "  - servetus\n"
        "  - log\n"
        "  - talk\n"
        f"  - {room_slug}\n"
        "---\n"
        "\n"
        f"# {room_name} \u2014 Talk Log \u2014 {today}\n"
        "\n"
    )


def log_message(
    room_token: str,
    room_name: str,
    actor_id: str,
    actor_display: str,
    message: str,
    dt: datetime = None,
    attachment_name: str = None,
    is_bot: bool = False,
) -> None:
    """
    Append a single message entry to the daily room log.

    room_token    — NC Talk room token (e.g. "9mvw5kaq")
    room_name     — Human-readable room name (e.g. "Jim Coler")
    actor_id      — NC username of sender
    actor_display — Display name of sender
    message       — Message text (plain string)
    dt            — Timestamp; defaults to now
    attachment_name — Filename if a file was shared; adds an attachment line
    is_bot        — True when logging a Servetus reply
    """
    if dt is None:
        dt = datetime.now()

    MEMORIES_DIR.mkdir(parents=True, exist_ok=True)
    path = _log_path(room_name, dt)
    lock = _get_lock(path)

    time_str = dt.strftime("%H:%M")

    if is_bot:
        header = f"**{time_str}** \u00b7 Servetus"
    else:
        header = f"**{time_str}** \u00b7 {actor_display} (`{actor_id}`)"

    # Build the message block
    block = f"\n---\n\n{header}\n{message}"
    if attachment_name:
        block += f"\n\n*\ud83d\udcce {attachment_name}*"
    block += "\n"

    with lock:
        if not path.exists():
            path.write_text(_build_frontmatter(room_name, room_token, dt) + block)
            print(f"[log] Created: {path.name}")
        else:
            with path.open("a", encoding="utf-8") as f:
                f.write(block)
