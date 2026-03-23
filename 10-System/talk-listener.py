#!/usr/bin/env python3
"""
talk-listener.py — Concurrent Nextcloud Talk monitor for Servetus.

Each room runs in its own thread using lookIntoFuture=1 long-polling.
New rooms are discovered every ROOM_REFRESH_INTERVAL seconds.
Emoji reactions on Servetus messages are monitored and handled.

Triggers on:
  - Any message in a 1-on-1 (onetoone) room
  - @Servetus mention in group/public rooms
  - respond_all flag set on a room in talk-rooms.json
  - Contextual relevance (Haiku classifier) in group rooms
  - Emoji reactions on Servetus messages

Usage:
    python3 10-System/talk-listener.py           # run continuously
    python3 10-System/talk-listener.py --once    # single pass, then exit

config/nextcloud.env must contain:
    NEXTCLOUD_URL=https://your.server
    NEXTCLOUD_USER=servetus
    NEXTCLOUD_APP_PASSWORD=your-app-password
"""

import json
import re
import base64
import time
import sys
import threading
import urllib.request
import urllib.error
import urllib.parse
from pathlib import Path
from datetime import datetime
import anthropic

VAULT_ROOT  = Path(__file__).parent.parent
ENV_FILE    = VAULT_ROOT / "config" / "nextcloud.env"
ROOMS_FILE  = VAULT_ROOT / "config" / "talk-rooms.json"
CURSOR_FILE = VAULT_ROOT / "config" / "talk-cursor.json"

POLL_TIMEOUT          = 30    # seconds per long-poll hold
RETRY_DELAY           = 5     # seconds after error before retry
ROOM_REFRESH_INTERVAL = 120   # seconds between room list refreshes
MY_ACTOR              = "servetus"
THREAD_HISTORY        = 12    # messages of context to Claude
CLAUDE_MODEL          = "claude-sonnet-4-6"
CLASSIFIER_MODEL      = "claude-haiku-4-5-20251001"

# Shared state — protected by locks
_cursor_lock  = threading.Lock()
_rooms_lock   = threading.Lock()
_cursor_cache = {}
_rooms_cache  = {}

# Track which message IDs we've already reacted to (avoid double-react)
_reacted_ids = set()
_reacted_lock = threading.Lock()

# Track Servetus message IDs per room for reaction monitoring (token -> list of int IDs)
_servetus_msg_ids = {}
_servetus_msg_ids_lock = threading.Lock()

# Track which room tokens have active watcher threads
_active_tokens = set()
_active_tokens_lock = threading.Lock()


def load_env():
    env = {}
    with open(ENV_FILE) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env


def load_system_prompt():
    """Load bootloader specs as system prompt — same specs the hook injects."""
    specs = [
        "Toolkit/S00.01-00-00-servetus-bootloader.md",
        "Toolkit/S00.01-04-00-servetus-behavioral-rules.md",
        "Toolkit/S00.01-05-00-servetus-guardrails.md",
        "Toolkit/S00.01-06-00-servetus-disclosure-spec.md",
        "config/projects.md",
        "10-System/last-session-brief.md",
    ]
    parts = ["You are Servetus — the executive officer and knowledge architecture for Christian Sass.",
             "You are operating in Nextcloud Talk. Respond conversationally. Be direct. No hollow affirmations.\n"]
    for rel in specs:
        path = VAULT_ROOT / rel
        if path.exists():
            content = path.read_text().strip()
            if content:
                parts.append(f"=== {rel} ===\n{content}")
    return "\n\n".join(parts)


WITNESSES_DIR = VAULT_ROOT / "08-Witnesses"


def update_witness(actor_id, display_name, token, room_name, room_type):
    """Create or update the witness file for a Talk participant."""
    if not actor_id or actor_id == MY_ACTOR:
        return
    path = WITNESSES_DIR / f"{actor_id}_witness.md"
    now  = datetime.now().strftime("%Y-%m-%dT%H:%M:00-05:00")
    today = datetime.now().strftime("%Y-%m-%d")

    if not path.exists():
        WITNESSES_DIR.mkdir(parents=True, exist_ok=True)
        content = f"""---
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
"""
        path.write_text(content)
        print(f"[witness] Created: {actor_id}_witness.md")
    else:
        # Update updated_at and last-seen for this room
        text = path.read_text()
        text = re.sub(r'(  updated_at: )"[^"]+"', f'\\1"{now}"', text)
        # Update last-seen for this token in the rooms table
        row_pattern = re.compile(rf'\| {re.escape(room_name)} \| {re.escape(token)} \|.*\| \d{{4}}-\d{{2}}-\d{{2}} \|')
        if row_pattern.search(text):
            text = row_pattern.sub(
                lambda m: re.sub(r'\| \d{4}-\d{2}-\d{2} \|$', f'| {today} |', m.group()),
                text
            )
        elif "## Rooms" in text:
            # Append new room row
            text = text.replace(
                "## Rooms\n\n| Room | Token | Type | First seen | Last seen |\n|------|-------|------|-----------|-----------|",
                f"## Rooms\n\n| Room | Token | Type | First seen | Last seen |\n|------|-------|------|-----------|----------|\n| {room_name} | {token} | {room_type} | {today} | {today} |"
            )
        path.write_text(text)


def fetch_thread_history(base_url, headers, token, limit=THREAD_HISTORY):
    """Fetch recent messages from a room for context."""
    endpoint = (
        f"{base_url}/ocs/v2.php/apps/spreed/api/v1/chat/{token}"
        f"?lookIntoFuture=0&limit={limit}&format=json"
    )
    req = urllib.request.Request(endpoint, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
            return data["ocs"]["data"]
    except Exception:
        return []


def build_claude_messages(history, new_message):
    """Convert Talk thread history into Claude API message format."""
    messages = []
    for msg in history:
        actor = msg.get("actorId", "")
        text  = msg.get("message", "")
        mtype = msg.get("messageType", "")
        if mtype in ("system", "command") or not text:
            continue
        role = "assistant" if actor == MY_ACTOR else "user"
        # Prefix non-Christian speakers in group rooms
        display = msg.get("actorDisplayName", actor)
        content = text if actor in (MY_ACTOR, "csass") else f"[{display}]: {text}"
        # Merge consecutive same-role messages
        if messages and messages[-1]["role"] == role:
            messages[-1]["content"] += f"\n{content}"
        else:
            messages.append({"role": role, "content": content})

    # Ensure thread ends with the new user message
    new_text = new_message.get("message", "")
    display  = new_message.get("actorDisplayName", "")
    actor    = new_message.get("actorId", "")
    content  = new_text if actor in ("csass",) else f"[{display}]: {new_text}"
    if messages and messages[-1]["role"] == "user":
        messages[-1]["content"] += f"\n{content}"
    else:
        messages.append({"role": "user", "content": content})

    return messages


def make_headers(user, password):
    b64 = base64.b64encode(f"{user}:{password}".encode()).decode()
    return {"Authorization": f"Basic {b64}", "OCS-APIREQUEST": "true"}


def load_rooms():
    if not ROOMS_FILE.exists():
        return {}
    with open(ROOMS_FILE) as f:
        return json.load(f)


def load_cursor():
    if not CURSOR_FILE.exists():
        return {}
    with open(CURSOR_FILE) as f:
        return json.load(f)


def save_cursor(cursor):
    with open(CURSOR_FILE, "w") as f:
        json.dump(cursor, f, indent=2)


def fetch_messages(base_url, headers, token, last_id=None):
    """
    Long-poll for new messages in a room.
    If last_id is set, uses lookIntoFuture=1 (waits for new messages).
    Otherwise fetches recent history to seed the cursor.
    """
    if last_id:
        endpoint = (
            f"{base_url}/ocs/v2.php/apps/spreed/api/v1/chat/{token}"
            f"?lookIntoFuture=1&timeout={POLL_TIMEOUT}&lastKnownMessageId={last_id}"
            f"&limit=20&format=json"
        )
    else:
        endpoint = (
            f"{base_url}/ocs/v2.php/apps/spreed/api/v1/chat/{token}"
            f"?lookIntoFuture=0&limit=5&format=json"
        )

    req = urllib.request.Request(endpoint, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=POLL_TIMEOUT + 10) as resp:
            data = json.loads(resp.read())
            return data["ocs"]["data"]
    except urllib.error.HTTPError as e:
        if e.code == 304:
            return []  # No new messages — normal long-poll timeout
        raise


def is_contextually_relevant(message, history, api_key):
    """
    Ask Haiku whether this message warrants a Servetus response.
    Returns True if Servetus should interject, False if it should stay silent.
    Fast and cheap — max_tokens=3, expects YES or NO.
    """
    recent = []
    for m in history[-6:]:
        actor = m.get("actorDisplayName", m.get("actorId", "?"))
        text  = m.get("message", "")
        mtype = m.get("messageType", "")
        if mtype in ("system", "command") or not text:
            continue
        recent.append(f"{actor}: {text}")

    new_text = message.get("message", "")
    new_name = message.get("actorDisplayName", "someone")
    recent.append(f"{new_name}: {new_text}")

    thread = "\n".join(recent)

    prompt = (
        "You are deciding whether an AI assistant named Servetus should interject in this conversation.\n"
        "Servetus should respond when: the conversation is about AI, technology, the platform, "
        "server infrastructure, Servetus's capabilities, or when a question is asked that Servetus "
        "could meaningfully answer. Servetus should stay silent for purely personal exchanges "
        "between humans that don't invite AI input.\n\n"
        f"Conversation:\n{thread}\n\n"
        "Should Servetus respond? Reply YES or NO only."
    )

    try:
        client = anthropic.Anthropic(api_key=api_key)
        resp = client.messages.create(
            model=CLASSIFIER_MODEL,
            max_tokens=3,
            messages=[{"role": "user", "content": prompt}]
        )
        answer = resp.content[0].text.strip().upper()
        return answer.startswith("YES")
    except Exception:
        return False


def is_addressed_to_me(message, room_type, room=None, history=None, api_key=None):
    """Check if this message should trigger a Servetus response."""
    actor = message.get("actorId", "")
    msg   = message.get("message", "").lower()
    mtype = message.get("messageType", "")

    # Don't respond to system messages or our own messages
    if mtype in ("system", "command") or actor == MY_ACTOR:
        return False

    # Always respond to direct messages
    if room_type == "onetoone":
        return True

    # Rooms flagged respond_all — respond to everyone regardless of @mention
    if room and room.get("respond_all"):
        return True

    # Explicit @mention — always respond
    if "@servetus" in msg or "servetus" in msg:
        return True

    # Contextual relevance check — let Haiku decide
    if api_key and history is not None:
        return is_contextually_relevant(message, history, api_key)

    return False


def handle_message(message, room_name, room_type, token, base_url, headers, api_key, history=None):
    """Fetch thread context, call Claude, post reply. Returns sent message ID or None."""
    actor_id = message.get("actorId", "")
    actor    = message.get("actorDisplayName", actor_id or "?")
    msg      = message.get("message", "")
    ts       = datetime.fromtimestamp(message.get("timestamp", 0)).strftime("%H:%M")
    print(f"\n[{ts}] {room_name} | {actor}: {msg}")

    # Update witness file for this participant
    try:
        update_witness(actor_id, actor, token, room_name, room_type)
    except Exception as e:
        print(f"  [witness] update failed: {e}")

    if history is None:
        history = fetch_thread_history(base_url, headers, token)
    messages = build_claude_messages(history, message)
    if not messages:
        return None

    system = load_system_prompt()
    client = anthropic.Anthropic(api_key=api_key)

    try:
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=1024,
            system=system,
            messages=messages,
        )
        reply = response.content[0].text.strip()
        print(f"  → Replying: {reply[:80]}...")
        result = send_message(base_url, headers, token, reply)
        return result.get("ocs", {}).get("data", {}).get("id")
    except Exception as e:
        print(f"  → Claude API error: {e}")
        return None


def send_message(base_url, headers, token, message_text):
    """Post a message to a Talk room."""
    import urllib.parse
    data = urllib.parse.urlencode({"message": message_text}).encode()
    req  = urllib.request.Request(
        f"{base_url}/ocs/v2.php/apps/spreed/api/v1/chat/{token}?format=json",
        data=data,
        headers={**headers, "Content-Type": "application/x-www-form-urlencoded"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())


REACTION_POLL_INTERVAL = 15  # seconds between reaction sweeps


def fetch_reactions(base_url, headers, token, message_id):
    """Fetch reactions for a specific message. Returns dict of emoji -> list of reactor dicts."""
    endpoint = (
        f"{base_url}/ocs/v2.php/apps/spreed/api/v1/reaction/{token}/{message_id}"
        f"?format=json"
    )
    req = urllib.request.Request(endpoint, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            return data["ocs"]["data"]
    except Exception:
        return {}


def handle_reaction(base_url, headers, token, message_id, emoji, reactor, api_key):
    """Respond to an emoji reaction placed on a Servetus message."""
    actor = reactor.get("actorDisplayName", reactor.get("actorId", "someone"))
    history = fetch_thread_history(base_url, headers, token)
    original_text = ""
    for msg in history:
        if msg.get("id") == message_id:
            original_text = msg.get("message", "")
            break

    system = load_system_prompt()
    client = anthropic.Anthropic(api_key=api_key)
    prompt = (
        f"{actor} reacted with {emoji} to your message: \"{original_text}\"\n"
        f"Respond briefly and naturally to this reaction. 1-2 sentences, conversational."
    )
    try:
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=256,
            system=system,
            messages=[{"role": "user", "content": prompt}]
        )
        reply = response.content[0].text.strip()
        print(f"  → Reaction reply: {reply[:80]}")
        send_message(base_url, headers, token, reply)
    except Exception as e:
        print(f"  → Reaction reply error: {e}")


def watch_reactions(url, headers, api_key):
    """Background thread: polls for emoji reactions on recent Servetus messages."""
    while True:
        time.sleep(REACTION_POLL_INTERVAL)
        with _servetus_msg_ids_lock:
            snapshot = {t: list(ids) for t, ids in _servetus_msg_ids.items()}

        for token, msg_ids in snapshot.items():
            with _rooms_lock:
                room = _rooms_cache.get(token, {})
            name = room.get("name", token)

            for msg_id in msg_ids:
                reactions = fetch_reactions(url, headers, token, msg_id)
                for emoji, reactors in reactions.items():
                    for reactor in reactors:
                        actor_id = reactor.get("actorId", "")
                        if actor_id == MY_ACTOR:
                            continue
                        react_key = f"{token}:{msg_id}:{emoji}:{actor_id}"
                        with _reacted_lock:
                            if react_key in _reacted_ids:
                                continue
                            _reacted_ids.add(react_key)
                        print(f"[reaction] {name} | {actor_id} reacted {emoji} to msg {msg_id}")
                        handle_reaction(url, headers, token, msg_id, emoji, reactor, api_key)


def fetch_rooms_from_api(base_url, headers):
    """Fetch all Talk rooms from Nextcloud API."""
    endpoint = f"{base_url}/ocs/v2.php/apps/spreed/api/v1/room?format=json"
    req = urllib.request.Request(endpoint, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
            return data["ocs"]["data"]
    except Exception as e:
        print(f"[refresh_rooms] API error: {e}")
        return []


def watch_room(token, url, headers, api_key):
    """Per-room daemon thread: long-polls for new messages indefinitely."""
    last_id = None
    with _cursor_lock:
        last_id = _cursor_cache.get(token)

    # Low-priority rooms start with a delay so high-priority rooms get first slots
    with _rooms_lock:
        initial_priority = _rooms_cache.get(token, {}).get("priority", "normal")
    if initial_priority == "low":
        time.sleep(30)
    elif initial_priority == "normal":
        time.sleep(10)

    while True:
        with _rooms_lock:
            room = _rooms_cache.get(token, {})
        if not room:
            time.sleep(RETRY_DELAY)
            continue

        name      = room.get("name", token)
        room_type = room.get("type", "group")

        try:
            messages = fetch_messages(url, headers, token, last_id)

            for msg in messages:
                msg_id = msg.get("id", 0)

                with _cursor_lock:
                    current_last = _cursor_cache.get(token, 0)
                if last_id and msg_id <= current_last:
                    continue

                # Advance cursor immediately — prevents double-fire
                with _cursor_lock:
                    _cursor_cache[token] = msg_id
                    cursor_snapshot = dict(_cursor_cache)
                save_cursor(cursor_snapshot)
                last_id = msg_id

                # Passively record witness for any non-system participant
                msg_actor   = msg.get("actorId", "")
                msg_display = msg.get("actorDisplayName", msg_actor)
                if msg.get("messageType", "") not in ("system", "command") and msg_actor and msg_actor != MY_ACTOR:
                    try:
                        update_witness(msg_actor, msg_display, token, name, room_type)
                    except Exception:
                        pass

                history = fetch_thread_history(url, headers, token)
                if is_addressed_to_me(msg, room_type, room, history, api_key):
                    sent_id = handle_message(msg, name, room_type, token, url, headers, api_key, history)
                    if sent_id:
                        with _servetus_msg_ids_lock:
                            _servetus_msg_ids.setdefault(token, [])
                            _servetus_msg_ids[token].append(sent_id)
                            _servetus_msg_ids[token] = _servetus_msg_ids[token][-20:]

        except urllib.error.HTTPError as e:
            if e.code == 429:
                # Rate-limited — back off based on room priority
                with _rooms_lock:
                    priority = _rooms_cache.get(token, {}).get("priority", "normal")
                backoff = 15 if priority == "high" else 60
                print(f"[{name}] 429 rate-limited — backing off {backoff}s")
                time.sleep(backoff)
            elif e.code != 304:
                print(f"[{name}] HTTP {e.code}")
                time.sleep(RETRY_DELAY)
            # 304 = normal long-poll timeout; loop immediately
        except Exception as e:
            print(f"[{name}] {e}")
            time.sleep(RETRY_DELAY)


def spawn_room_thread(token, url, headers, api_key):
    """Spawn a daemon watcher thread for a room if not already active."""
    with _active_tokens_lock:
        if token in _active_tokens:
            return
        _active_tokens.add(token)
    t = threading.Thread(
        target=watch_room,
        args=(token, url, headers, api_key),
        daemon=True,
        name=f"room-{token}"
    )
    t.start()
    with _rooms_lock:
        name = _rooms_cache.get(token, {}).get("name", token)
    print(f"[talk-listener] Thread started: {name} ({token})")


def refresh_rooms(url, headers, api_key):
    """Background thread: discovers new Talk rooms every ROOM_REFRESH_INTERVAL seconds."""
    type_map = {1: "onetoone", 2: "group", 3: "group", 4: "public"}
    while True:
        time.sleep(ROOM_REFRESH_INTERVAL)
        api_rooms = fetch_rooms_from_api(url, headers)
        if not api_rooms:
            continue

        disk_rooms = load_rooms()
        changed = False

        for r in api_rooms:
            token = r.get("token")
            if not token:
                continue
            if token not in disk_rooms:
                room_type = type_map.get(r.get("type", 3), "group")
                new_room = {
                    "name": r.get("displayName", token),
                    "type": room_type,
                    "last_activity": r.get("lastActivity", 0),
                    "participants": []
                }
                disk_rooms[token] = new_room
                print(f"[refresh_rooms] New room: {new_room['name']} ({token})")
                changed = True

            with _rooms_lock:
                if token not in _rooms_cache:
                    _rooms_cache[token] = disk_rooms[token]

        if changed:
            with open(ROOMS_FILE, "w") as f:
                json.dump(disk_rooms, f, indent=2)

        # Spawn threads for any newly discovered rooms
        with _rooms_lock:
            current_tokens = list(_rooms_cache.keys())
        for token in current_tokens:
            spawn_room_thread(token, url, headers, api_key)


def run(once=False):
    env     = load_env()
    url     = env["NEXTCLOUD_URL"]
    user    = env["NEXTCLOUD_USER"]
    pw      = env["NEXTCLOUD_APP_PASSWORD"]
    api_key = env["ANTHROPIC_API_KEY"]
    headers = make_headers(user, pw)

    print(f"[talk-listener] Starting as '{user}' on {url}")

    with _cursor_lock:
        _cursor_cache.update(load_cursor())
    with _rooms_lock:
        _rooms_cache.update(load_rooms())

    if once:
        # Single pass — sequential, no threads
        with _rooms_lock:
            rooms_snapshot = dict(_rooms_cache)
        for token, room in rooms_snapshot.items():
            name      = room.get("name", token)
            room_type = room.get("type", "group")
            with _cursor_lock:
                last_id = _cursor_cache.get(token)
            try:
                messages = fetch_messages(url, headers, token, last_id)
                for msg in messages:
                    msg_id = msg.get("id", 0)
                    with _cursor_lock:
                        current_last = _cursor_cache.get(token, 0)
                    if last_id and msg_id <= current_last:
                        continue
                    with _cursor_lock:
                        _cursor_cache[token] = msg_id
                        cursor_snapshot = dict(_cursor_cache)
                    save_cursor(cursor_snapshot)
                    history = fetch_thread_history(url, headers, token)
                    if is_addressed_to_me(msg, room_type, room, history, api_key):
                        handle_message(msg, name, room_type, token, url, headers, api_key, history)
            except urllib.error.HTTPError as e:
                if e.code != 304:
                    print(f"[{name}] HTTP {e.code}")
            except Exception as e:
                print(f"[{name}] {e}")
        return

    if not _rooms_cache:
        print("[talk-listener] No rooms found — run talk-room-map.py first")
        return

    # Spawn per-room watcher threads — staggered to avoid burst 429s
    with _rooms_lock:
        tokens = list(_rooms_cache.keys())
    for i, token in enumerate(tokens):
        spawn_room_thread(token, url, headers, api_key)
        if i < len(tokens) - 1:
            time.sleep(2)

    # Room discovery thread
    threading.Thread(target=refresh_rooms, args=(url, headers, api_key),
                     daemon=True, name="room-refresh").start()

    # Reaction monitoring thread
    threading.Thread(target=watch_reactions, args=(url, headers, api_key),
                     daemon=True, name="reactions").start()

    print(f"[talk-listener] Monitoring {len(tokens)} rooms. "
          f"Room refresh every {ROOM_REFRESH_INTERVAL}s.")

    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("\n[talk-listener] Stopped.")


if __name__ == "__main__":
    once = "--once" in sys.argv
    run(once=once)
