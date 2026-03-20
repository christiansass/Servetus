---
type: spec
title: "Security Scrub Protocol — Device Fingerprint Redaction"
slug: "security-scrub-protocol"
status: active
version: 1.0
created: 2026-03-20
---

# Security Scrub Protocol

Any documentation, example, template, or README that references real device
fingerprint data must be redacted before it enters a public (or controlled-tier)
git commit.

This is not optional. It is a hard gate.

---

## What Counts as Device Fingerprint Data

| Category | Examples | Risk |
|----------|----------|------|
| MAC address | `aa:bb:cc:dd:ee:ff` | Hardware identity — permanent per NIC |
| Private IP | `10.0.0.x`, `192.168.x.x` | Network topology leak |
| Hostname | `my-machine`, `BinaryRanchDev` | Machine identification |
| OS version (exact) | `Linux Mint 22.x`, `macOS 14.4.1` | Attack surface fingerprint |
| Username / homedir | `/Users/sastian/`, `~/sastian/` | Account identity |
| Serial numbers | Any hardware serial | Device tracking |
| UUIDs tied to hardware | Disk UUID, board UUID | Hardware fingerprint |

**Note:** Internal IPs (`10.x`, `192.168.x`, `172.16-31.x`) don't route on the
internet but still expose network topology. Scrub them.

---

## Approved Placeholders

Use these exact placeholders in all public documentation and examples:

| Real value | Placeholder |
|-----------|-------------|
| MAC address | `aa:bb:cc:dd:ee:ff` |
| Private IP | `10.0.0.x` |
| Hostname | `my-machine` |
| OS version | `Linux Mint 22.x` / `macOS 14.x` |
| Username | `username` |
| Home path | `/home/username/` or `~/` |
| Serial | `[SERIAL]` |

---

## When This Rule Triggers

- **Before any `git commit`** that touches README, docs, templates, or Toolkit specs
- **Before any `git push`** to a public or controlled-tier repo
- **When writing frontmatter examples** — always use placeholders, never paste from a real session
- **When ingesting session artifacts** — scrub origin block before filing to any controlled or public tier

The `origin:` frontmatter block is the highest-risk location. It is generated
automatically by `session-close.py` and contains real MAC, IP, hostname, and OS.
It belongs in **Sovereign tier only** (Nextcloud vault). Never copy it verbatim
into README, docs, or any git-tracked file.

---

## If Real Data Gets Into History

Follow the temp-clone procedure in CLAUDE.md (Rule 3 — Hard stops):

```bash
git clone /path/to/vault /tmp/servetus-scrub
cd /tmp/servetus-scrub

# Create replacements file
cat > /tmp/replacements.txt << 'EOF'
real-mac-address==>aa:bb:cc:dd:ee:ff
real-ip==>10.0.0.x
real-hostname==>my-machine
EOF

git filter-repo --replace-text /tmp/replacements.txt
git remote add origin https://github.com/christiansass/Servetus.git
git push --force origin main

# Sync live vault to rewritten history
cd /path/to/vault
git fetch origin
git reset --hard origin/main
```

**Never run `git filter-repo` in the live vault.** Nextcloud syncs deletions
immediately. Always use the temp clone.

---

## Pre-Commit Enforcement

`10-System/pre-commit-check.sh` scans staged files for fingerprint patterns
before each commit. Install it as a git hook:

```bash
ln -sf ../../10-System/pre-commit-check.sh .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

The hook will block the commit and print exactly which file and line triggered it.
