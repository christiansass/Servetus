#!/usr/bin/env python3
"""
browser-control.py — Servetus browser automation via Chrome DevTools Protocol.

Provides mouse, keyboard, screenshot, and DOM interaction against the
headless Chromium instance on display :1.

DOMAIN WHITELIST: Hardcoded. Cannot be modified by this script.
To add a domain, a human must edit the ALLOWED_DOMAINS list below and
commit the change. Future enforcement will move to a network-level proxy.
"""

import json
import time
import subprocess
import urllib.request
import urllib.parse
import base64
import os
import sys
import websocket

# ─── Domain Whitelist ────────────────────────────────────────────────────────
# HUMAN-MAINTAINED. Do not modify programmatically.
# To request a new domain, send a message to the admin Talk room.

ALLOWED_DOMAINS = [
    "cloud.binaryranch.com",
    "binaryranch.com",
]

# ─── Config ──────────────────────────────────────────────────────────────────

CDP_URL = "http://localhost:9222"
SCREENSHOT_PATH = "/tmp/servetus-screen-current.png"
ENV_FILE = "/mnt/Cloud/Nextcloud/Obsidian/Servetus/config/nextcloud.env"


# ─── Core CDP Client ─────────────────────────────────────────────────────────

class BrowserControl:
    def __init__(self):
        self.ws = None
        self._msg_id = 0
        self._connect()

    def _connect(self):
        tabs = json.loads(urllib.request.urlopen(f"{CDP_URL}/json").read())
        # Find or create a page tab
        page_tabs = [t for t in tabs if t.get("type") == "page"]
        if not page_tabs:
            raise RuntimeError("No page tab found in Chromium")
        tab = page_tabs[0]
        self.tab_id = tab["id"]
        self.ws = websocket.create_connection(tab["webSocketDebuggerUrl"])

    def _send(self, method, params=None):
        self._msg_id += 1
        msg = {"id": self._msg_id, "method": method, "params": params or {}}
        self.ws.send(json.dumps(msg))
        # Drain until we get our response
        while True:
            raw = self.ws.recv()
            data = json.loads(raw)
            if data.get("id") == self._msg_id:
                if "error" in data:
                    raise RuntimeError(f"CDP error: {data['error']}")
                return data.get("result", {})

    def close(self):
        if self.ws:
            self.ws.close()

    # ─── Navigation ──────────────────────────────────────────────────────────

    def navigate(self, url):
        """Navigate to URL. Raises if domain not in whitelist."""
        parsed = urllib.parse.urlparse(url)
        domain = parsed.netloc.lstrip("www.")
        if not any(domain == d or domain.endswith("." + d) for d in ALLOWED_DOMAINS):
            raise PermissionError(
                f"Domain '{domain}' not in whitelist. "
                f"Request admin access to add it. Allowed: {ALLOWED_DOMAINS}"
            )
        return self._send("Page.navigate", {"url": url})

    def get_url(self):
        result = self._send("Runtime.evaluate", {"expression": "window.location.href"})
        return result.get("result", {}).get("value", "")

    def reload(self):
        return self._send("Page.reload", {})

    # ─── Screenshot ──────────────────────────────────────────────────────────

    def screenshot(self, path=SCREENSHOT_PATH):
        """Take screenshot, save to path, return path."""
        result = self._send("Page.captureScreenshot", {"format": "png"})
        data = base64.b64decode(result["data"])
        with open(path, "wb") as f:
            f.write(data)
        return path

    # ─── Mouse ───────────────────────────────────────────────────────────────

    def _mouse_event(self, event_type, x, y, button="left", click_count=1):
        return self._send("Input.dispatchMouseEvent", {
            "type": event_type,
            "x": x,
            "y": y,
            "button": button,
            "clickCount": click_count,
        })

    def move(self, x, y):
        return self._mouse_event("mouseMoved", x, y, button="none")

    def click(self, x, y, button="left"):
        self._mouse_event("mousePressed", x, y, button=button)
        time.sleep(0.05)
        self._mouse_event("mouseReleased", x, y, button=button)

    def double_click(self, x, y):
        self._mouse_event("mousePressed", x, y, click_count=2)
        time.sleep(0.05)
        self._mouse_event("mouseReleased", x, y, click_count=2)

    def scroll(self, x, y, delta_x=0, delta_y=-300):
        return self._send("Input.dispatchMouseEvent", {
            "type": "mouseWheel",
            "x": x,
            "y": y,
            "deltaX": delta_x,
            "deltaY": delta_y,
        })

    # ─── Keyboard ────────────────────────────────────────────────────────────

    def type_text(self, text):
        for char in text:
            self._send("Input.dispatchKeyEvent", {"type": "keyDown", "text": char})
            self._send("Input.dispatchKeyEvent", {"type": "keyUp", "text": char})

    def key(self, key_name):
        self._send("Input.dispatchKeyEvent", {"type": "keyDown", "key": key_name})
        self._send("Input.dispatchKeyEvent", {"type": "keyUp", "key": key_name})

    # ─── DOM ─────────────────────────────────────────────────────────────────

    def eval(self, expression):
        result = self._send("Runtime.evaluate", {
            "expression": expression,
            "returnByValue": True,
        })
        return result.get("result", {}).get("value")

    def find_element_coords(self, selector):
        """Return (x, y) center of first element matching CSS selector, or None."""
        js = f"""
        (function() {{
            var el = document.querySelector({json.dumps(selector)});
            if (!el) return null;
            var r = el.getBoundingClientRect();
            return {{x: r.left + r.width/2, y: r.top + r.height/2}};
        }})()
        """
        result = self._send("Runtime.evaluate", {"expression": js, "returnByValue": True})
        val = result.get("result", {}).get("value")
        if val:
            return (val["x"], val["y"])
        return None

    def find_by_text(self, text, tag="*"):
        """Return (x, y) of element containing text, or None."""
        js = f"""
        (function() {{
            var els = document.querySelectorAll({json.dumps(tag)});
            var el = Array.from(els).find(e => e.innerText && e.innerText.trim().includes({json.dumps(text)}));
            if (!el) return null;
            var r = el.getBoundingClientRect();
            return {{x: r.left + r.width/2, y: r.top + r.height/2}};
        }})()
        """
        result = self._send("Runtime.evaluate", {"expression": js, "returnByValue": True})
        val = result.get("result", {}).get("value")
        if val:
            return (val["x"], val["y"])
        return None

    def click_element(self, selector):
        """Click element by CSS selector."""
        coords = self.find_element_coords(selector)
        if coords:
            self.click(*coords)
            return True
        return False

    def click_text(self, text, tag="*"):
        """Click element containing text."""
        coords = self.find_by_text(text, tag)
        if coords:
            self.click(*coords)
            return True
        return False

    def wait_for(self, selector, timeout=10):
        """Wait until element matching selector exists. Returns True/False."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            coords = self.find_element_coords(selector)
            if coords:
                return True
            time.sleep(0.5)
        return False

    def read_text(self, selector):
        """Read innerText of element."""
        return self.eval(f'document.querySelector({json.dumps(selector)})?.innerText')

    def read_page_text(self):
        """Read visible text of entire page."""
        return self.eval("document.body.innerText")

    # ─── Auth ────────────────────────────────────────────────────────────────

    def login_nextcloud(self):
        """Log into Nextcloud as servetus using stored credentials."""
        env = {}
        with open(ENV_FILE) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    env[k.strip()] = v.strip()

        password = env.get('NEXTCLOUD_GUI_PASSSWORD', '')
        if not password:
            raise RuntimeError("NEXTCLOUD_GUI_PASSSWORD not found in env file")

        self.navigate("https://cloud.binaryranch.com/login")
        self.wait_for("input[name=user]", timeout=10)
        time.sleep(1)

        self.eval('document.querySelector("input[name=user]").value = "servetus"')
        self.eval(f'document.querySelector("input[name=password]").value = {json.dumps(password)}')
        self.click_element('input[type=submit], button[type=submit]')
        time.sleep(4)

        url = self.get_url()
        if "login" in url:
            raise RuntimeError("Login failed — still on login page")
        return url

    def ensure_logged_in(self):
        """Check if logged in, re-login if not."""
        url = self.get_url()
        if "login" in url or "binaryranch.com" not in url:
            return self.login_nextcloud()
        return url

    # ─── Talk ────────────────────────────────────────────────────────────────

    def open_talk_room(self, token):
        """Navigate to a Talk room by token."""
        self.ensure_logged_in()
        self.navigate(f"https://cloud.binaryranch.com/apps/spreed/{token}")
        time.sleep(3)

    def send_talk_message(self, token, message):
        """Open a Talk room and type + send a message."""
        self.open_talk_room(token)
        self.wait_for(".message-composer-input, [contenteditable=true]", timeout=10)
        composer = self.find_element_coords(".message-composer-input, [contenteditable=true]")
        if not composer:
            raise RuntimeError("Could not find message composer")
        self.click(*composer)
        time.sleep(0.5)
        self.type_text(message)
        time.sleep(0.3)
        self.key("Enter")

    def read_notifications(self):
        """Open notifications panel and return text content."""
        self.ensure_logged_in()
        btn = self.find_element_coords('[aria-label="Notifications"]')
        if not btn:
            return None
        self.click(*btn)
        time.sleep(1.5)
        panel = self.eval('''
            var m = document.querySelector(".header-menu--open .header-menu__content");
            m ? m.innerText : null
        ''')
        # Close panel
        self.key("Escape")
        return panel


# ─── CLI usage ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Servetus browser control")
    parser.add_argument("command", choices=[
        "screenshot", "url", "login", "notifications",
        "click", "scroll", "navigate", "talk-room"
    ])
    parser.add_argument("--x", type=float)
    parser.add_argument("--y", type=float)
    parser.add_argument("--url", type=str)
    parser.add_argument("--token", type=str)
    parser.add_argument("--out", type=str, default=SCREENSHOT_PATH)
    args = parser.parse_args()

    b = BrowserControl()

    try:
        if args.command == "screenshot":
            path = b.screenshot(args.out)
            print(f"Screenshot saved: {path}")

        elif args.command == "url":
            print(b.get_url())

        elif args.command == "login":
            url = b.login_nextcloud()
            print(f"Logged in, now at: {url}")

        elif args.command == "notifications":
            text = b.read_notifications()
            print(text or "No notifications panel found")

        elif args.command == "click":
            if args.x is None or args.y is None:
                print("--x and --y required")
                sys.exit(1)
            b.click(args.x, args.y)
            print(f"Clicked ({args.x}, {args.y})")

        elif args.command == "scroll":
            b.scroll(args.x or 400, args.y or 400)
            print("Scrolled")

        elif args.command == "navigate":
            if not args.url:
                print("--url required")
                sys.exit(1)
            b.navigate(args.url)
            print(f"Navigated to {args.url}")

        elif args.command == "talk-room":
            if not args.token:
                print("--token required")
                sys.exit(1)
            b.open_talk_room(args.token)
            b.screenshot(args.out)
            print(f"Room opened, screenshot: {args.out}")

    finally:
        b.close()
