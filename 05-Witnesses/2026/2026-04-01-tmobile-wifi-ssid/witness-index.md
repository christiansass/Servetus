---
servitus:
  schema_version: 2
  record_type: witness
  pipeline_stage: raw
  status: active

identity:
  title: "T-Mobile Guest Wi-Fi — SSID Evidence, 2026-04-01"
  slug: "tmobile-wifi-ssid-2026-04-01"
  record_id: "SV-20260401-0953-CST-WIFI"

time:
  captured_at: "2026-04-01T09:53:00-05:00"
  timezone: "America/Chicago"

provenance:
  captured_by: Christian Sass
  device: iPhone
  location: Across the street from United Wireless, 3400 Broadway, Quincy, IL

linked_arcs: [tmobile-breach]
linked_events: [2026-04-01--tmobile-wifi-witness_event]
tags: [witness, t-mobile, wifi, credibility, united-wireless, quincy]
---

# Witness: T-Mobile Guest Wi-Fi SSID — 2026-04-01

Captured 2026-04-01 from across the street outside United Wireless, 3400 Broadway, Quincy, IL.
The store rep "Christian" told Christian Sass during the March 16 visit that the store had no Wi-Fi.

---

## Files

| File | Type | Time | Description |
|------|------|------|-------------|
| `IMG_0053-discovery-from-street.MP4` | Video | ~9:53 AM | Screen recording of Christian recognizing the SSID for the first time while standing across the street — the moment of discovery |
| `IMG_0054-wifi-network-list.PNG` | Screenshot | 9:54 AM | iOS Wi-Fi settings showing `tmobileguest` in the available networks list alongside neighboring businesses (Kunes Auto & RV, Wendy's, Schafer Chiropractic) — establishes location context |
| `IMG_0052-join-prompt.PNG` | Screenshot | 9:53 AM | iOS "Join tmobileguest" prompt — iPhone auto-detected and offered to join the network. **File not yet on disk — save from device.** |

---

## Evidentiary Value

1. **Directly contradicts employee statement.** Rep "Christian" stated "We don't have any" Wi-Fi during the March 16 incident (on tape). This SSID was broadcasting publicly from the same location 16 days later.

2. **Visible from across the street.** The video documents the moment of discovery at distance. The signal was strong enough to trigger an iOS join prompt — not a faint or incidental detection.

3. **Location corroborated by surrounding SSIDs.** The Wi-Fi list includes Kunes Auto & RV, Kunes Corporate, Schafer Chiropractic, Wendy's — all businesses on or near Broadway in Quincy, IL. This is independent location verification.

4. **iOS join prompt = active, joinable network.** The "Join tmobileguest" screen (IMG_0052) means iOS confirmed the network as accessible — not just visible.

---

## Outstanding

- [ ] Save IMG_0052 (join prompt) from device to this folder
- [ ] Extract EXIF/metadata from IMG_0054 to confirm device timestamp
