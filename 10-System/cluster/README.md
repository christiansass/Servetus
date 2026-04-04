# Servetus Cluster Bus

Vault-native task queue. Nextcloud sync IS the message bus — no Redis, no RabbitMQ.

## Directories

| Dir | Purpose |
|-----|---------|
| `nodes/` | Node heartbeat registry. Each node writes `{name}.json` every 60s. |
| `queue/` | Pending and in-progress tasks. Task files named `{task-id}.json`. |
| `results/` | Completed task output. Written by the executing node. |

## Task Schema

```json
{
  "task_id": "a1b2c3d4",
  "created_at": "2026-04-03T14:00:00Z",
  "created_by": "wordinfilm",
  "target_node": "binaryranch",
  "type": "summarize",
  "payload": { "text": "...", "model": "claude-haiku-4-5-20251001" },
  "status": "pending",
  "claimed_by": null,
  "claimed_at": null
}
```

## Task Types

| Type | Capability | Payload |
|------|-----------|---------|
| `ping` | any | `{}` |
| `summarize` | claude-code / talk | `{text, prompt?, model?, max_tokens?}` |
| `claude-code-run` | claude-code | `{prompt, files?, model?}` |
| `talk-send` | talk | `{room_token, message}` |

## Nodes

| Node | Location | Capabilities |
|------|----------|-------------|
| `wordinfilm` | Homelab / Elgin IL | whisper, ollama, browse, talk, cluster-routing |
| `binaryranch` | Colo / BinaryRanch R420 | claude-code, talk, cluster-routing |

## Dispatching a Task

```python
from cluster_dispatch import dispatch

task_id = dispatch(
    target_node="binaryranch",
    task_type="summarize",
    payload={"text": transcript},
    vault_root=Path("/vault"),
)
```

## Latency

Task pickup latency = Nextcloud sync time + cluster-router poll interval (15s).
Typical end-to-end for a cross-node task: 30–90 seconds.
