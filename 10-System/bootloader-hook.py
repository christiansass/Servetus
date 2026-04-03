#!/usr/bin/env python3
"""
bootloader-hook.py — SessionStart hook for Servetus vault.

Reads all bootloader-required specs and injects them as additionalContext
so Claude receives the full operating environment before processing any input.
This is the mechanical enforcement of the bootloader — Claude does not get
to skip it.
"""
import json
from pathlib import Path

VAULT = Path(__file__).parent.parent

# Order matches bootloader load sequence
SPECS = [
    "Toolkit/S00.01-00-00-servetus-bootloader.md",
    "Toolkit/S00.01-10-90-session-start.md",
    "Toolkit/S00.01-04-00-servetus-behavioral-rules.md",
    "Toolkit/S00.01-05-00-servetus-guardrails.md",
    "Toolkit/S00.01-03-00-servetus-vault-search.md",
    "Toolkit/S00.01-06-00-servetus-disclosure-spec.md",
    "Toolkit/S00.01-01-00-servetus-export-rules.md",
    "Toolkit/S00.01-02-00-servetus-frontmatter-schema.md",
    "Toolkit/S00.01-02-10-servetus-time-rules.md",
    "Toolkit/S00.01-02-20-servetus-spelling-rules.md",
    "Toolkit/S00.01-01-10-servetus-topic-segmentation.md",
    "Toolkit/S00.01-01-20-servetus-sorting-and-placement-protocol.md",
    "config/projects.md",
    "config/overrides.md",
    "10-System/last-session-brief.md",
    "10-System/hopper-events.log",
    "10-System/hopper-cursor.txt",
]

parts = []
for rel in SPECS:
    path = VAULT / rel
    if path.exists():
        content = path.read_text().strip()
        if content:
            parts.append(f"=== {rel} ===\n{content}")

context = "\n\n".join(parts)

header = (
    "SERVETUS BOOTLOADER — MECHANICALLY INJECTED AT SESSION START\n"
    "All operating specs are loaded below. These rules are active now.\n"
    "Do not skip, defer, or summarize them. Execute against them.\n\n"
)

print(json.dumps({
    "hookSpecificOutput": {
        "hookEventName": "SessionStart",
        "additionalContext": header + context
    }
}))
