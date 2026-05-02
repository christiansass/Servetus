#!/usr/bin/env python3
"""
talk-listener.py — Notification-driven Nextcloud Talk monitor for Servetus.

Single polling loop. No room map. No per-room threads.

The rooms API returns every room Servetus is in, with unread counts and last
message IDs. That is the notification signal. Rooms with unread content get
fetched and processed. New rooms are discovered automatically — any room
Servetus is added to shows up in the next poll cycle.

Triggers on:
  - Any message in a 1-on-1 (onetoone) room
  - @Servetus mention in group/public rooms
  - respond_all flag set in room_overrides (config/talk-rooms.json)
  - Emoji reactions on Servetus messages

Usage:
    python3 10-System/talk-listener.py           # run continuously
    python3 10-System/talk-listener.py --once    # single pass, then exit

config/nextcloud.env must contain:
    NEXTCLOUD_URL=https://your.server
    NEXTCLOUD_USER=servetus
    NEXTCLOUD_APP_PASSWORD=your-app-password
    ANTHROPIC_API_KEY=sk-ant-...
"""

import json
import re
import base64
import time
import sys
import subprocess
import threading
import urllib.request
import urllib.error
import urllib.parse
from pathlib import Path
from datetime import datetime
import anthropic

VAULT_ROOT     = Path(__file__).parent.parent
ENV_FILE       = VAULT_ROOT / "config" / "nextcloud.env"
OVERRIDES_FILE = VAULT_ROOT / "config" / "talk-rooms.json"   # manual per-room overrides only
WITNESSES_DIR  = VAULT_ROOT / "08-Witnesses"

POLL_INTERVAL         = 5      # seconds between room-list polls
RETRY_DELAY           = 10     # seconds after a poll error before retrying
REACTION_POLL_INTERVAL = 15    # seconds between reaction sweeps
MY_ACTOR              = "servetus"
THREAD_HISTORY        = 12
CLAUDE_MODEL          = "claude-sonnet-4-6"
CLASSIFIER_MODEL      = "claude-haiku-4-5-20251001"
MAX_MESSAGE_CHARS     = 3000

# cursor: token -> last processed message ID
# Kept in memory; seeded from the rooms API on first sight of a room.
_cursor: dict[str, int] = {}
_cursor_lock = threading.Lock()

# Dedup: (token, msg_id) -> True for messages we've already handled this run
_handled: set = set()
_handled_lock = threading.Lock()

# Content-based dedup: (token, actor_id, text_hash) -> timestamp
CONTENT_DEDUP_WINDOW = 10
_content_dedup: dict = {}
_content_dedup_lock = threading.Lock()

# Reaction tracking: token -> list of our message IDs
_our_msg_ids: dict[str, list] = {}
_our_msg_ids_lock = threading.Lock()

# Reacted set: "token:msg_id:emoji:actor" -> True
_reacted: set = set()
_reacted_lock = threading.Lock()

# Talk state cache (injected into system prompt)
_talk_state_cache: str = ""
_talk_state_ts: float = 0.0
_talk_state_lock = threading.Lock()
TALK_STATE_TTL = 60


# ── Helpers ────────────────────────────────────────────────────────────────────

def load_env() -> dict:
    env = {}
    with open(ENV_FILE) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env


def make_headers(user: str, password: str) -> dict:
    b64 = base64.b64encode(f"{user}:{password}".encode()).decode()
    return {"Authorization": f"Basic {b64}", "OCS-APIREQUEST": "true"}


def load_overrides() -> dict:
    """Load manual per-room overrides (respond_all, arc, notes) from talk-rooms.json."""
    if not OVERRIDES_FILE.exists():
        return {}
    with open(OVERRIDES_FILE) as f:
        return json.load(f)


def _is_content_duplicate(token: str, actor_id: str, text: str) -> bool:
    import hashlib
    key = (token, actor_id, hashlib.md5(text.encode()).hexdigest())
    now = time.time()
    with _content_dedup_lock:
        stale = [k for k, ts in _content_dedup.items() if now - ts > CONTENT_DEDUP_WINDOW * 2]
        for k in stale:
            del _content_dedup[k]
        if key in _content_dedup and now - _content_dedup[key] < CONTENT_DEDUP_WINDOW:
            return True
        _content_dedup[key] = now
        return False


# ── Nextcloud API ──────────────────────────────────────────────────────────────

def api_get(base_url: str, headers: dict, path: str, timeout: int = 15):
    req = urllib.request.Request(f"{base_url}{path}", headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def api_post(base_url: str, headers: dict, path: str, params: dict, timeout: int = 15):
    data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(
        f"{base_url}{path}",
        data=data,
        headers={**headers, "Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def fetch_all_rooms(base_url: str, headers: dict) -> list:
    """Return all rooms the Servetus user is a participant in."""
    data = api_get(base_url, headers, "/ocs/v2.php/apps/spreed/api/v4/room?format=json")
    return data["ocs"]["data"]


def fetch_notifications(base_url: str, headers: dict) -> list:
    """Return pending Nextcloud notifications — room invites land here."""
    try:
        data = api_get(base_url, headers, "/ocs/v1.php/core/api/v1/notifications?format=json")
        return data.get("ocs", {}).get("data", [])
    except Exception:
        return []


def mark_notification_read(base_url: str, headers: dict, notif_id: int):
    try:
        req = urllib.request.Request(
            f"{base_url}/ocs/v2.php/apps/notifications/api/v1/notifications/{notif_id}?format=json",
            headers=headers,
            method="DELETE",
        )
        urllib.request.urlopen(req, timeout=10).close()
    except Exception:
        pass


def dismiss_all_notifications(base_url: str, headers: dict):
    try:
        req = urllib.request.Request(
            f"{base_url}/ocs/v2.php/apps/notifications/api/v1/notifications?format=json",
            headers=headers,
            method="DELETE",
        )
        urllib.request.urlopen(req, timeout=10).close()
    except Exception:
        pass


def join_room(base_url: str, headers: dict, token: str):
    """Accept a room invite — POST to participants endpoint."""
    try:
        api_post(base_url, headers, f"/ocs/v2.php/apps/spreed/api/v4/room/{token}/participants?format=json", {})
        print(f"[invite] Joined room {token}")
    except Exception as e:
        print(f"[invite] Could not join {token}: {e}")


def fetch_messages(base_url: str, headers: dict, token: str, since_id: int | None, limit: int = 20) -> list:
    if since_id:
        path = (f"/ocs/v2.php/apps/spreed/api/v1/chat/{token}"
                f"?lookIntoFuture=0&lastKnownMessageId={since_id}&limit={limit}&format=json")
    else:
        path = f"/ocs/v2.php/apps/spreed/api/v1/chat/{token}?lookIntoFuture=0&limit={limit}&format=json"
    try:
        data = api_get(base_url, headers, path)
        msgs = data["ocs"]["data"]
        # API returns newest-first; we want oldest-first
        return list(reversed(msgs))
    except urllib.error.HTTPError as e:
        if e.code == 304:
            return []
        raise


def fetch_thread_history(base_url: str, headers: dict, token: str, limit: int = THREAD_HISTORY) -> list:
    path = (f"/ocs/v2.php/apps/spreed/api/v1/chat/{token}"
            f"?lookIntoFuture=0&limit={limit}&format=json")
    try:
        data = api_get(base_url, headers, path)
        return list(reversed(data["ocs"]["data"]))
    except Exception:
        return []


def _post_chunk(base_url: str, headers: dict, token: str, text: str) -> dict:
    return api_post(base_url, headers,
                    f"/ocs/v2.php/apps/spreed/api/v1/chat/{token}?format=json",
                    {"message": text})


def send_message(base_url: str, headers: dict, token: str, text: str) -> dict:
    if len(text) <= MAX_MESSAGE_CHARS:
        return _post_chunk(base_url, headers, token, text)
    chunks, remaining = [], text
    while remaining:
        if len(remaining) <= MAX_MESSAGE_CHARS:
            chunks.append(remaining)
            break
        window = remaining[:MAX_MESSAGE_CHARS]
        cut = window.rfind("\n\n")
        if cut == -1:
            cut = window.rfind("\n")
        if cut == -1:
            cut = MAX_MESSAGE_CHARS
        chunks.append(remaining[:cut].rstrip())
        remaining = remaining[cut:].lstrip()
    last = None
    for i, chunk in enumerate(chunks):
        label = f"({i+1}/{len(chunks)}) " if len(chunks) > 1 else ""
        last = _post_chunk(base_url, headers, token, label + chunk)
    return last


def fetch_reactions(base_url: str, headers: dict, token: str, msg_id: int) -> dict:
    try:
        data = api_get(base_url, headers,
                       f"/ocs/v2.php/apps/spreed/api/v1/reaction/{token}/{msg_id}?format=json",
                       timeout=10)
        return data["ocs"]["data"]
    except Exception:
        return {}


def set_presence_online(base_url: str, headers: dict):
    try:
        data = urllib.parse.urlencode({"statusType": "online"}).encode()
        req = urllib.request.Request(
            f"{base_url}/ocs/v2.php/apps/user_status/api/v1/user_status/status?format=json",
            data=data,
            headers={**headers, "Content-Type": "application/x-www-form-urlencoded"},
            method="PUT",
        )
        urllib.request.urlopen(req, timeout=10).close()
    except Exception:
        pass


# ── Witness ────────────────────────────────────────────────────────────────────

def find_witness(actor_id: str) -> str | None:
    if not actor_id or actor_id == MY_ACTOR:
        return None
    found = {}
    exact = WITNESSES_DIR / f"{actor_id}_witness.md"
    if exact.exists():
        found[exact] = exact.read_text().strip()
    if WITNESSES_DIR.exists():
        for wf in WITNESSES_DIR.glob("*.md"):
            if wf in found:
                continue
            try:
                text = wf.read_text()
                if f"actor_id: {actor_id}" in text or f'actor_id: "{actor_id}"' in text:
                    found[wf] = text.strip()
            except Exception:
                continue
    if not found:
        return None
    return "\n\n---\n\n".join(c for _, c in sorted(found.items(), key=lambda kv: len(kv[1]), reverse=True))


def update_witness(actor_id: str, display_name: str, token: str, room_name: str, room_type: str):
    if not actor_id or actor_id == MY_ACTOR:
        return
    path = WITNESSES_DIR / f"{actor_id}_witness.md"
    now   = datetime.now().strftime("%Y-%m-%dT%H:%M:00-05:00")
    today = datetime.now().strftime("%Y-%m-%d")

    if not path.exists() and WITNESSES_DIR.exists():
        for wf in WITNESSES_DIR.glob("*.md"):
            try:
                text = wf.read_text()
                if f"actor_id: {actor_id}" in text or f'actor_id: "{actor_id}"' in text:
                    path = wf
                    break
            except Exception:
                continue

    if not path.exists():
        WITNESSES_DIR.mkdir(parents=True, exist_ok=True)
        path.write_text(f"""---
servitus:
  schema_version: 1
  system_version: 0.2.1
  record_type: witness
  pipeline_stage: distilled
  status: active
  intent: reference

identity:
  title: "{display_name}"
  slug: "{actor_id}-witness"
  record_id: "SV-{today.replace('-','')}-NOW-CST-WITN"

time:
  created_at: "{now}"
  updated_at: "{now}"
  timezone: "America/Chicago"
  source_range: "ongoing"

subject:
  actor_id: "{actor_id}"
  display_name: "{display_name}"

circles:
  read: inner

keywords:
  - witness
  - {actor_id}

tags:
  - servitus
  - witness
---

# {display_name}

## Known Identity

- **Nextcloud username:** {actor_id}
- **Display name:** {display_name}

## Rooms

| Room | Token | Type | First seen | Last seen |
|------|-------|------|-----------|-----------|
| {room_name} | {token} | {room_type} | {today} | {today} |

## What Works With Them

*Positive observations — what they respond well to, communication style, shared interests.*

## Navigate Carefully

*Friction points, sensitivities, topics that require tact or should be avoided.*

## Context Notes

*Role, relationship to Christian, project involvement, anything else relevant.*
""")
        print(f"[witness] Created: {path.name}")
    else:
        text = path.read_text()
        text = re.sub(r'(  updated_at: )"[^"]+"', f'\\1"{now}"', text)
        row_pat = re.compile(rf'\| {re.escape(room_name)} \| {re.escape(token)} \|.*\| \d{{4}}-\d{{2}}-\d{{2}} \|')
        if row_pat.search(text):
            text = row_pat.sub(
                lambda m: re.sub(r'\| \d{4}-\d{2}-\d{2} \|$', f'| {today} |', m.group()), text)
        elif "## Rooms" in text:
            text = text.replace(
                "## Rooms\n\n| Room | Token | Type | First seen | Last seen |\n|------|-------|------|-----------|-----------|",
                f"## Rooms\n\n| Room | Token | Type | First seen | Last seen |\n|------|-------|------|-----------|----------|\n| {room_name} | {token} | {room_type} | {today} | {today} |"
            )
        path.write_text(text)


# ── Claude ─────────────────────────────────────────────────────────────────────

def load_system_prompt(actor_id: str | None = None, talk_state: str | None = None) -> str:
    specs = [
        "Toolkit/S00.01-00-00-servetus-bootloader.md",
        "Toolkit/S00.01-04-00-servetus-behavioral-rules.md",
        "Toolkit/S00.01-05-00-servetus-guardrails.md",
        "Toolkit/S00.01-06-00-servetus-disclosure-spec.md",
        "config/projects.md",
    ]
    now_str = datetime.now().strftime("%Y-%m-%dT%H:%M:00-05:00")
    parts = [
        "You are Servetus — the executive officer and knowledge architecture for Christian Sass.\n"
        "\n"
        "## OPERATING CONTEXT\n"
        "\n"
        "You are running inside Nextcloud Talk as a bot. This is NOT a Claude Code session.\n"
        "CRITICAL: You MUST NOT output JSON, XML, tool_call blocks, markdown code fences, "
        "or any structured syntax in your replies. Respond only in plain conversational prose.\n"
        "\n"
        "## WHAT YOU CAN AND CANNOT DO IN TALK\n"
        "\n"
        "Talk is the reporting layer. The Claude Code CLI is where the hard lift happens. You are NOT "
        "limited to passive responses — you can dispatch tasks to the cluster queue "
        "(10-System/cluster/queue/) and the Claude Code daemon will pick them up within ~15 seconds.\n"
        "\n"
        "Cluster task types: claude-code-run, summarize, talk-send.\n"
        "\n"
        "In Talk: respond from context you already have. If you need to look something up, say so "
        "and dispatch it to the cluster.\n"
        "\n"
        "## DM ETIQUETTE\n"
        "\n"
        "One reply per message. Short and direct. No looping. No responding to your own messages.\n"
        "\n"
        f"## CURRENT TIME\n\nRight now: {now_str} (America/Chicago)\n",
    ]
    for rel in specs:
        path = VAULT_ROOT / rel
        if path.exists():
            content = path.read_text().strip()
            if content:
                parts.append(f"=== {rel} ===\n{content}")
    if actor_id:
        witness = find_witness(actor_id)
        if witness:
            parts.append(f"## WHO YOU ARE TALKING TO\n\n{witness}")
    if talk_state:
        parts.append(f"## CURRENT TALK STATE\n\n{talk_state}")
    return "\n\n".join(parts)


def get_talk_state(base_url: str, headers: dict, active_token: str | None = None) -> str:
    global _talk_state_cache, _talk_state_ts
    with _talk_state_lock:
        if time.time() - _talk_state_ts < TALK_STATE_TTL and _talk_state_cache:
            state = _talk_state_cache
            if active_token:
                state = re.sub(r" ← YOU ARE HERE", "", state)
                state = state.replace(f"({active_token})", f"({active_token}) ← YOU ARE HERE", 1)
            return state
        try:
            fresh = _build_talk_state(base_url, headers, active_token)
            _talk_state_cache = fresh
            _talk_state_ts = time.time()
            return fresh
        except Exception as e:
            print(f"  [talk-state] {e}")
            return _talk_state_cache or "(Talk state unavailable)"


def _build_talk_state(base_url: str, headers: dict, active_token: str | None = None) -> str:
    type_map = {1: "1-on-1", 2: "group", 3: "group", 4: "public"}
    lines = []
    rooms = fetch_all_rooms(base_url, headers)
    rooms_sorted = sorted(
        rooms,
        key=lambda r: (-(r.get("unreadMessages", 0) + r.get("unreadMention", 0)),
                       -r.get("lastActivity", 0))
    )
    unread_lines, read_lines = [], []
    for r in rooms_sorted:
        name    = r.get("displayName", r.get("token", "?"))
        rtype   = type_map.get(r.get("type", 3), "group")
        unread  = r.get("unreadMessages", 0)
        mention = r.get("unreadMention", 0)
        last    = r.get("lastMessage", {})
        preview = ""
        if isinstance(last, dict) and last.get("message"):
            actor   = last.get("actorDisplayName", last.get("actorId", ""))
            preview = f"{actor}: {last['message']}"[:60].strip(": ")
        tok    = r.get("token", "")
        marker = " ← YOU ARE HERE" if tok == active_token else ""
        if unread > 0 or mention > 0:
            badge = f"[{unread} unread" + (f", {mention} mention" if mention else "") + "]"
            entry = f"  • {name} ({rtype}) {badge}{marker}"
            if preview:
                entry += f"\n    Last: {preview}"
            unread_lines.append(entry)
        else:
            entry = f"  • {name} ({rtype}){marker}"
            if preview:
                entry += f" — {preview[:40]}"
            read_lines.append(entry)
    if unread_lines:
        lines.append("Rooms with unread messages:\n" + "\n".join(unread_lines))
    if read_lines:
        lines.append("Read rooms:\n" + "\n".join(read_lines))
    return "\n\n".join(lines) if lines else "(Talk state unavailable)"


def expand_rich_message(msg: dict) -> str:
    text   = msg.get("message", "")
    params = msg.get("messageParameters", {})
    if not params:
        return text
    if "{object}" in text and "object" in params:
        obj = params["object"]
        if obj.get("type") == "talk-location":
            return f"[Map pin: {obj.get('name','location')} — {obj.get('latitude','?')},{obj.get('longitude','?')}]"
        return f"[Shared object: {obj.get('name', obj.get('description', 'object'))}]"
    if "{file}" in text and "file" in params:
        f = params["file"]
        mime = f.get("mimetype", "")
        name = f.get("name", "file")
        if mime.startswith("audio/"):
            return f"[Voice memo: {name}]"
        elif mime.startswith("image/"):
            return f"[Image: {name}]"
        elif mime.startswith("video/"):
            return f"[Video: {name}]"
        return f"[File: {name} ({mime})]"
    return text


def build_claude_messages(history: list, new_msg: dict) -> list:
    messages = []
    for msg in history:
        actor = msg.get("actorId", "")
        text  = expand_rich_message(msg)
        mtype = msg.get("messageType", "")
        if mtype in ("system", "command") or not text:
            continue
        role    = "assistant" if actor == MY_ACTOR else "user"
        display = msg.get("actorDisplayName", actor)
        content = text if actor in (MY_ACTOR, "csass") else f"[{display}]: {text}"
        if messages and messages[-1]["role"] == role:
            messages[-1]["content"] += f"\n{content}"
        else:
            messages.append({"role": role, "content": content})
    new_text = expand_rich_message(new_msg)
    actor    = new_msg.get("actorId", "")
    display  = new_msg.get("actorDisplayName", actor)
    content  = new_text if actor in ("csass",) else f"[{display}]: {new_text}"
    if messages and messages[-1]["role"] == "user":
        messages[-1]["content"] += f"\n{content}"
    else:
        messages.append({"role": "user", "content": content})
    return messages


def is_contextually_relevant(message: dict, history: list, api_key: str) -> bool:
    recent = []
    for m in history[-6:]:
        actor = m.get("actorDisplayName", m.get("actorId", "?"))
        text  = m.get("message", "")
        if m.get("messageType", "") in ("system", "command") or not text:
            continue
        recent.append(f"{actor}: {text}")
    new_name = message.get("actorDisplayName", "someone")
    recent.append(f"{new_name}: {message.get('message', '')}")
    prompt = (
        "You are deciding whether an AI assistant named Servetus should interject.\n"
        "Respond YES if the conversation is about AI, technology, the platform, server "
        "infrastructure, Servetus's capabilities, or a question Servetus could meaningfully "
        "answer. Respond NO for purely personal exchanges.\n\n"
        f"Conversation:\n{chr(10).join(recent)}\n\nShould Servetus respond? Reply YES or NO only."
    )
    try:
        client = anthropic.Anthropic(api_key=api_key)
        resp = client.messages.create(model=CLASSIFIER_MODEL, max_tokens=3,
                                      messages=[{"role": "user", "content": prompt}])
        return resp.content[0].text.strip().upper().startswith("YES")
    except Exception:
        return False


def should_respond(msg: dict, room_type: str, overrides: dict, token: str,
                   history: list, api_key: str) -> bool:
    actor = msg.get("actorId", "")
    text  = msg.get("message", "").lower()
    mtype = msg.get("messageType", "")
    if mtype in ("system", "command") or actor == MY_ACTOR:
        return False
    if room_type == "onetoone":
        return True
    room_cfg = overrides.get(token, {})
    if room_cfg.get("respond_all"):
        return True
    if "@servetus" in text or "servetus" in text:
        return True
    return is_contextually_relevant(msg, history, api_key)


# ── Command handling ───────────────────────────────────────────────────────────

def _secretary_status() -> str:
    secretary = Path(__file__).parent / "secretary.py"
    lines = [f"Servetus status — {datetime.now().strftime('%Y-%m-%d %H:%M')} CT", ""]
    try:
        result = subprocess.run([sys.executable, str(secretary), "--pretty"],
                                capture_output=True, text=True, timeout=20)
        data = json.loads(result.stdout) if result.stdout.strip() else {}
        q = data.get("transcription", {})
        recent = q.get("most_recent")
        ok = q.get("total_processed", "?")
        if recent:
            import os as _os
            lines.append(f"Transcription: {ok} done, last: {_os.path.basename(recent[1]) if len(recent) > 1 else '?'}")
        else:
            lines.append(f"Transcription: {ok} done")
        errors = q.get("total_errors", 0)
        if errors:
            lines.append(f"  Errors: {errors}")
        svcs = data.get("services", {})
        up   = [k for k, v in svcs.items() if v.get("active")]
        down = [k for k, v in svcs.items() if not v.get("active")]
        if up:
            lines.append(f"Services up: {', '.join(up)}")
        if down:
            lines.append(f"Services down: {', '.join(down)}")
        hopper = data.get("hopper", {})
        new_count = len(hopper.get("new_items", []))
        if new_count:
            lines.append(f"Hopper: {new_count} new items since last session")
    except Exception as e:
        lines.append(f"(secretary error: {e})")
    return "\n".join(lines)


def handle_command(msg: dict, token: str, base_url: str, headers: dict) -> bool:
    """Return True if we handled a structured command (skip Claude)."""
    actor = msg.get("actorId", "")
    text  = msg.get("message", "").strip()
    if actor == MY_ACTOR or not text:
        return False
    lc = text.lower()
    if lc.startswith("!status"):
        try:
            send_message(base_url, headers, token, _secretary_status())
        except Exception as e:
            print(f"[command] !status failed: {e}")
        return True
    if lc.startswith("approve:") or lc.startswith("reject:"):
        try:
            sys.path.insert(0, str(Path(__file__).parent))
            from approval import ApprovalManager
            mgr = ApprovalManager()
            mgr.process_message(room_token=token, actor=actor, message=text)
        except Exception as e:
            print(f"[approval] {e}")
        return True
    return False


# ── Core message handler ───────────────────────────────────────────────────────

def handle_message(msg: dict, room_name: str, room_type: str, token: str,
                   base_url: str, headers: dict, api_key: str) -> int | None:
    actor_id = msg.get("actorId", "")
    actor    = msg.get("actorDisplayName", actor_id or "?")
    text     = msg.get("message", "")
    ts       = datetime.fromtimestamp(msg.get("timestamp", 0)).strftime("%H:%M")
    print(f"\n[{ts}] {room_name} | {actor}: {text}")

    try:
        update_witness(actor_id, actor, token, room_name, room_type)
    except Exception as e:
        print(f"  [witness] {e}")

    history  = fetch_thread_history(base_url, headers, token)
    messages = build_claude_messages(history, msg)
    if not messages:
        return None

    talk_state = get_talk_state(base_url, headers, active_token=token)
    system     = load_system_prompt(actor_id=actor_id, talk_state=talk_state)
    client     = anthropic.Anthropic(api_key=api_key)
    try:
        resp  = client.messages.create(model=CLAUDE_MODEL, max_tokens=1024,
                                       system=system, messages=messages)
        reply = resp.content[0].text.strip()
        print(f"  → {reply[:80]}...")
        result = send_message(base_url, headers, token, reply)
        return result.get("ocs", {}).get("data", {}).get("id")
    except Exception as e:
        print(f"  → Claude error: {e}")
        return None


# ── Reaction watcher ───────────────────────────────────────────────────────────

def watch_reactions(base_url: str, headers: dict, api_key: str):
    while True:
        time.sleep(REACTION_POLL_INTERVAL)
        with _our_msg_ids_lock:
            snapshot = {t: list(ids) for t, ids in _our_msg_ids.items()}
        for token, msg_ids in snapshot.items():
            for msg_id in msg_ids:
                reactions = fetch_reactions(base_url, headers, token, msg_id)
                for emoji, reactors in reactions.items():
                    for reactor in reactors:
                        actor_id = reactor.get("actorId", "")
                        if actor_id == MY_ACTOR:
                            continue
                        key = f"{token}:{msg_id}:{emoji}:{actor_id}"
                        with _reacted_lock:
                            if key in _reacted:
                                continue
                            _reacted.add(key)
                        actor    = reactor.get("actorDisplayName", actor_id)
                        history  = fetch_thread_history(base_url, headers, token)
                        original = next((m.get("message", "") for m in history if m.get("id") == msg_id), "")
                        system   = load_system_prompt()
                        client   = anthropic.Anthropic(api_key=api_key)
                        prompt   = (f"{actor} reacted with {emoji} to your message: \"{original}\"\n"
                                    "Respond briefly and naturally. 1-2 sentences, conversational.")
                        try:
                            resp  = client.messages.create(model=CLAUDE_MODEL, max_tokens=256,
                                                           system=system,
                                                           messages=[{"role": "user", "content": prompt}])
                            reply = resp.content[0].text.strip()
                            send_message(base_url, headers, token, reply)
                        except Exception as e:
                            print(f"  [reaction] {e}")


# ── Presence heartbeat ─────────────────────────────────────────────────────────

def presence_heartbeat(base_url: str, headers: dict, interval: int = 240):
    while True:
        set_presence_online(base_url, headers)
        time.sleep(interval)


# ── Notification handler ───────────────────────────────────────────────────────

def process_notifications(base_url: str, headers: dict, api_key: str):
    """
    Check the notifications endpoint for Talk room invites and mentions
    in rooms not yet in our cursor. Join invited rooms, seed cursors.
    """
    notifs = fetch_notifications(base_url, headers)
    for n in notifs:
        if n.get("app") != "spreed":
            continue
        notif_id = n.get("notification_id") or n.get("notificationId")
        subject  = n.get("subject", "")
        params   = n.get("subjectRichParameters") or {}

        # Room invite
        if "invited" in subject.lower() or n.get("objectType") == "room":
            token = n.get("objectId") or (params.get("call", {}) or {}).get("id")
            if token:
                print(f"[notification] Room invite: {token}")
                join_room(base_url, headers, token)
                mark_notification_read(base_url, headers, notif_id)

        # Mention in unknown room
        elif "mentioned" in subject.lower() or "mention" in subject.lower():
            token = n.get("objectId") or (params.get("call", {}) or {}).get("id")
            if token:
                with _cursor_lock:
                    already_watching = token in _cursor
                if not already_watching:
                    print(f"[notification] Mention in new room: {token}")
                    # Cursor will be seeded on next poll cycle
                mark_notification_read(base_url, headers, notif_id)


# ── Main poll loop ─────────────────────────────────────────────────────────────

ROOM_TYPES = {1: "onetoone", 2: "group", 3: "group", 4: "public", 5: "notetoself", 6: "notetoself"}


def run(once: bool = False):
    env     = load_env()
    url     = env["NEXTCLOUD_URL"]
    user    = env["NEXTCLOUD_USER"]
    pw      = env["NEXTCLOUD_APP_PASSWORD"]
    api_key = env["ANTHROPIC_API_KEY"]
    headers = make_headers(user, pw)

    print(f"[talk-listener] Starting as '{user}' on {url}")

    if not once:
        threading.Thread(target=watch_reactions, args=(url, headers, api_key),
                         daemon=True, name="reactions").start()
        threading.Thread(target=presence_heartbeat, args=(url, headers),
                         daemon=True, name="presence").start()

    while True:
        try:
            # Check notifications first — pick up invites before room poll
            process_notifications(url, headers, api_key)

            rooms = fetch_all_rooms(url, headers)
            overrides = load_overrides()

            for r in rooms:
                token     = r.get("token")
                room_name = r.get("displayName", token)
                room_type = ROOM_TYPES.get(r.get("type", 3), "group")
                unread    = r.get("unreadMessages", 0)
                last_msg  = r.get("lastMessage", {})
                last_id   = last_msg.get("id") if isinstance(last_msg, dict) else None

                with _cursor_lock:
                    known = token in _cursor
                    cursor_id = _cursor.get(token)

                # First time seeing this room — seed cursor to current position, no replay
                if not known:
                    seed_id = last_id or 0
                    with _cursor_lock:
                        _cursor[token] = seed_id
                    print(f"[new room] {room_name} ({token}) — seeded at {seed_id}")
                    continue

                # Skip rooms with nothing new
                if unread == 0 and (last_id is None or last_id <= cursor_id):
                    continue

                # Fetch only messages since our cursor
                messages = fetch_messages(url, headers, token, since_id=cursor_id)

                for msg in messages:
                    msg_id = msg.get("id", 0)
                    with _cursor_lock:
                        if msg_id <= _cursor.get(token, 0):
                            continue
                        _cursor[token] = msg_id

                    handle_key = (token, msg_id)
                    with _handled_lock:
                        if handle_key in _handled:
                            continue
                        _handled.add(handle_key)

                    msg_actor = msg.get("actorId", "")
                    msg_text  = msg.get("message", "").strip()
                    if msg_actor and msg_actor != MY_ACTOR and msg_text:
                        if _is_content_duplicate(token, msg_actor, msg_text):
                            continue

                    if handle_command(msg, token, url, headers):
                        continue

                    history = fetch_thread_history(url, headers, token)
                    if should_respond(msg, room_type, overrides, token, history, api_key):
                        sent_id = handle_message(msg, room_name, room_type, token,
                                                 url, headers, api_key)
                        if sent_id:
                            with _our_msg_ids_lock:
                                _our_msg_ids.setdefault(token, [])
                                _our_msg_ids[token].append(sent_id)
                                _our_msg_ids[token] = _our_msg_ids[token][-20:]

        except Exception as e:
            print(f"[poll] {e}")
            time.sleep(RETRY_DELAY)
            continue

        if once:
            break

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    run(once="--once" in sys.argv)
