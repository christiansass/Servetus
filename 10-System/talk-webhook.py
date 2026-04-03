#!/usr/bin/env python3
"""
talk-webhook.py — Nextcloud Talk Bot API webhook receiver for Servetus.

NC pushes a POST to this server whenever a message arrives in a registered room.
No polling. No 429s. Push-based, one HTTP handler per message.

── Setup (run once) ──────────────────────────────────────────────────────────

1. Generate a shared secret:
       python3 -c "import secrets; print(secrets.token_hex(32))"
   Add to config/nextcloud.env:
       WEBHOOK_SECRET=<the hex string>

2. Expose this server to the NC host.
   Interim (Mac → Tailscale Funnel):
       tailscale funnel --bg 8082
   Permanent (server-side): run this script on the NC server, use localhost URL.

3. Register the bot on the NC server:
       php occ talk:bot:install "Servetus" <WEBHOOK_SECRET> \
           "https://<public-host>/webhook" "Servetus XO" \
           --feature=webhook --feature=response

4. Start this server under PM2:
       pm2 start 10-System/talk-webhook.py --name servetus-webhook \
           --interpreter python3
       pm2 save

5. Retire the polling bot:
       pm2 stop servetus-talk
       pm2 delete servetus-talk
       pm2 save

── config/nextcloud.env keys ─────────────────────────────────────────────────
    NEXTCLOUD_URL=https://your.server
    NEXTCLOUD_USER=servetus
    NEXTCLOUD_APP_PASSWORD=your-app-password
    ANTHROPIC_API_KEY=sk-...
    WEBHOOK_SECRET=your-shared-secret

── Usage ─────────────────────────────────────────────────────────────────────
    python3 10-System/talk-webhook.py              # port 8082
    python3 10-System/talk-webhook.py --port 9000
"""

import json
import re
import base64
import sys
import hmac
import hashlib
import threading
import urllib.request
import urllib.error
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from datetime import datetime
import anthropic

# Attachment processing + vault write-back
sys.path.insert(0, str(Path(__file__).parent))
try:
    from attachment_handler import process_attachment
    from vault_writer import write_artifact, IngestionSource
    ATTACHMENTS_ENABLED = True
except ImportError as _att_err:
    print(f"[talk-webhook] attachment modules unavailable: {_att_err}")
    ATTACHMENTS_ENABLED = False

VAULT_ROOT       = Path(__file__).parent.parent

# Conversation logging
try:
    from conversation_logger import log_message as _log_message
    LOGGING_ENABLED = True
except ImportError as _log_err:
    print(f"[talk-webhook] conversation logger unavailable: {_log_err}")
    LOGGING_ENABLED = False


def log_talk(room_token, room_name, actor_id, actor_display, message,
             attachment_name=None, is_bot=False):
    if not LOGGING_ENABLED:
        return
    try:
        _log_message(
            room_token=room_token,
            room_name=room_name,
            actor_id=actor_id,
            actor_display=actor_display,
            message=message,
            attachment_name=attachment_name,
            is_bot=is_bot,
        )
    except Exception as le:
        print(f"  [log] {le}")
ENV_FILE         = VAULT_ROOT / "config" / "nextcloud.env"
ROOMS_FILE       = VAULT_ROOT / "config" / "talk-rooms.json"
WITNESSES_DIR    = VAULT_ROOT / "08-Witnesses"
MY_ACTOR         = "servetus"
THREAD_HISTORY   = 6
CLAUDE_MODEL     = "claude-sonnet-4-6"
CLASSIFIER_MODEL = "claude-haiku-4-5-20251001"
DEFAULT_PORT     = 8082

# Loaded at startup, refreshed from disk on each request
_env   = {}
_env_lock   = threading.Lock()
_rooms_lock = threading.Lock()


# ── Environment / Config ───────────────────────────────────────────────────────

def load_env():
    env = {}
    with open(ENV_FILE) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env


def load_rooms():
    if not ROOMS_FILE.exists():
        return {}
    with open(ROOMS_FILE) as f:
        return json.load(f)


def make_headers(user, password):
    b64 = base64.b64encode(f"{user}:{password}".encode()).decode()
    return {"Authorization": f"Basic {b64}", "OCS-APIREQUEST": "true"}


def find_witness_for_actor(actor_id: str):
    """
    Return combined content of all witness files for this actor_id, or None.
    Collects: exact {actor_id}_witness.md + any file with actor_id in frontmatter.
    Returns them all concatenated — both auto-generated and human-authored files.
    """
    if not actor_id or actor_id == MY_ACTOR:
        return None

    found = {}  # path -> content, deduped

    exact = WITNESSES_DIR / f"{actor_id}_witness.md"
    if exact.exists():
        found[exact] = exact.read_text().strip()

    if WITNESSES_DIR.exists():
        needle_bare = f"actor_id: {actor_id}"
        needle_quoted = f'actor_id: "{actor_id}"'
        for wf in WITNESSES_DIR.glob("*.md"):
            if wf in found:
                continue
            try:
                text = wf.read_text()
                if needle_bare in text or needle_quoted in text:
                    found[wf] = text.strip()
            except Exception:
                continue

    if not found:
        return None

    sorted_files = sorted(found.items(), key=lambda kv: len(kv[1]), reverse=True)
    return "\n\n---\n\n".join(content for _, content in sorted_files)


def fetch_talk_state_for_webhook(base_url, headers, active_token=None):
    """
    Build a human-readable Talk sidebar summary for injection into the system prompt.
    Equivalent to what a user sees when they open Nextcloud Talk.
    """
    type_map = {1: "1-on-1", 2: "group", 3: "group", 4: "public"}
    lines = []

    try:
        endpoint = f"{base_url}/ocs/v2.php/apps/spreed/api/v4/room?format=json"
        req = urllib.request.Request(endpoint, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            rooms = data["ocs"]["data"]

        rooms_sorted = sorted(
            rooms,
            key=lambda r: (-(r.get("unreadMessages", 0) + r.get("unreadMention", 0)),
                           -r.get("lastActivity", 0))
        )
        unread_lines = []
        read_lines = []
        for r in rooms_sorted:
            name      = r.get("displayName", r.get("token", "?"))
            rtype     = type_map.get(r.get("type", 3), "group")
            unread    = r.get("unreadMessages", 0)
            mention   = r.get("unreadMention", 0)
            last_msg  = r.get("lastMessage", {})
            last_text = last_msg.get("message", "") if isinstance(last_msg, dict) else ""
            last_actor = (last_msg.get("actorDisplayName", last_msg.get("actorId", ""))
                          if isinstance(last_msg, dict) else "")
            preview = f"{last_actor}: {last_text}"[:60].strip(": ") if last_text else ""
            tok = r.get("token", "")
            active_marker = " ← YOU ARE HERE" if tok == active_token else ""

            if unread > 0 or mention > 0:
                badge = f"[{unread} unread" + (f", {mention} mention" if mention else "") + "]"
                entry = f"  • {name} ({rtype}) {badge}{active_marker}"
                if preview:
                    entry += f"\n    Last: {preview}"
                unread_lines.append(entry)
            else:
                entry = f"  • {name} ({rtype}){active_marker}"
                if preview:
                    entry += f" — {preview[:40]}"
                read_lines.append(entry)

        if unread_lines:
            lines.append("Rooms with unread messages:\n" + "\n".join(unread_lines))
        if read_lines:
            lines.append("Read rooms:\n" + "\n".join(read_lines))
    except Exception as e:
        lines.append(f"(Room state unavailable: {e})")

    try:
        notif_endpoint = f"{base_url}/ocs/v2.php/apps/admin_notifications/api/v1/notifications?format=json"
        req = urllib.request.Request(notif_endpoint, headers=headers)
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read())
            notifs = data.get("ocs", {}).get("data", [])
            if notifs:
                notif_lines = []
                for n in notifs[:10]:
                    subject = n.get("subject", "")
                    msg     = n.get("message", "")
                    app     = n.get("app", "")
                    notif_lines.append(f"  • [{app}] {subject}" + (f" — {msg}" if msg else ""))
                lines.append("Pending notifications:\n" + "\n".join(notif_lines))
    except Exception:
        pass

    return "\n\n".join(lines) if lines else None


def load_system_prompt(env=None, token=None, rooms=None, actor_id=None, talk_state=None):
    specs = [
        "Toolkit/S00.01-00-00-servetus-bootloader.md",
        "Toolkit/S00.01-04-00-servetus-behavioral-rules.md",
        "Toolkit/S00.01-05-00-servetus-guardrails.md",
        "Toolkit/S00.01-06-00-servetus-disclosure-spec.md",
        "config/projects.md",
    ]
    # last-session-brief.md intentionally excluded — contains Claude Code tool call
    # artifacts that cause the model to emit raw JSON in Talk messages.

    room_name = (rooms or {}).get(token, {}).get("name", token) if token else "unknown"
    nc_url  = (env or {}).get("NEXTCLOUD_URL", "unknown")
    nc_user = (env or {}).get("NEXTCLOUD_USER", "servetus")
    now_str = datetime.now().strftime("%Y-%m-%dT%H:%M:00-05:00")

    parts = [
        "You are Servetus — the executive officer and knowledge architecture for Christian Sass.\n"
        "\n"
        "## OPERATING CONTEXT — READ THIS FIRST\n"
        "\n"
        "You are running inside Nextcloud Talk as an automated bot. This is NOT a Claude Code session.\n"
        "CRITICAL: You MUST NOT output JSON, XML, tool_call blocks, code fences, or any structured "
        "syntax in your replies. Plain conversational prose only — as if writing a chat message.\n"
        "\n"
        "## WHAT YOU CAN AND CANNOT DO IN TALK\n"
        "\n"
        "Talk is the reporting layer. The Claude Code CLI is where the hard lift happens.\n"
        "In Talk: respond from context you already have. Do not attempt to run commands or searches.\n"
        "If you need to look something up that you don't have in context, say so plainly and suggest\n"
        "Christian run it via the CLI. Never pretend you searched when you didn't.\n"
        "\n"
        "## DM ETIQUETTE\n"
        "\n"
        "One reply per message. Short and direct. Never respond to your own messages.\n"
        "\n"
        f"## CURRENT TIME\n"
        f"\n"
        f"Right now: {now_str} (America/Chicago)\n"
        "\n"
        "## WHAT YOU ALREADY KNOW\n"
        f"\n"
        f"- Nextcloud URL: {nc_url}\n"
        f"- Your username: {nc_user}\n"
        f"- Current room: {room_name}\n"
        f"- All credentials and room tokens are already configured — never ask for them\n"
        "\n"
        "## ATTACHMENT HANDLING\n"
        "\n"
        "When someone shares a file, the runtime downloads and extracts it before you respond.\n"
        "File content appears directly in the message. Respond to it naturally.\n"
        "If no file content appears in this message, no file was received.\n",
    ]
    for rel in specs:
        path = VAULT_ROOT / rel
        if path.exists():
            content = path.read_text().strip()
            if content:
                parts.append(f"=== {rel} ===\n{content}")

    # Inject witness context for the current actor
    if actor_id:
        witness_content = find_witness_for_actor(actor_id)
        if witness_content:
            parts.append(
                f"## WHO YOU ARE TALKING TO\n\n"
                f"Witness file for this conversation's participant:\n\n{witness_content}"
            )

    # Inject Talk sidebar state
    if talk_state:
        parts.append(f"## CURRENT TALK STATE (what you'd see in the sidebar)\n\n{talk_state}")

    return "\n\n".join(parts)


# ── Witness ────────────────────────────────────────────────────────────────────

def update_witness(actor_id, display_name, token, room_name, room_type):
    if not actor_id or actor_id == MY_ACTOR:
        return
    path  = WITNESSES_DIR / f"{actor_id}_witness.md"
    now   = datetime.now().strftime("%Y-%m-%dT%H:%M:00-05:00")
    today = datetime.now().strftime("%Y-%m-%d")

    # If a human-authored witness file already exists with this actor_id in frontmatter,
    # adopt that file instead of creating a new skeleton.
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
  record_id: "SV-{today.replace('-', '')}-NOW-CST-WITN"

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
        text = path.read_text()
        text = re.sub(r'(  updated_at: )"[^"]+"', f'\\1"{now}"', text)
        row_pat = re.compile(
            rf'\| {re.escape(room_name)} \| {re.escape(token)} \|.*\| \d{{4}}-\d{{2}}-\d{{2}} \|'
        )
        if row_pat.search(text):
            text = row_pat.sub(
                lambda m: re.sub(r'\| \d{4}-\d{2}-\d{2} \|$', f'| {today} |', m.group()),
                text,
            )
        elif "## Rooms" in text:
            text = text.replace(
                "## Rooms\n\n| Room | Token | Type | First seen | Last seen |\n|------|-------|------|-----------|-----------|",
                (
                    "## Rooms\n\n| Room | Token | Type | First seen | Last seen |\n"
                    "|------|-------|------|-----------|----------|\n"
                    f"| {room_name} | {token} | {room_type} | {today} | {today} |"
                ),
            )
        path.write_text(text)


# ── NC Talk API ────────────────────────────────────────────────────────────────

def fetch_recent_messages(base_url, headers, token, limit=5):
    """Fetch the most recent messages in a room (newest-first from NC, returned as-is)."""
    endpoint = (
        f"{base_url}/ocs/v2.php/apps/spreed/api/v1/chat/{token}"
        f"?lookIntoFuture=0&limit={limit}&format=json"
    )
    req = urllib.request.Request(endpoint, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
            return data["ocs"]["data"]  # newest-first
    except Exception:
        return []


def fetch_message_details(base_url, headers, token, message_id):
    """
    Find a specific message by ID in the recent message list.
    Returns the full message dict (including messageParameters) or None.
    """
    msgs = fetch_recent_messages(base_url, headers, token, limit=10)
    target = str(message_id)
    for m in msgs:
        if str(m.get("id", "")) == target:
            return m
    return None


def fetch_thread_history(base_url, headers, token, limit=THREAD_HISTORY):
    endpoint = (
        f"{base_url}/ocs/v2.php/apps/spreed/api/v1/chat/{token}"
        f"?lookIntoFuture=0&limit={limit}&format=json"
    )
    req = urllib.request.Request(endpoint, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
            # NC returns newest-first; reverse to oldest-first for Claude
            return list(reversed(data["ocs"]["data"]))
    except Exception:
        return []


def send_message(base_url, headers, token, message_text):
    data = urllib.parse.urlencode({"message": message_text}).encode()
    req  = urllib.request.Request(
        f"{base_url}/ocs/v2.php/apps/spreed/api/v1/chat/{token}?format=json",
        data=data,
        headers={**headers, "Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())


# ── Claude ─────────────────────────────────────────────────────────────────────

def build_claude_messages(history, actor_id, actor_display, message_text):
    messages = []
    for msg in history:
        a     = msg.get("actorId", "")
        text  = msg.get("message", "")
        mtype = msg.get("messageType", "")
        if mtype in ("system", "command") or not text:
            continue
        role    = "assistant" if a == MY_ACTOR else "user"
        display = msg.get("actorDisplayName", a)
        content = text if a in (MY_ACTOR, "csass") else f"[{display}]: {text}"
        if messages and messages[-1]["role"] == role:
            messages[-1]["content"] += f"\n{content}"
        else:
            messages.append({"role": role, "content": content})

    content = message_text if actor_id == "csass" else f"[{actor_display}]: {message_text}"
    if messages and messages[-1]["role"] == "user":
        messages[-1]["content"] += f"\n{content}"
    else:
        messages.append({"role": "user", "content": content})

    return messages


def is_contextually_relevant(actor_display, message_text, history, api_key):
    recent = []
    for m in history[-6:]:
        name  = m.get("actorDisplayName", m.get("actorId", "?"))
        text  = m.get("message", "")
        mtype = m.get("messageType", "")
        if mtype in ("system", "command") or not text:
            continue
        recent.append(f"{name}: {text}")
    recent.append(f"{actor_display}: {message_text}")

    prompt = (
        "You are deciding whether an AI assistant named Servetus should interject in this conversation.\n"
        "Servetus should respond when: the conversation is about AI, technology, the platform, "
        "server infrastructure, Servetus's capabilities, or when a question is asked that Servetus "
        "could meaningfully answer. Servetus should stay silent for purely personal exchanges "
        "between humans that don't invite AI input.\n\n"
        f"Conversation:\n{chr(10).join(recent)}\n\n"
        "Should Servetus respond? Reply YES or NO only."
    )
    try:
        client = anthropic.Anthropic(api_key=api_key)
        resp   = client.messages.create(
            model=CLASSIFIER_MODEL,
            max_tokens=3,
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.content[0].text.strip().upper().startswith("YES")
    except Exception:
        return False


# ── Hood-Up Diagnostic ─────────────────────────────────────────────────────────

HOOD_UP_TRIGGERS = {
    "hood up", "diagnostic", "what are you working with",
    "what's loaded", "open the hood", "what do you know",
    "context check", "what context", "system state",
}


def is_diagnostic_request(message_text):
    lower = message_text.lower().strip()
    return any(trigger in lower for trigger in HOOD_UP_TRIGGERS)


def _extract_witness_summary(witness_text):
    """Pull the Relationship Summary section from a witness file."""
    if not witness_text:
        return None
    lines = witness_text.splitlines()
    in_section = False
    summary_lines = []
    for line in lines:
        if line.startswith("## Relationship Summary"):
            in_section = True
            continue
        if in_section:
            if line.startswith("## "):
                break
            if line.strip() or summary_lines:
                summary_lines.append(line)
    text = "\n".join(summary_lines).strip()
    return text if text else None


def _extract_frontmatter_value(text, key):
    """Minimal YAML key extractor — handles quoted and unquoted values."""
    import re as _re
    m = _re.search(rf'^\s*{_re.escape(key)}:\s*["\']?([^"\'\n]+)["\']?', text, _re.MULTILINE)
    return m.group(1).strip() if m else None


def _load_active_arcs():
    """Return list of (title, slug) for all active arcs."""
    arcs_dir = VAULT_ROOT / "05-Arcs"
    results = []
    if not arcs_dir.exists():
        return results
    for arc_file in sorted(arcs_dir.glob("*.md")):
        if arc_file.name.startswith("_"):
            continue
        try:
            text = arc_file.read_text()
            status = _extract_frontmatter_value(text, "status")
            if status and status.lower() != "active":
                continue
            title = _extract_frontmatter_value(text, "title")
            if not title:
                title = arc_file.stem.replace("_arc", "").replace("-", " ").title()
            results.append(title)
        except Exception:
            continue
    return results


def build_diagnostic_report(token, actor_id, actor_display, room_name, room_type, history, env, rooms, talk_state):
    import importlib.util as _ilu
    version = "0.2.1"
    mode = env.get("SERVETUS_MODE", "development")
    room_obj = rooms.get(token, {})
    circle = room_obj.get("circle", "unknown")

    lines = []

    # Thread — the actual conversation, compact
    visible = [m for m in history if m.get("messageType") not in ("system", "command") and m.get("message")]
    window_note = f"{len(visible)}/{THREAD_HISTORY}" + (" — window full" if len(visible) >= THREAD_HISTORY else "")
    lines.append(f"THREAD  ({window_note})")
    if visible:
        for m in visible:
            is_bot = m.get("actorId") == MY_ACTOR
            label  = "S" if is_bot else "You"
            raw_text = m.get("message", "")
            try:
                parsed = json.loads(raw_text)
                text = parsed.get("message", raw_text)
            except (json.JSONDecodeError, TypeError):
                text = raw_text
            display = text[:100] + ("…" if len(text) > 100 else "")
            lines.append(f"  {label}: {display}")
    else:
        lines.append("  (empty — no prior messages in window)")
    lines.append("")

    # Who you are — one line
    witness_raw = find_witness_for_actor(actor_id)
    org  = _extract_frontmatter_value(witness_raw, "organization") if witness_raw else None
    role = _extract_frontmatter_value(witness_raw, "role")         if witness_raw else None
    tier = _extract_frontmatter_value(witness_raw, "trust_tier")   if witness_raw else None
    who_parts = [actor_display]
    if role:  who_parts.append(role)
    if org:   who_parts.append(org)
    if tier:  who_parts.append(tier)
    lines.append("  ".join(who_parts))
    lines.append("")

    # Active arcs
    arcs = _load_active_arcs()
    if arcs:
        lines.append("ARCS  " + "  ·  ".join(arcs))
        lines.append("")

    # Footer — version, mode, room, context health
    specs_ok = sum(1 for rel in [
        "Toolkit/S00.01-00-00-servetus-bootloader.md",
        "Toolkit/S00.01-04-00-servetus-behavioral-rules.md",
        "Toolkit/S00.01-05-00-servetus-guardrails.md",
        "Toolkit/S00.01-06-00-servetus-disclosure-spec.md",
    ] if (VAULT_ROOT / rel).exists())
    witness_flag = "witness OK" if witness_raw else "NO WITNESS"
    sidebar_flag = "sidebar OK" if talk_state else "no sidebar"
    lines.append(
        f"v{version}  ·  {mode}  ·  {room_name} [{circle}]  ·  "
        f"specs {specs_ok}/4  ·  {witness_flag}  ·  {sidebar_flag}"
    )

    return "\n".join(lines)


def should_respond(room, room_type, actor_id, actor_display, message_text, history, api_key, mentioned_bot=False):
    if actor_id == MY_ACTOR:
        return False
    if room_type == "onetoone":
        return True
    if mentioned_bot:
        return True
    if room and room.get("respond_all"):
        return True
    msg_lower = message_text.lower()
    if "@servetus" in msg_lower or "servetus" in msg_lower:
        return True
    return is_contextually_relevant(actor_display, message_text, history, api_key)


def handle_incoming(token, actor_id, actor_display, message_text, message_id=None, mentioned_bot=False):
    env     = load_env()
    url     = env["NEXTCLOUD_URL"]
    user    = env["NEXTCLOUD_USER"]
    pw      = env["NEXTCLOUD_APP_PASSWORD"]
    api_key = env["ANTHROPIC_API_KEY"]
    headers = make_headers(user, pw)

    rooms     = load_rooms()
    room      = rooms.get(token, {})
    room_name = room.get("name", token)
    room_type = room.get("type", "group")

    ts = datetime.now().strftime("%H:%M")
    print(f"\n[{ts}] {room_name} | {actor_display}: {message_text[:80]}")

    try:
        update_witness(actor_id, actor_display, token, room_name, room_type)
    except Exception as e:
        print(f"  [witness] {e}")

    # Log incoming message (attachment_name filled in below after detection)
    _log_incoming_text   = message_text
    _log_attachment_name = None

    # ── Attachment detection ────────────────────────────────────────────────
    attachment = None
    if ATTACHMENTS_ENABLED and message_id:
        try:
            full_msg  = fetch_message_details(url, headers, token, message_id)
            # messageParameters is {} when present, [] when empty (NC quirk)
            params    = (full_msg or {}).get("messageParameters") or {}
            file_info = params.get("file") if isinstance(params, dict) else None
            if file_info:
                print(f"  [attachment] detected: {file_info.get('name','?')} ({file_info.get('mimetype','?')})")
                attachment = process_attachment(file_info, url, user, pw)
                if attachment:
                    print(f"  [attachment] {attachment.summary}")
                    _log_attachment_name = attachment.filename
                    # Write into vault — artifact chain + memory note + witness backlink
                    try:
                        write_artifact(attachment, IngestionSource(
                            surface       = "talk",
                            actor_id      = actor_id,
                            actor_display = actor_display,
                            room_token    = token,
                            room_name     = room_name,
                        ))
                    except Exception as ve:
                        print(f"  [vault] write failed: {ve}")
        except Exception as e:
            print(f"  [attachment] error: {e}")

    # Log the incoming message now that we know the attachment (if any)
    log_talk(token, room_name, actor_id, actor_display,
             _log_incoming_text, attachment_name=_log_attachment_name)

    history = fetch_thread_history(url, headers, token)

    # For file-share messages ({file} template), always respond in 1-on-1;
    # the message_text may be bare "{file}" — treat it as addressed if attachment present
    effective_text = message_text
    if message_text.strip() in ("{file}", "") and attachment:
        effective_text = f"[shared file: {attachment.filename}]"

    if not should_respond(room, room_type, actor_id, actor_display, effective_text, history, api_key, mentioned_bot=mentioned_bot):
        print("  → silent (not addressed to Servetus)")
        return

    # ── Hood-up diagnostic — short-circuit before Claude ───────────────────
    if is_diagnostic_request(effective_text):
        try:
            talk_state_diag = fetch_talk_state_for_webhook(url, headers, active_token=token)
        except Exception:
            talk_state_diag = None
        report = build_diagnostic_report(
            token, actor_id, actor_display, room_name, room_type,
            history, env, rooms, talk_state_diag
        )
        print(f"  → Diagnostic requested by {actor_display}")
        send_message(url, headers, token, report)
        log_talk(token, room_name, MY_ACTOR, "Servetus", report, is_bot=True)
        return

    messages = build_claude_messages(history, actor_id, actor_display, effective_text)
    if not messages:
        return

    # ── Inject attachment content into last user message ────────────────────
    if attachment:
        last = messages[-1]
        if attachment.image_data and attachment.media_type:
            # Claude vision: replace string content with content block list
            existing_text = last["content"] if isinstance(last["content"], str) else ""
            last["content"] = [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": attachment.media_type,
                        "data": base64.b64encode(attachment.image_data).decode(),
                    },
                },
                {"type": "text", "text": existing_text or f"[shared: {attachment.filename}]"},
            ]
        elif attachment.text:
            # Text-based (PDF, DOCX, transcription): append to message content
            injected = attachment.text[:12000]  # cap at 12k chars
            if isinstance(last["content"], str):
                last["content"] += f"\n\n{injected}"
            else:
                last["content"].append({"type": "text", "text": injected})

    try:
        talk_state = fetch_talk_state_for_webhook(url, headers, active_token=token)
    except Exception as _ts_err:
        talk_state = None
        print(f"  [talk-state] {_ts_err}")

    system = load_system_prompt(env=env, token=token, rooms=rooms, actor_id=actor_id, talk_state=talk_state)
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
        send_message(url, headers, token, reply)
        log_talk(token, room_name, MY_ACTOR, "Servetus", reply, is_bot=True)
    except Exception as e:
        print(f"  → Error: {e}")


# ── Signature Validation ───────────────────────────────────────────────────────

def verify_signature(secret: str, random_header: str, body: bytes, sig_header: str) -> bool:
    """HMAC-SHA256(random_header_bytes + body_bytes, secret) == sig_header (hex)."""
    mac = hmac.new(
        secret.encode(),
        random_header.encode() + body,
        hashlib.sha256,
    )
    return hmac.compare_digest(mac.hexdigest(), sig_header.lower())


# ── Payload Parsing ────────────────────────────────────────────────────────────

def last_path_segment(url: str) -> str:
    return url.rstrip("/").split("/")[-1]


def extract_actor_id(actor_obj: dict) -> str:
    """
    Best-effort NC username extraction from actor object.
    NC Talk Bot API actor.id is typically https://host/u/<username>
    or https://host/ocs/.../participants/active. Try last segment first.
    """
    actor_url = actor_obj.get("id", "")
    if actor_url:
        segment = last_path_segment(actor_url)
        # Skip numeric IDs and NC API path endings
        if segment and not segment.isdigit() and segment not in ("active", "participants"):
            return segment
    # Fallback: slugify display name
    name = actor_obj.get("name", "unknown")
    return re.sub(r"[^a-z0-9_-]", "", name.lower().replace(" ", "-")) or "unknown"


# ── HTTP Handler ───────────────────────────────────────────────────────────────

class WebhookHandler(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        # Suppress default access log noise; we log manually
        pass

    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"ok\n")
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path != "/webhook":
            self.send_response(404)
            self.end_headers()
            return

        length   = int(self.headers.get("Content-Length", 0))
        body     = self.rfile.read(length)
        random_h = self.headers.get("X-Nextcloud-Talk-Random", "")
        sig_h    = self.headers.get("X-Nextcloud-Talk-Signature", "")

        # Reload env fresh (picks up secret rotation without restart)
        try:
            env = load_env()
        except Exception:
            env = _env

        secret = env.get("WEBHOOK_SECRET", "")
        if secret:
            if not verify_signature(secret, random_h, body, sig_h):
                print("[webhook] signature mismatch — rejected")
                self.send_response(401)
                self.end_headers()
                return
        else:
            print("[webhook] WEBHOOK_SECRET not set — skipping signature check")

        # ACK immediately; NC Talk expects a fast 200
        self.send_response(200)
        self.end_headers()

        try:
            payload = json.loads(body)
        except Exception as e:
            print(f"[webhook] JSON parse error: {e}")
            return

        # Only handle Create (new message) events
        if payload.get("type") != "Create":
            return

        target_id     = payload.get("target", {}).get("id", "")
        token         = last_path_segment(target_id)
        actor_obj     = payload.get("actor", {})
        actor_id      = extract_actor_id(actor_obj)
        actor_display = actor_obj.get("name", actor_id)
        obj           = payload.get("object", {})
        # NC Talk bot webhook delivers object.content as a JSON-encoded string:
        # {"message": "actual text", "parameters": {...}}
        # Parse it to extract the clean human-readable message.
        raw_content   = obj.get("content", "").strip()
        mentioned_bot = False
        try:
            parsed = json.loads(raw_content)
            message_text = parsed.get("message", raw_content).strip()
            # Expand {mention-userN} placeholders and detect bot @mentions
            params = parsed.get("parameters") or {}
            if isinstance(params, dict):
                for key, val in params.items():
                    if isinstance(val, dict):
                        name = val.get("name", key)
                        if val.get("id") == MY_ACTOR:
                            mentioned_bot = True
                        message_text = message_text.replace("{" + key + "}", name)
        except (json.JSONDecodeError, AttributeError):
            message_text = raw_content
        obj_id        = obj.get("id", "")
        # object.id URL ends in: .../chat/<token>/<message_id>
        message_id    = last_path_segment(obj_id) if obj_id else None

        if not token or (not message_text and not message_id):
            return

        print(f"[webhook] {token} | {actor_display}: {message_text[:60]}")

        threading.Thread(
            target=handle_incoming,
            args=(token, actor_id, actor_display, message_text),
            kwargs={"message_id": message_id, "mentioned_bot": mentioned_bot},
            daemon=True,
        ).start()


# ── Entry Point ────────────────────────────────────────────────────────────────

def main():
    global _env

    port = DEFAULT_PORT
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--port" and i + 1 < len(args):
            port = int(args[i + 1])
            i += 2
        elif args[i].startswith("--port="):
            port = int(args[i].split("=", 1)[1])
            i += 1
        else:
            i += 1

    _env   = load_env()
    rooms  = load_rooms()

    if "WEBHOOK_SECRET" not in _env:
        print("[talk-webhook] WARNING: WEBHOOK_SECRET not set — requests will not be validated")

    print(f"[talk-webhook] Starting as '{_env.get('NEXTCLOUD_USER', '?')}' on {_env.get('NEXTCLOUD_URL', '?')}")
    print(f"[talk-webhook] Listening on 0.0.0.0:{port}  →  POST /webhook")
    print(f"[talk-webhook] {len(rooms)} rooms loaded from talk-rooms.json")
    print(f"[talk-webhook] Health check: GET /health")

    server = HTTPServer(("0.0.0.0", port), WebhookHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[talk-webhook] Stopped.")


if __name__ == "__main__":
    main()
