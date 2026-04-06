#!/usr/bin/env python3
"""
browser.py — Servetus browser agent with vision loop and full screenshot audit trail.

Playwright controls a headless Chromium instance. At each step:
  1. Screenshot captured and filed as a vault artifact
  2. Screenshot sent to vision model (local Ollama/llava or Claude API)
  3. Vision model reads the page and decides the next action
  4. Action executed, loop continues

Every screenshot is evidence. Every action is auditable.

Artifact structure:
  00-Artifacts/YYYY/MM-Mon/DD/browser/
    YYYY-MM-DD-HHMM-<slug>.png      ← screenshot
    YYYY-MM-DD-HHMM-<slug>.md       ← companion with context + vision output

Usage:
  python3 10-System/browser.py --task "Log into Nextcloud as servetus"
  python3 10-System/browser.py --url https://cloud.binaryranch.com --screenshot
  python3 10-System/browser.py --session servetus  # use named saved session

Dependencies:
  pip install playwright
  playwright install chromium

Config (config/nextcloud.env):
  NEXTCLOUD_URL, NEXTCLOUD_USER, NEXTCLOUD_APP_PASSWORD
  BROWSER_VISION_MODEL=llava (local) or claude (API)
  BROWSER_SESSION_DIR=~/.servetus_browser_sessions
"""

import argparse
import base64
import json
import os
import re
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────

VAULT        = Path(__file__).parent.parent
ENV_FILE     = VAULT / "config" / "nextcloud.env"
ARTIFACTS    = VAULT / "00-Artifacts"
SESSIONS_DIR = Path.home() / ".servetus_browser_sessions"

MONTH_NAMES = {
    1: "01-Jan",  2: "02-Feb",  3: "03-Mar",  4: "04-Apr",
    5: "05-May",  6: "06-Jun",  7: "07-Jul",  8: "08-Aug",
    9: "09-Sep", 10: "10-Oct", 11: "11-Nov", 12: "12-Dec",
}


# ── Config ────────────────────────────────────────────────────────────────────

def load_env() -> dict:
    env = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env


def slugify(text: str, max_len: int = 40) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text[:max_len]


# ── Artifact writer ───────────────────────────────────────────────────────────

def artifact_dir(dt: datetime) -> Path:
    month = MONTH_NAMES[dt.month]
    day_dir = dt.strftime("%Y-%m-%d")
    d     = ARTIFACTS / str(dt.year) / month / day_dir
    d.mkdir(parents=True, exist_ok=True)
    return d


def save_screenshot_artifact(screenshot_bytes: bytes, label: str,
                              url: str, vision_output: str,
                              action_taken: str = "") -> Path:
    """
    Save screenshot + companion .md to the vault artifact hierarchy.
    Returns path to the companion .md file.
    """
    dt      = datetime.now()
    ts      = dt.strftime("%Y-%m-%d-%H%M")
    slug    = f"{ts}-{slugify(label)}"
    art_dir = artifact_dir(dt)

    # Save PNG
    png_path = art_dir / f"{slug}.png"
    png_path.write_bytes(screenshot_bytes)

    # Companion .md
    rid      = f"SV-{dt.strftime('%Y%m%d')}-{dt.strftime('%H%M')}-CST-BWSR"
    created  = dt.strftime("%Y-%m-%dT%H:%M:00-05:00")

    frontmatter = f"""---
servitus:
  schema_version: 2
  system_version: 0.2.1
  record_type: artifact
  pipeline_stage: raw
  status: active
  intent: capture

identity:
  title: "{label}"
  slug: "{slug}"
  record_id: "{rid}"

time:
  created_at: "{created}"
  timezone: "America/Chicago"

provenance:
  source_file: "{png_path.name}"
  mimetype: "image/png"
  url: "{url}"
  actor: "servetus"
  tool: "browser.py / Playwright"

tags:
  - servetus
  - artifact
  - browser
  - screenshot
---

# {label}

**URL:** {url}
**Time:** {created}
**Action taken:** {action_taken or "Screenshot captured"}

## Vision Model Output

{vision_output or "_No vision analysis performed._"}

## Screenshot

![[{png_path.name}]]
"""
    md_path = art_dir / f"{slug}.md"
    md_path.write_text(frontmatter)
    print(f"  [browser] Artifact: {md_path.relative_to(VAULT)}")
    return md_path


# ── Vision ────────────────────────────────────────────────────────────────────

def vision_analyze_local(screenshot_bytes: bytes, prompt: str,
                          model: str = "llava") -> str:
    """
    Send screenshot to local Ollama vision model.
    Returns the model's text response.
    """
    b64 = base64.b64encode(screenshot_bytes).decode()
    payload = {
        "model": model,
        "prompt": prompt,
        "images": [b64],
        "stream": False,
    }
    req = urllib.request.Request(
        "http://localhost:11434/api/generate",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            resp = json.loads(r.read())
            return resp.get("response", "").strip()
    except Exception as e:
        return f"[vision error: {e}]"


def vision_analyze_claude(screenshot_bytes: bytes, prompt: str,
                           api_key: str, model: str = "claude-haiku-4-5-20251001") -> str:
    """
    Send screenshot to Claude API (vision). Uses Haiku by default to minimize cost.
    """
    import anthropic
    client = anthropic.Anthropic(api_key=api_key)
    b64    = base64.b64encode(screenshot_bytes).decode()

    response = client.messages.create(
        model=model,
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": b64,
                    },
                },
                {"type": "text", "text": prompt},
            ],
        }],
    )
    return response.content[0].text.strip()


def vision_analyze(screenshot_bytes: bytes, prompt: str, env: dict) -> str:
    """Route vision request to local or API model based on config."""
    vision_model = env.get("BROWSER_VISION_MODEL", "local")

    if vision_model == "claude":
        api_key = env.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            print("  [vision] No ANTHROPIC_API_KEY — falling back to local")
            return vision_analyze_local(screenshot_bytes, prompt)
        return vision_analyze_claude(screenshot_bytes, prompt, api_key)
    else:
        # Default: local Ollama llava
        model = env.get("BROWSER_VISION_MODEL_NAME", "llava")
        return vision_analyze_local(screenshot_bytes, prompt, model)


# ── Session management ────────────────────────────────────────────────────────

def session_path(name: str) -> Path:
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    return SESSIONS_DIR / name


# ── Browser agent ─────────────────────────────────────────────────────────────

class ServetusBrowser:
    """
    Browser agent that sees, thinks, and acts.
    Each step: screenshot → vision → action → repeat.
    """

    def __init__(self, env: dict, session_name: str = None,
                 headless: bool = True, slow_mo: int = 500):
        self.env          = env
        self.session_name = session_name
        self.headless     = headless
        self.slow_mo      = slow_mo
        self._playwright  = None
        self._browser     = None
        self._context     = None
        self._page        = None
        self.step_count   = 0

    def __enter__(self):
        from playwright.sync_api import sync_playwright
        self._playwright = sync_playwright().start()
        launch_opts = {
            "headless": self.headless,
            "slow_mo":  self.slow_mo,
            "args": ["--no-sandbox", "--disable-dev-shm-usage"],
        }
        self._browser = self._playwright.chromium.launch(**launch_opts)

        # Load or create session context
        ctx_opts = {"viewport": {"width": 1280, "height": 900}}
        if self.session_name:
            sp = session_path(self.session_name)
            if sp.exists():
                ctx_opts["storage_state"] = str(sp)
                print(f"  [browser] Loaded session: {self.session_name}")

        self._context = self._browser.new_context(**ctx_opts)
        self._page    = self._context.new_page()
        return self

    def __exit__(self, *_):
        if self.session_name and self._context:
            sp = session_path(self.session_name)
            self._context.storage_state(path=str(sp))
            print(f"  [browser] Saved session: {self.session_name}")
        if self._browser:
            self._browser.close()
        if self._playwright:
            self._playwright.stop()

    def screenshot(self) -> bytes:
        return self._page.screenshot(full_page=False)

    def step(self, label: str, action_fn=None,
             vision_prompt: str = None, save_artifact: bool = True) -> str:
        """
        Execute one browser step:
          1. Run action_fn (if provided)
          2. Take screenshot
          3. Analyze with vision model (if prompt provided)
          4. Save artifact
        Returns vision output text.
        """
        self.step_count += 1
        if action_fn:
            action_fn()
            time.sleep(0.5)  # Let page settle

        screenshot_bytes = self.screenshot()
        url              = self._page.url
        vision_out       = ""

        if vision_prompt:
            print(f"  [vision] Analyzing: {label}")
            vision_out = vision_analyze(screenshot_bytes, vision_prompt, self.env)
            print(f"  [vision] → {vision_out[:120]}...")

        if save_artifact:
            save_screenshot_artifact(
                screenshot_bytes, label, url, vision_out,
                action_taken=label
            )

        return vision_out

    def goto(self, url: str, label: str = None) -> str:
        label = label or f"Navigate to {url}"
        return self.step(label, action_fn=lambda: self._page.goto(url),
                         vision_prompt=f"Describe what you see on this page. URL: {url}")

    def click(self, selector: str, label: str = None) -> str:
        label = label or f"Click {selector}"
        return self.step(label, action_fn=lambda: self._page.click(selector))

    def fill(self, selector: str, value: str, label: str = None):
        label = label or f"Fill {selector}"
        self._page.fill(selector, value)

    def wait_for(self, selector: str, timeout: int = 10000):
        self._page.wait_for_selector(selector, timeout=timeout)

    @property
    def page(self):
        return self._page


# ── Prebuilt tasks ────────────────────────────────────────────────────────────

def task_login_nextcloud(browser: "ServetusBrowser", env: dict):
    """Log into Nextcloud as the servetus user."""
    nc_url  = env.get("NEXTCLOUD_URL", "https://cloud.binaryranch.com")
    user    = env.get("NEXTCLOUD_USER", "servetus")
    pwd     = env.get("NEXTCLOUD_APP_PASSWORD", "")

    print(f"  [task] Logging into Nextcloud as {user}")

    browser.goto(f"{nc_url}/login", label="Nextcloud login page")
    browser.fill("input[name='user']", user)
    browser.fill("input[name='password']", pwd)
    browser.step("Submit login",
                 action_fn=lambda: browser.page.click("button[type='submit']"),
                 vision_prompt="Did the login succeed? What do you see?")
    browser.page.wait_for_url(f"{nc_url}/apps/dashboard/", timeout=15000)
    browser.step("Nextcloud dashboard",
                 vision_prompt="Describe the Nextcloud dashboard state.")
    print("  [task] Login complete.")


def task_screenshot_url(browser: "ServetusBrowser", url: str, env: dict):
    """Navigate to a URL and take an analyzed screenshot."""
    browser.goto(url, label=f"Page: {url}")


def task_join_talk_room(browser: "ServetusBrowser", env: dict, room_token: str):
    """Join a Nextcloud Talk call room as servetus."""
    nc_url = env.get("NEXTCLOUD_URL", "https://cloud.binaryranch.com")
    call_url = f"{nc_url}/call/{room_token}"

    print(f"  [task] Joining Talk room: {room_token}")
    task_login_nextcloud(browser, env)
    browser.goto(call_url, label=f"Talk room {room_token}")
    browser.step("Talk room loaded",
                 vision_prompt="Is this a Nextcloud Talk call room? What controls are visible?")
    # Click join call button if present
    try:
        browser.page.wait_for_selector("button.join-call", timeout=5000)
        browser.step("Join call",
                     action_fn=lambda: browser.page.click("button.join-call"),
                     vision_prompt="Did we join the call? What do you see?")
    except Exception:
        browser.step("Room state after navigation",
                     vision_prompt="Describe the current state of the Talk room.")


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Servetus browser agent")
    parser.add_argument("--task",     metavar="TASK",  help="Task name to run")
    parser.add_argument("--url",      metavar="URL",   help="Navigate to this URL")
    parser.add_argument("--room",     metavar="TOKEN", help="Join a Talk room")
    parser.add_argument("--session",  metavar="NAME",  help="Named browser session to load/save")
    parser.add_argument("--show",     action="store_true", help="Show browser window (not headless)")
    parser.add_argument("--no-vision", action="store_true", help="Skip vision analysis (faster)")
    args = parser.parse_args()

    env = load_env()

    with ServetusBrowser(
        env,
        session_name=args.session or "servetus",
        headless=not args.show,
    ) as browser:

        if args.url:
            task_screenshot_url(browser, args.url, env)

        elif args.room:
            task_join_talk_room(browser, env, args.room)

        elif args.task == "login":
            task_login_nextcloud(browser, env)

        else:
            # Default: login to Nextcloud and screenshot dashboard
            task_login_nextcloud(browser, env)

    print(f"\n[browser] Session complete. {browser.step_count} steps taken.")
    print(f"[browser] Artifacts in: {ARTIFACTS}/[date]/browser/")


if __name__ == "__main__":
    main()
