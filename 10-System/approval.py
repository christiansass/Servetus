#!/usr/bin/env python3
"""
approval.py — Servetus Talk Approval Protocol

Two-factor approval for high-trust actions via Nextcloud Talk.

Factor 1: Approver is present in the Talk room (Nextcloud identity)
Factor 2: Approver received a one-time token out-of-band (email/SMS)
          and pastes it in the room: APPROVE: <token>

Spec: Toolkit/S00.01-14-00-servetus-talk-approval-protocol.md

State persisted to: 10-System/.approval-state.json (gitignored)

Usage:
    from approval import ApprovalManager

    mgr = ApprovalManager()

    # Propose a high-trust action
    action_id = mgr.propose(
        description="Deploy new Whisper model to WordInFilm",
        reason="Faster transcription for new recording format",
        impact="10 min service interruption, transcription queue pauses",
        requester="servetus",
        required_approvers=["csass", "jcoler"],
        quorum="unanimous",
        room_token="abc123"          # NC Talk room token
    )

    # Deliver tokens out-of-band (email/SMS) — called after propose()
    token = mgr.get_delivery_token(action_id, "csass")
    # → send token via email to approver

    # Process an incoming Talk message — returns outcome or None
    outcome = mgr.process_message(
        room_token="abc123",
        actor="csass",
        message="APPROVE: a3f8c2d1..."
    )
    # outcome: {"status": "approved"|"rejected"|"pending", "action_id": ..., ...}
"""

import hashlib
import json
import os
import secrets
import smtplib
import sys
import urllib.request
import urllib.error
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from pathlib import Path
from typing import Optional


VAULT_ROOT  = Path(__file__).parent.parent
ENV_FILE    = VAULT_ROOT / "config" / "nextcloud.env"
STATE_FILE  = VAULT_ROOT / "10-System" / ".approval-state.json"

TOKEN_TTL_HOURS = 24
TOKEN_HEX_BYTES = 32  # 64-char hex token


def _load_env() -> dict:
    env = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                env[k.strip()] = v.strip()
    return env


def _load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except json.JSONDecodeError:
            pass
    return {"actions": {}}


def _save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2, default=str))


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _talk_post(env: dict, room_token: str, message: str) -> bool:
    """Post a message to a Nextcloud Talk room."""
    url = f"{env['NEXTCLOUD_URL']}/ocs/v2.php/apps/spreed/api/v1/chat/{room_token}"
    credentials = f"{env['NEXTCLOUD_USER']}:{env['NEXTCLOUD_APP_PASSWORD']}"
    import base64
    auth = base64.b64encode(credentials.encode()).decode()
    headers = {
        "Authorization": f"Basic {auth}",
        "OCS-APIRequest": "true",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
    }
    body = urllib.parse.urlencode({"message": message}).encode()
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status in (200, 201)
    except Exception as e:
        print(f"[approval] Talk post failed: {e}", file=sys.stderr)
        return False


import urllib.parse


class ApprovalManager:
    """
    Manages approval lifecycle for high-trust actions.

    All state persisted to .approval-state.json (gitignored).
    Token hashes stored — never plaintext tokens.
    """

    def __init__(self):
        self.env = _load_env()

    # ---------------------------------------------------------------
    # PROPOSE
    # ---------------------------------------------------------------

    def propose(
        self,
        description: str,
        reason: str,
        impact: str,
        requester: str,
        required_approvers: list[str],
        quorum: str = "unanimous",
        room_token: str = "",
        deadline_hours: Optional[int] = None,
    ) -> str:
        """
        Register a new approval request. Returns the action_id.

        quorum options: unanimous | majority | any-one | named
        """
        state = _load_state()

        action_id = f"APR-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{secrets.token_hex(4).upper()}"

        deadline = None
        if deadline_hours:
            deadline = (datetime.now(timezone.utc) + timedelta(hours=deadline_hours)).isoformat()

        state["actions"][action_id] = {
            "status": "pending",
            "description": description,
            "reason": reason,
            "impact": impact,
            "requester": requester,
            "required_approvers": required_approvers,
            "quorum": quorum,
            "room_token": room_token,
            "proposed_at": _now_iso(),
            "deadline": deadline,
            "tokens": {},       # approver_id -> {hash, expires_at, used, delivered_at}
            "responses": {},    # approver_id -> {action: approve|reject, timestamp}
            "outcome": None,
        }

        _save_state(state)

        # Post proposal to Talk room
        if room_token and self.env.get("NEXTCLOUD_URL"):
            deadline_str = f"Deadline: {deadline[:10] if deadline else 'None (pending approval)'}"
            approvers_str = " + ".join(required_approvers)
            msg = (
                f"ACTION REQUIRED: {description}\n"
                f"Requestor: {requester}\n"
                f"Reason: {reason}\n"
                f"Impact: {impact}\n"
                f"Requires: {approvers_str} ({quorum})\n"
                f"{deadline_str}"
            )
            _talk_post(self.env, room_token, msg)

        print(f"[approval] Proposed action {action_id}: {description}")
        return action_id

    # ---------------------------------------------------------------
    # TOKEN GENERATION + DELIVERY
    # ---------------------------------------------------------------

    def generate_token(self, action_id: str, approver_id: str) -> str:
        """
        Generate a one-time token for an approver. Returns the plaintext token
        (never stored — caller must deliver out-of-band).

        Stores only the SHA-256 hash in state.
        """
        state = _load_state()
        action = state["actions"].get(action_id)
        if not action:
            raise ValueError(f"Unknown action_id: {action_id}")

        token = secrets.token_hex(TOKEN_HEX_BYTES)
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        expires_at = (datetime.now(timezone.utc) + timedelta(hours=TOKEN_TTL_HOURS)).isoformat()

        action["tokens"][approver_id] = {
            "hash": token_hash,
            "expires_at": expires_at,
            "used": False,
            "delivered_at": None,
        }

        _save_state(state)
        return token  # caller delivers out-of-band; never log this value

    def mark_token_delivered(self, action_id: str, approver_id: str) -> None:
        """Record that the token was delivered (without storing the token)."""
        state = _load_state()
        action = state["actions"].get(action_id)
        if action and approver_id in action["tokens"]:
            action["tokens"][approver_id]["delivered_at"] = _now_iso()
            _save_state(state)

    def get_delivery_token(self, action_id: str, approver_id: str) -> str:
        """
        Convenience: generate + return token (caller is responsible for delivery).
        Call mark_token_delivered() after sending.
        """
        return self.generate_token(action_id, approver_id)

    def deliver_via_email(
        self,
        action_id: str,
        approver_id: str,
        to_address: str,
        smtp_host: str,
        smtp_port: int = 587,
        smtp_user: str = "",
        smtp_pass: str = "",
    ) -> bool:
        """
        Generate token and deliver via SMTP. Returns True on success.
        Token is never logged — only the delivery timestamp is recorded.
        """
        token = self.generate_token(action_id, approver_id)
        state = _load_state()
        action = state["actions"].get(action_id, {})

        msg = EmailMessage()
        msg["Subject"] = f"[Servetus] Approval required — {action.get('description','action')[:60]}"
        msg["From"] = smtp_user or "servetus@binaryranch.com"
        msg["To"] = to_address

        expires = action["tokens"][approver_id]["expires_at"][:16].replace("T", " ") + " UTC"

        msg.set_content(
            f"Servetus requires your approval for the following action:\n\n"
            f"ACTION: {action.get('description', '')}\n"
            f"Reason: {action.get('reason', '')}\n"
            f"Impact: {action.get('impact', '')}\n\n"
            f"To approve, paste the following in the Talk approval room:\n\n"
            f"  APPROVE: {token}\n\n"
            f"To reject, paste:\n\n"
            f"  REJECT: {token}\n\n"
            f"Token expires: {expires}\n"
            f"Single use only. Do not share this token.\n\n"
            f"— Servetus"
        )

        try:
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                if smtp_user and smtp_pass:
                    server.login(smtp_user, smtp_pass)
                server.send_message(msg)
            self.mark_token_delivered(action_id, approver_id)
            print(f"[approval] Token delivered to {to_address} for {approver_id}")
            return True
        except Exception as e:
            print(f"[approval] Email delivery failed: {e}", file=sys.stderr)
            return False

    # ---------------------------------------------------------------
    # PROCESS INCOMING TALK MESSAGE
    # ---------------------------------------------------------------

    def process_message(
        self, room_token: str, actor: str, message: str
    ) -> Optional[dict]:
        """
        Process an incoming Talk message. If it matches APPROVE: <token>
        or REJECT: <token>, validate and record the response.

        Returns outcome dict if quorum reached or action resolved, else None.

        Expected message format:
            APPROVE: a3f8c2d1e9b4...
            REJECT: a3f8c2d1e9b4...
        """
        message = message.strip()

        # Determine intent
        if message.upper().startswith("APPROVE:"):
            intent = "approve"
            submitted_token = message[8:].strip()
        elif message.upper().startswith("REJECT:"):
            intent = "reject"
            submitted_token = message[7:].strip()
        else:
            return None  # Not an approval message

        state = _load_state()

        # Find matching pending action for this room and actor
        matching_action_id = None
        for action_id, action in state["actions"].items():
            if (
                action["status"] == "pending"
                and action.get("room_token") == room_token
                and actor in action["required_approvers"]
                and actor not in action["responses"]
            ):
                matching_action_id = action_id
                break

        if not matching_action_id:
            return None

        action = state["actions"][matching_action_id]
        token_record = action["tokens"].get(actor)

        if not token_record:
            _talk_post(
                self.env, room_token,
                f"@{actor}: No token found for this approval. "
                "Contact the requestor to generate one."
            )
            return None

        # Validate token
        valid, reason = self._validate_token(token_record, submitted_token)

        if not valid:
            _talk_post(
                self.env, room_token,
                f"@{actor}: Token validation failed — {reason}. "
                "Request a new token if yours expired."
            )
            return None

        # Record response
        action["responses"][actor] = {
            "action": intent,
            "timestamp": _now_iso(),
        }
        token_record["used"] = True

        # Check if any rejection immediately resolves
        if intent == "reject":
            action["status"] = "rejected"
            action["outcome"] = {
                "result": "rejected",
                "by": actor,
                "at": _now_iso(),
            }
            _save_state(state)
            _talk_post(
                self.env, room_token,
                f"REJECTED by {actor} at {action['responses'][actor]['timestamp'][:16]}Z. "
                "Action cancelled. All participants notified."
            )
            self._notify_rejection(action, matching_action_id, actor)
            return {"status": "rejected", "action_id": matching_action_id, "by": actor}

        # Check quorum (for approve)
        quorum_reached = self._check_quorum(action)

        _save_state(state)

        if quorum_reached:
            approver_names = [
                f"{r_actor} ({v['timestamp'][:16]}Z)"
                for r_actor, v in action["responses"].items()
                if v["action"] == "approve"
            ]
            action["status"] = "approved"
            action["outcome"] = {
                "result": "approved",
                "by": list(action["responses"].keys()),
                "at": _now_iso(),
            }
            _save_state(state)
            _talk_post(
                self.env, room_token,
                f"APPROVED by {', '.join(approver_names)}. Executing."
            )
            return {
                "status": "approved",
                "action_id": matching_action_id,
                "approvers": list(action["responses"].keys()),
            }

        # Quorum not yet reached — acknowledge and wait
        remaining = [
            a for a in action["required_approvers"]
            if a not in action["responses"]
        ]
        _talk_post(
            self.env, room_token,
            f"@{actor} approved. Waiting for: {', '.join(remaining)}."
        )
        return {"status": "pending", "action_id": matching_action_id, "approved_by": actor}

    # ---------------------------------------------------------------
    # INTERNAL HELPERS
    # ---------------------------------------------------------------

    def _validate_token(self, record: dict, submitted: str) -> tuple[bool, str]:
        if record.get("used"):
            return False, "token already used"
        expires_at = datetime.fromisoformat(record["expires_at"])
        if datetime.now(timezone.utc) > expires_at:
            return False, "token expired"
        expected_hash = record["hash"]
        submitted_hash = hashlib.sha256(submitted.encode()).hexdigest()
        if submitted_hash != expected_hash:
            return False, "invalid token"
        return True, "ok"

    def _check_quorum(self, action: dict) -> bool:
        approvals = [
            k for k, v in action["responses"].items()
            if v["action"] == "approve"
        ]
        required = action["required_approvers"]
        quorum = action.get("quorum", "unanimous")

        if quorum == "unanimous":
            return set(approvals) == set(required)
        elif quorum == "majority":
            return len(approvals) > len(required) / 2
        elif quorum == "any-one":
            return len(approvals) >= 1
        elif quorum == "named":
            # All required approvers must approve
            return set(approvals) >= set(required)
        return False

    def _notify_rejection(self, action: dict, action_id: str, rejector: str) -> None:
        """Notify all participants of a rejection."""
        room_token = action.get("room_token", "")
        if not room_token:
            return
        participants = set(action["required_approvers"]) | {action.get("requester", "")}
        participants.discard(rejector)
        names = ", ".join(f"@{p}" for p in participants if p)
        if names:
            _talk_post(
                self.env, room_token,
                f"Notifying participants: {names} — action was rejected by @{rejector}."
            )

    # ---------------------------------------------------------------
    # STATUS / QUERY
    # ---------------------------------------------------------------

    def get_status(self, action_id: str) -> Optional[dict]:
        """Return current status of an action."""
        state = _load_state()
        return state["actions"].get(action_id)

    def list_pending(self, room_token: str = "") -> list:
        """List all pending actions, optionally filtered by room."""
        state = _load_state()
        pending = []
        for action_id, action in state["actions"].items():
            if action["status"] == "pending":
                if not room_token or action.get("room_token") == room_token:
                    pending.append({"action_id": action_id, **action})
        return pending

    def expire_stale(self) -> int:
        """
        Mark any pending actions as expired if past deadline or 24h old with no activity.
        Returns count of expired actions.
        """
        state = _load_state()
        expired_count = 0
        now = datetime.now(timezone.utc)

        for action_id, action in state["actions"].items():
            if action["status"] != "pending":
                continue

            deadline = action.get("deadline")
            if deadline:
                if now > datetime.fromisoformat(deadline):
                    action["status"] = "expired"
                    action["outcome"] = {"result": "expired", "at": _now_iso()}
                    expired_count += 1
                    if action.get("room_token") and self.env.get("NEXTCLOUD_URL"):
                        _talk_post(
                            self.env, action["room_token"],
                            f"EXPIRED: Action '{action['description'][:60]}' — "
                            "quorum not reached before deadline. Action cancelled."
                        )

        if expired_count:
            _save_state(state)
        return expired_count


# ---------------------------------------------------------------
# CLI — for testing and manual approval management
# ---------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Servetus approval manager")
    subparsers = parser.add_subparsers(dest="command")

    # propose
    p = subparsers.add_parser("propose", help="Propose a new approval action")
    p.add_argument("--description", required=True)
    p.add_argument("--reason", required=True)
    p.add_argument("--impact", required=True)
    p.add_argument("--requester", default="servetus")
    p.add_argument("--approvers", required=True, help="Comma-separated NC usernames")
    p.add_argument("--quorum", default="unanimous",
                   choices=["unanimous", "majority", "any-one", "named"])
    p.add_argument("--room", default="", help="NC Talk room token")
    p.add_argument("--deadline-hours", type=int)

    # token
    t = subparsers.add_parser("token", help="Generate token for an approver")
    t.add_argument("--action-id", required=True)
    t.add_argument("--approver", required=True)

    # status
    s = subparsers.add_parser("status", help="Show action status")
    s.add_argument("--action-id", required=True)

    # pending
    subparsers.add_parser("pending", help="List all pending actions")

    # expire
    subparsers.add_parser("expire", help="Expire stale actions")

    args = parser.parse_args()
    mgr = ApprovalManager()

    if args.command == "propose":
        action_id = mgr.propose(
            description=args.description,
            reason=args.reason,
            impact=args.impact,
            requester=args.requester,
            required_approvers=[a.strip() for a in args.approvers.split(",")],
            quorum=args.quorum,
            room_token=args.room,
            deadline_hours=args.deadline_hours,
        )
        print(f"Action ID: {action_id}")

    elif args.command == "token":
        token = mgr.get_delivery_token(args.action_id, args.approver)
        print(f"Token for {args.approver} (deliver out-of-band, never log):")
        print(f"  APPROVE: {token}")
        print(f"  REJECT:  {token}")
        print("Call mark_token_delivered() after sending.")

    elif args.command == "status":
        status = mgr.get_status(args.action_id)
        if status:
            print(json.dumps(status, indent=2, default=str))
        else:
            print(f"No action found: {args.action_id}")

    elif args.command == "pending":
        pending = mgr.list_pending()
        if pending:
            for p in pending:
                print(f"{p['action_id']}: {p['description'][:60]} [{p['quorum']}]")
        else:
            print("No pending actions.")

    elif args.command == "expire":
        count = mgr.expire_stale()
        print(f"Expired {count} stale actions.")

    else:
        parser.print_help()
