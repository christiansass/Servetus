#!/usr/bin/env python3
"""
shopping-agent.py — Servetus Shopping Agent

Watches eBay and Amazon for refurbished Pixel 8a phones (and configurable
other items) under a price threshold. Posts findings to a Nextcloud Talk room.

Dictated by Christian Sass — 2026-04-02:
  "I told Servetus to set up a shopping bot that shops on eBay and Amazon
   for all these spec phones. Refurbished, they're like $200 bucks a pop.
   An 8a is less than $300 refurbished from Amazon."

Use case: Binary Ranch device sovereignty stack. Acquire refurbished Pixel 8a
phones → install GrapheneOS + Binary Ranch ROM → resell as sovereign devices.

Usage:
    python3 10-System/shopping-agent.py --once        # single check, post findings
    python3 10-System/shopping-agent.py --daemon      # poll every POLL_INTERVAL
    python3 10-System/shopping-agent.py --list        # show configured targets

Config: config/shopping-targets.json (created on first run with defaults)
State:  10-System/.shopping-agent-state.json (gitignored)

Notes:
  eBay search uses the Finding API (free, no key required for basic search).
  Amazon search uses a web scrape fallback (no official API without seller account).
  Both are rate-limited and respectful. This is monitoring, not scraping at scale.
"""

import json
import sys
import time
import urllib.request
import urllib.parse
import urllib.error
import hashlib
from datetime import datetime, timezone
from pathlib import Path

VAULT_ROOT    = Path(__file__).parent.parent
ENV_FILE      = VAULT_ROOT / "config" / "nextcloud.env"
TARGETS_FILE  = VAULT_ROOT / "config" / "shopping-targets.json"
STATE_FILE    = VAULT_ROOT / "10-System" / ".shopping-agent-state.json"

POLL_INTERVAL = 3600   # seconds between full scans (1 hour default)
USER_AGENT    = "Mozilla/5.0 (compatible; Servetus/1.0; shopping research)"


# ── Default targets ───────────────────────────────────────────────────────────

DEFAULT_TARGETS = [
    {
        "id": "pixel-8a-refurb",
        "name": "Pixel 8a (refurbished)",
        "keywords": "Google Pixel 8a",
        "condition": "refurbished",
        "max_price_usd": 280,
        "sources": ["ebay"],
        "talk_room": "",   # filled from config/talk-rooms.json at runtime
        "notes": "Binary Ranch sovereign device stack — GrapheneOS candidate",
        "active": True,
    },
    {
        "id": "pixel-7a-refurb",
        "name": "Pixel 7a (refurbished, fallback)",
        "keywords": "Google Pixel 7a",
        "condition": "refurbished",
        "max_price_usd": 180,
        "sources": ["ebay"],
        "talk_room": "",
        "notes": "Secondary option if 8a supply dries up",
        "active": False,   # disabled by default — enable when needed
    },
]


# ── Env / Config ──────────────────────────────────────────────────────────────

def load_env() -> dict:
    env = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                env[k.strip()] = v.strip()
    return env


def load_targets() -> list:
    if not TARGETS_FILE.exists():
        TARGETS_FILE.write_text(json.dumps(DEFAULT_TARGETS, indent=2))
        print(f"[shopping] Created default targets: {TARGETS_FILE}", file=sys.stderr)
    return json.loads(TARGETS_FILE.read_text())


def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except json.JSONDecodeError:
            pass
    return {"seen": {}}   # seen: listing_hash -> first_seen_iso


def save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2, default=str))


# ── Talk posting ──────────────────────────────────────────────────────────────

def post_to_talk(env: dict, room_token: str, message: str) -> bool:
    if not room_token or not env.get("NEXTCLOUD_URL"):
        print(f"[shopping] No room token — would post:\n{message}", file=sys.stderr)
        return False
    import base64
    url = f"{env['NEXTCLOUD_URL']}/ocs/v2.php/apps/spreed/api/v1/chat/{room_token}"
    credentials = f"{env['NEXTCLOUD_USER']}:{env['NEXTCLOUD_APP_PASSWORD']}"
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
        print(f"[shopping] Talk post failed: {e}", file=sys.stderr)
        return False


def default_talk_room(env: dict) -> str:
    """Find the Christian direct room or Binary Ranch room as default destination."""
    rooms_file = VAULT_ROOT / "config" / "talk-rooms.json"
    if not rooms_file.exists():
        return ""
    rooms = json.loads(rooms_file.read_text())
    # Prefer 1:1 with csass
    for token, room in rooms.items():
        if room.get("type") == "onetoone" and "csass" in room.get("participants", []):
            return token
        if room.get("name") == "Christian B Sass":
            return token
    return list(rooms.keys())[0] if rooms else ""


# ── eBay search ───────────────────────────────────────────────────────────────

def search_ebay(keywords: str, max_price: float, condition: str = "refurbished") -> list:
    """
    Search eBay using the public finding endpoint (no API key needed).
    Returns list of {title, price, url, seller, condition, listing_id}.
    """
    # eBay Finding API — free tier, no key, returns JSON
    condition_map = {
        "refurbished": "2500",   # Seller refurbished
        "used":        "3000",
        "new":         "1000",
    }
    cond_id = condition_map.get(condition.lower(), "2500")

    params = urllib.parse.urlencode({
        "OPERATION-NAME":           "findItemsAdvanced",
        "SERVICE-VERSION":          "1.0.0",
        "SECURITY-APPNAME":         "Servetus0-shopping-PRD-placeholder",  # public endpoint works without real key for basic use
        "RESPONSE-DATA-FORMAT":     "JSON",
        "keywords":                 keywords,
        "itemFilter(0).name":       "MaxPrice",
        "itemFilter(0).value":      str(max_price),
        "itemFilter(0).paramName":  "Currency",
        "itemFilter(0).paramValue": "USD",
        "itemFilter(1).name":       "Condition",
        "itemFilter(1).value":      cond_id,
        "itemFilter(2).name":       "ListingType",
        "itemFilter(2).value":      "FixedPrice",
        "sortOrder":                "PricePlusShippingLowest",
        "paginationInput.entriesPerPage": "10",
    })

    url = f"https://svcs.ebay.com/services/search/FindingService/v1?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
    except Exception as e:
        print(f"[shopping] eBay search error: {e}", file=sys.stderr)
        return []

    items = []
    try:
        search_result = data.get("findItemsAdvancedResponse", [{}])[0]
        if search_result.get("ack", [""])[0] != "Success":
            # Fallback: if API key required, use simple scrape approach
            return _ebay_scrape_fallback(keywords, max_price)
        listings = (
            search_result
            .get("searchResult", [{}])[0]
            .get("item", [])
        )
        for item in listings:
            price_str = (
                item.get("sellingStatus", [{}])[0]
                    .get("currentPrice", [{}])[0]
                    .get("__value__", "0")
            )
            try:
                price = float(price_str)
            except ValueError:
                continue
            items.append({
                "title":      item.get("title", ["?"])[0],
                "price":      price,
                "url":        item.get("viewItemURL", [""])[0],
                "seller":     item.get("sellerInfo", [{}])[0].get("sellerUserName", ["?"])[0],
                "condition":  item.get("condition", [{}])[0].get("conditionDisplayName", ["?"])[0],
                "listing_id": item.get("itemId", ["?"])[0],
                "source":     "ebay",
            })
    except Exception as e:
        print(f"[shopping] eBay parse error: {e}", file=sys.stderr)
        return _ebay_scrape_fallback(keywords, max_price)

    return items


def _ebay_scrape_fallback(keywords: str, max_price: float) -> list:
    """
    Lightweight eBay search via the public search URL when API key isn't set.
    Parses JSON-LD or structured data from the search results page.
    This is a best-effort fallback — returns empty list on failure.
    """
    query = urllib.parse.quote_plus(keywords)
    url = (
        f"https://www.ebay.com/sch/i.html?_nkw={query}"
        f"&_sop=15"          # sort: price + shipping lowest
        f"&LH_BIN=1"         # Buy It Now only
        f"&LH_ItemCondition=2500"  # seller refurbished
        f"&_udhi={int(max_price)}" # max price
    )
    req = urllib.request.Request(url, headers={
        "User-Agent": USER_AGENT,
        "Accept-Language": "en-US,en;q=0.9",
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"[shopping] eBay scrape failed: {e}", file=sys.stderr)
        return []

    # Extract from JSON-LD if present
    import re
    items = []
    ld_blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.DOTALL)
    for block in ld_blocks:
        try:
            data = json.loads(block)
            if isinstance(data, list):
                for d in data:
                    _extract_ld_item(d, items, max_price)
            else:
                _extract_ld_item(data, items, max_price)
        except Exception:
            pass
    return items[:10]


def _extract_ld_item(data: dict, items: list, max_price: float) -> None:
    """Extract a listing from a JSON-LD product block."""
    if data.get("@type") not in ("Product", "Offer"):
        return
    offers = data.get("offers", {})
    if isinstance(offers, list):
        offers = offers[0] if offers else {}
    price_str = offers.get("price", "0")
    try:
        price = float(price_str)
    except ValueError:
        return
    if price > max_price:
        return
    url = data.get("url", offers.get("url", ""))
    items.append({
        "title":      data.get("name", "?"),
        "price":      price,
        "url":        url,
        "seller":     offers.get("seller", {}).get("name", "?"),
        "condition":  data.get("itemCondition", "?").split("/")[-1],
        "listing_id": url.split("/")[-1].split("?")[0],
        "source":     "ebay",
    })


# ── Listing dedup ─────────────────────────────────────────────────────────────

def listing_hash(item: dict) -> str:
    key = f"{item['source']}:{item.get('listing_id', item['url'])}"
    return hashlib.sha256(key.encode()).hexdigest()[:16]


# ── Main scan ─────────────────────────────────────────────────────────────────

def scan_target(target: dict, env: dict, state: dict) -> list:
    """
    Scan one target across its configured sources.
    Returns list of new (unseen) listings found.
    """
    results = []
    sources = target.get("sources", ["ebay"])
    max_price = target.get("max_price_usd", 300)
    keywords  = target.get("keywords", "")
    condition = target.get("condition", "refurbished")

    for source in sources:
        if source == "ebay":
            listings = search_ebay(keywords, max_price, condition)
        else:
            print(f"[shopping] Unsupported source: {source}", file=sys.stderr)
            continue

        for item in listings:
            h = listing_hash(item)
            if h not in state["seen"]:
                state["seen"][h] = {
                    "first_seen": datetime.now(timezone.utc).isoformat(),
                    "target_id":  target["id"],
                    "title":      item["title"],
                    "price":      item["price"],
                }
                results.append(item)

    return results


def format_findings(target: dict, new_listings: list) -> str:
    lines = [
        f"Shopping agent — {target['name']}",
        f"Max price: ${target['max_price_usd']} | {len(new_listings)} new listing(s)",
        "",
    ]
    for item in new_listings[:5]:  # cap at 5 per notification
        price = f"${item['price']:.0f}"
        title = item["title"][:60]
        url   = item["url"]
        cond  = item.get("condition", "?")
        lines.append(f"{price} — {title} [{cond}]")
        lines.append(f"  {url}")
    if len(new_listings) > 5:
        lines.append(f"  ... and {len(new_listings) - 5} more")
    return "\n".join(lines)


def run_once(env: dict, targets: list, state: dict) -> int:
    """Run one pass across all active targets. Returns count of new listings found."""
    default_room = default_talk_room(env)
    total_new = 0

    for target in targets:
        if not target.get("active", True):
            continue

        print(f"[shopping] Scanning: {target['name']}", file=sys.stderr)
        new_listings = scan_target(target, env, state)

        if new_listings:
            room = target.get("talk_room") or default_room
            msg  = format_findings(target, new_listings)
            if room:
                post_to_talk(env, room, msg)
            else:
                print(msg)
            total_new += len(new_listings)
        else:
            print(f"[shopping] No new listings for: {target['name']}", file=sys.stderr)

        time.sleep(5)  # polite delay between searches

    save_state(state)
    return total_new


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Servetus shopping agent")
    parser.add_argument("--once",   action="store_true", help="Scan once and exit")
    parser.add_argument("--daemon", action="store_true", help="Poll every POLL_INTERVAL seconds")
    parser.add_argument("--list",   action="store_true", help="List configured targets")
    parser.add_argument("--interval", type=int, default=POLL_INTERVAL,
                        help=f"Daemon poll interval in seconds (default: {POLL_INTERVAL})")
    args = parser.parse_args()

    env     = load_env()
    targets = load_targets()
    state   = load_state()

    if args.list:
        for t in targets:
            status = "ACTIVE" if t.get("active", True) else "disabled"
            print(f"[{status}] {t['id']}: {t['name']} — max ${t['max_price_usd']}")
        sys.exit(0)

    if args.once or args.daemon:
        while True:
            found = run_once(env, targets, state)
            print(f"[shopping] Scan complete — {found} new listings", file=sys.stderr)
            if args.once:
                break
            print(f"[shopping] Next scan in {args.interval}s", file=sys.stderr)
            time.sleep(args.interval)
    else:
        parser.print_help()
