---
type: backlog
title: "Browser Autonomy Guardrails — Domain Whitelist + Mouse Control Policy"
slug: "browser-autonomy-guardrails"
status: required-before-mouse-autonomy
priority: high
created: "2026-04-15"
circle: inner
---

# Browser Autonomy Guardrails

## Principle

Before Servetus has autonomous mouse/keyboard control of the browser, a
domain whitelist must be enforced. Servetus may only navigate to approved
domains. Any domain not on the whitelist requires an explicit admin approval
request before access is granted.

## Config File

`config/browser-policy.json` — gitignored, lives in vault config.

```json
{
  "allowed_domains": [
    "cloud.binaryranch.com",
    "binaryranch.com"
  ],
  "require_approval_for_new_domains": true,
  "approval_channel": "nextcloud-talk",
  "log_all_navigation": true
}
```

## Enforcement — Must Be Hardware/Network Level

**Servetus has zero write access to its own policy.** This is non-negotiable.

Enforcement options (in order of preference):
1. **Squid/tinyproxy** — HTTP proxy with domain ACL. Chromium routes through it.
   Servetus cannot modify proxy ACL. Admin edits the proxy config.
2. **iptables/nftables rules** — outbound traffic from the Servetus user blocked
   except to whitelisted IPs. Firewall rules live outside vault.
3. **DNS-level blocking** — Pi-hole or similar, allowlist-only mode.

Servetus requests a new domain via Talk message to admin. Admin adds it to
the proxy/firewall config. The rule enforces it — not the application layer.

A config file Servetus can read is fine for UI purposes (showing what's allowed).
A config file Servetus can write is not acceptable — that's not a guardrail.

## Mouse/Keyboard Autonomy

Mouse and keyboard control (CDP Input events) are gated behind:
1. Domain whitelist enforcement active
2. Action logging enabled (every click/keystroke recorded)
3. Admin can revoke autonomy at any time by updating policy file

## Related

- `10-System/dev-backlog/ansible-servetus-node.md`
- `Toolkit/S00.01-05-00-servetus-guardrails.md`
