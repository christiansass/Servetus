#!/usr/bin/env python3
"""
cluster-router.py — Servetus Multi-Node Task Dispatcher

Runs as a daemon on each node. Polls the vault task queue, claims tasks
targeted at this node, executes them, and writes results back to the vault.

Cluster bus (vault-native, synced via Nextcloud):
  10-System/cluster/nodes/{node}.json   — heartbeat registry
  10-System/cluster/queue/{id}.json     — pending tasks
  10-System/cluster/results/{id}.json   — completed results

Task lifecycle: pending → in-progress → done | failed

Dispatch model:
  - WordinFilm writes a task with target_node="binaryranch"
  - BinaryRanch picks it up, executes, writes result
  - No RabbitMQ, no Redis — the vault IS the bus

Node capabilities (set via NODE_CAPABILITIES env var, comma-separated):
  binaryranch:  claude-code, talk, cluster-routing
  wordinfilm:   whisper, ollama, browse, talk, cluster-routing
"""

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


# ── Config ────────────────────────────────────────────────────────

ENV_FILE   = os.environ.get("ENV_FILE", "/vault/config/nextcloud.env")
NODE_NAME  = os.environ.get("NODE_NAME", "unknown")
NODE_CAPS  = set(os.environ.get("NODE_CAPABILITIES", "").split(","))
VAULT_ROOT = Path(ENV_FILE).parent.parent if ENV_FILE else Path("/vault")

CLUSTER_DIR = VAULT_ROOT / "10-System" / "cluster"
NODES_DIR   = CLUSTER_DIR / "nodes"
QUEUE_DIR   = CLUSTER_DIR / "queue"
RESULTS_DIR = CLUSTER_DIR / "results"

POLL_INTERVAL   = 15   # seconds between queue polls
HEARTBEAT_EVERY = 60   # seconds between heartbeat writes


def load_env(env_file: str) -> dict:
    env = {}
    try:
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, _, v = line.partition("=")
                    env[k.strip()] = v.strip().strip('"').strip("'")
    except FileNotFoundError:
        pass
    return env


# ── Node Registry ─────────────────────────────────────────────────

def write_heartbeat(status: str = "online"):
    NODES_DIR.mkdir(parents=True, exist_ok=True)
    node_file = NODES_DIR / f"{NODE_NAME}.json"
    payload = {
        "node": NODE_NAME,
        "capabilities": sorted(NODE_CAPS),
        "status": status,
        "heartbeat": datetime.now(timezone.utc).isoformat(),
        "pid": os.getpid(),
    }
    node_file.write_text(json.dumps(payload, indent=2))


def read_cluster() -> list[dict]:
    """Return list of all known nodes from registry."""
    if not NODES_DIR.exists():
        return []
    nodes = []
    for f in NODES_DIR.glob("*.json"):
        try:
            nodes.append(json.loads(f.read_text()))
        except Exception:
            pass
    return nodes


# ── Task Queue ────────────────────────────────────────────────────

def scan_queue() -> list:
    """Return pending tasks targeted at this node."""
    if not QUEUE_DIR.exists():
        return []
    tasks = []
    for f in sorted(QUEUE_DIR.glob("*.json")):
        try:
            task = json.loads(f.read_text())
            task["_file"] = f
            if task.get("status") == "pending" and task.get("target_node") == NODE_NAME:
                tasks.append(task)
        except Exception:
            pass
    return tasks


def claim_task(task: dict):
    """Mark task as in-progress."""
    task_file = task["_file"]
    task["status"] = "in-progress"
    task["claimed_by"] = NODE_NAME
    task["claimed_at"] = datetime.now(timezone.utc).isoformat()
    task_file.write_text(json.dumps({k: v for k, v in task.items() if k != "_file"}, indent=2))


def complete_task(task: dict, result: dict, error: str = None):
    """Write result and mark task done or failed."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    task_id = task.get("task_id", task["_file"].stem)

    result_payload = {
        "task_id": task_id,
        "node": NODE_NAME,
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "status": "failed" if error else "done",
        "error": error,
        "result": result,
    }
    (RESULTS_DIR / f"{task_id}.json").write_text(json.dumps(result_payload, indent=2))

    task_file = task["_file"]
    task["status"] = "failed" if error else "done"
    task["completed_at"] = result_payload["completed_at"]
    task_file.write_text(json.dumps({k: v for k, v in task.items() if k != "_file"}, indent=2))


# ── Task Helpers ─────────────────────────────────────────────────

def dispatch_task(task: dict, env: dict) -> dict:
    """Route task to the appropriate handler."""
    task_type = task.get("type", "")
    payload = task.get("payload", {})

    if task_type == "claude-code-run":
        return handle_claude_run(payload, env)
    elif task_type == "talk-send":
        return handle_talk_send(payload, env)
    elif task_type == "summarize":
        return handle_summarize(payload, env)
    elif task_type == "ping":
        return {"pong": True, "node": NODE_NAME}
    else:
        raise ValueError(f"Unknown task type: {task_type!r}")


def handle_claude_run(payload: dict, env: dict) -> dict:
    """
    Run claude --print with a prompt. Captures stdout.
    payload: { prompt: str, files: [str], model: str }
    """
    prompt = payload.get("prompt", "")
    model  = payload.get("model", "claude-sonnet-4-6")
    files  = payload.get("files", [])   # vault-relative paths to include

    # Build context prefix from any referenced files
    context_parts = []
    for rel_path in files:
        fpath = VAULT_ROOT / rel_path
        if fpath.exists():
            context_parts.append(f"=== {rel_path} ===\n{fpath.read_text()}")
    full_prompt = "\n\n".join(context_parts + [prompt]) if context_parts else prompt

    api_key = env.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_API_KEY", "")
    result  = subprocess.run(
        ["claude", "--print", "--model", model, full_prompt],
        capture_output=True,
        text=True,
        env={**os.environ, "ANTHROPIC_API_KEY": api_key, "HOME": "/home/servetus"},
        timeout=300,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "claude exited non-zero")
    return {"output": result.stdout.strip()}


def handle_talk_send(payload: dict, env: dict) -> dict:
    """
    Post a message to a Nextcloud Talk room.
    payload: { room_token: str, message: str }
    """
    import requests as req

    room_token = payload["room_token"]
    message    = payload["message"]
    base_url   = env.get("NEXTCLOUD_URL", "").rstrip("/")
    user       = env.get("NEXTCLOUD_USER", "")
    password   = env.get("NEXTCLOUD_APP_PASSWORD", "")

    url = f"{base_url}/ocs/v2.php/apps/spreed/api/v1/chat/{room_token}"
    resp = req.post(
        url,
        auth=(user, password),
        headers={"OCS-APIRequest": "true", "Accept": "application/json"},
        json={"message": message},
        timeout=30,
    )
    resp.raise_for_status()
    return {"status_code": resp.status_code, "room_token": room_token}


def handle_summarize(payload: dict, env: dict) -> dict:
    """
    Summarize text via Claude API.
    payload: { text: str, prompt: str, model: str, max_tokens: int }
    """
    import anthropic

    api_key   = env.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_API_KEY", "")
    model     = payload.get("model", "claude-haiku-4-5-20251001")
    max_tok   = payload.get("max_tokens", 512)
    text      = payload.get("text", "")
    prompt    = payload.get("prompt", f"Summarize the following:\n\n{text}")

    client = anthropic.Anthropic(api_key=api_key)
    resp   = client.messages.create(
        model=model,
        max_tokens=max_tok,
        messages=[{"role": "user", "content": prompt}],
    )
    return {"summary": resp.content[0].text}


# ── Main Loop ─────────────────────────────────────────────────────

def main():
    env = load_env(ENV_FILE)

    if not NODE_NAME or NODE_NAME == "unknown":
        print("ERROR: NODE_NAME env var required", file=sys.stderr)
        sys.exit(1)

    QUEUE_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    print(f"[cluster-router] Node: {NODE_NAME} | Capabilities: {sorted(NODE_CAPS)}", flush=True)

    last_heartbeat = 0.0

    while True:
        now = time.time()

        # Heartbeat
        if now - last_heartbeat >= HEARTBEAT_EVERY:
            write_heartbeat("online")
            last_heartbeat = now

        # Poll queue
        tasks = scan_queue()
        for task in tasks:
            task_id   = task.get("task_id", task["_file"].stem)
            task_type = task.get("type", "?")
            print(f"[cluster-router] Claiming task {task_id} ({task_type})", flush=True)
            claim_task(task)
            try:
                result = dispatch_task(task, env)
                complete_task(task, result)
                print(f"[cluster-router] Task {task_id} done", flush=True)
            except Exception as exc:
                complete_task(task, {}, error=str(exc))
                print(f"[cluster-router] Task {task_id} FAILED: {exc}", flush=True)

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
