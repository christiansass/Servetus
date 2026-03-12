---
servitus:
  schema_version: 1
  system_version: "0.2.1"
  record_type: thread_export
  pipeline_stage: distilled
  status: active
  intent: capture

identity:
  title: "UniFi Dream Machine — Port Forwarding Setup"
  slug: "unifi-dream-machine-port-forwarding"
  record_id: "SV-20251223-NOW-CST-UDM0"

time:
  created_at: "2025-12-23"
  timezone: "America/Chicago"
  source_range: "thread"

keywords:
  - unifi
  - dream-machine
  - udm
  - port-forwarding
  - networking
  - static-ip

tags:
  - chatgpt-import
  - troubleshooting
  - networking
  - infrastructure

origin:
  source_file: "2025-12-23-Network_port_forwarding_setup.md"
  source_url: "https://chatgpt.com/c/694581b0-b23c-8330-980e-f23d4501d246"
---

# UniFi Dream Machine — Port Forwarding Setup

**Source:** 2025-12-23-Network_port_forwarding_setup.md
**Date:** 2025-12-23

## Summary

Session on setting up selective port forwarding on a UniFi Dream Machine (UDM) — exposing two specific ports from an internal static IP network to the external WAN without bridging or exposing the whole network.

## Goal

- Internal network: static IP, controlled routing
- Desired: only 2 specific ports on specific devices reachable from WAN (selective ingress)
- NOT bridge mode / NOT port mirroring (those break isolation)

## Key Correction

"Punching through the switch" language leads people toward bridge mode or port mirroring, which break security isolation. The correct approach is **selective ingress port forwarding** through the UDM's WAN firewall.

## Correct Approach (UDM)

1. Assign static LAN IPs to the devices that need external access (DHCP reservation or manual)
2. Navigate: **UniFi Network → Settings → Port Forwarding**
3. Create rules: WAN port → internal device IP + port
4. Optionally restrict source IPs for tighter security

## Notes

- Full step-by-step in source file
- Works on UDM, UDM Pro, UDM SE

## Links / References

- Placement unconfirmed.
