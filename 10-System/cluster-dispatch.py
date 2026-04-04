"""
cluster-dispatch.py — Servetus Cluster Task Writer

Import this module from any Servetus script to dispatch a task to another node.
The task is written to the vault queue and picked up by the target node's
cluster-router.py daemon on its next poll (within ~15 seconds).

Usage:
    from cluster-dispatch import dispatch

    task_id = dispatch(
        target_node="binaryranch",
        task_type="summarize",
        payload={"text": transcript, "model": "claude-haiku-4-5-20251001"},
        vault_root=Path("/vault"),
    )

Task types:
    summarize       → payload: {text, prompt?, model?, max_tokens?}
    claude-code-run → payload: {prompt, files?, model?}
    talk-send       → payload: {room_token, message}
    ping            → payload: {}  (health check)
"""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path


def dispatch(
    target_node: str,
    task_type: str,
    payload: dict,
    vault_root: Path,
    created_by: str = "wordinfilm",
) -> str:
    """
    Write a task to the cluster queue. Returns the task_id.
    The target node's cluster-router picks it up within POLL_INTERVAL seconds.
    """
    task_id = str(uuid.uuid4())[:8]
    queue_dir = vault_root / "10-System" / "cluster" / "queue"
    queue_dir.mkdir(parents=True, exist_ok=True)

    task = {
        "task_id": task_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": created_by,
        "target_node": target_node,
        "type": task_type,
        "payload": payload,
        "status": "pending",
        "claimed_by": None,
        "claimed_at": None,
    }
    (queue_dir / f"{task_id}.json").write_text(json.dumps(task, indent=2))
    return task_id


def await_result(task_id: str, vault_root: Path, timeout: int = 120):
    """
    Poll for a task result. Returns result dict or None on timeout.
    Use sparingly — cluster tasks are designed to be fire-and-forget.
    """
    import time

    result_file = vault_root / "10-System" / "cluster" / "results" / f"{task_id}.json"
    deadline = time.time() + timeout
    while time.time() < deadline:
        if result_file.exists():
            return json.loads(result_file.read_text())
        time.sleep(3)
    return None
