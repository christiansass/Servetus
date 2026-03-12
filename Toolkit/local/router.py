#!/usr/bin/env python3
"""
Servetus AI Router
------------------
Local kernel for Servetus. Routes queries between:
  - local    : Ollama (default, private, never leaves machine)
  - @claude  : Claude CLI (PII scrubbed before sending)
  - @grok    : Grok API  (PII scrubbed) [stub]
  - @gemini  : Gemini API (PII scrubbed) [stub]

Auto-escalation: local queries that exceed the kernel's capability are
automatically packaged into a context bubble and routed to the configured
escalation_target (default: claude).

Routing prefixes:
  @claude <query>   → explicit Claude route
  @grok <query>     → explicit Grok route
  @gemini <query>   → explicit Gemini route
  @local <query>    → force local, no escalation
  (plain text)      → default_target with auto-escalation

Commands:
  /status   → show current config and session state
  /exit     → quit
"""

import sys
import json
import subprocess
import urllib.request
import urllib.error
import socket
import uuid
import platform
from pathlib import Path

# VAULT_ROOT is written by install.sh at deploy time
VAULT_ROOT = Path("__VAULT_ROOT__")

CONFIG_DIR      = VAULT_ROOT / "config"
SYSTEM_DIR      = VAULT_ROOT / "00-system"
TOOLKIT_DIR     = VAULT_ROOT / "Toolkit"
PII_MAP_FILE    = CONFIG_DIR / "pii_map.json"
ROUTER_CFG_FILE = CONFIG_DIR / "router_config.json"

OLLAMA_API = "http://localhost:11434/api/chat"


# ---------------------------------------------------------------------------
# Origin fingerprint — shared with servetus_cli.py
# ---------------------------------------------------------------------------

def get_os() -> str:
    """Returns a human-readable OS string. Reads /etc/os-release on Linux for distro name."""
    system = platform.system()
    if system == "Linux":
        try:
            for line in open("/etc/os-release"):
                if line.startswith("PRETTY_NAME="):
                    return line.split("=", 1)[1].strip().strip('"')
        except Exception:
            pass
        return f"Linux {platform.release()}"
    elif system == "Darwin":
        return f"macOS {platform.mac_ver()[0]}"
    elif system == "Windows":
        return f"Windows {platform.version()}"
    return system


def get_origin() -> dict:
    """
    Returns machine fingerprint: human name, MAC, outbound IP, OS.
    machine — config/overrides.md machine_name, else hostname
    mac     — primary network interface hardware address (stable across OS on dual-boot)
    ip      — outbound IP at session time (reveals network/location)
    os      — human-readable OS name (disambiguates dual-boot sessions)
    """
    machine = socket.gethostname()
    overrides = CONFIG_DIR / "overrides.md"
    if overrides.exists():
        for line in overrides.read_text().splitlines():
            stripped = line.strip()
            if stripped.startswith("machine_name:"):
                val = stripped.split(":", 1)[1].strip().strip('"').strip("'")
                if val:
                    machine = val
                break

    mac_int = uuid.getnode()
    mac = ":".join(["{:02x}".format((mac_int >> (8 * i)) & 0xff)
                    for i in reversed(range(6))])

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
    except Exception:
        ip = "unknown"

    return {"machine": machine, "mac": mac, "ip": ip, "os": get_os()}


# ---------------------------------------------------------------------------
# Kernel identity preamble — injected before Toolkit on every boot
# ---------------------------------------------------------------------------

KERNEL_PREAMBLE = """You are the Servetus kernel — a live AI operating system running on this machine.

Your directives:
- You ARE Servetus. Do not describe or analyze it — execute it.
- Process input: sort it, place it, log it, act on it per the Toolkit rules below.
- Be direct and decisive. Default to action. Ask only when genuinely ambiguous.
- Never explain what Servetus is to the user. They built it. Treat them as the operator.
- If a task exceeds your capability or requires deeper reasoning, respond with:
    ESCALATE: <one-line reason>
  on the very first line of your response. The router will handle the rest.

The Toolkit below is your operating system. Read it as live instructions, not documentation.
"""

# ---------------------------------------------------------------------------
# Complexity classifier — two-tier escalation detection
# ---------------------------------------------------------------------------

# Tier 1: pre-route heuristics (no LLM call needed)
ESCALATE_VERBS = {
    "analyze", "analyse", "synthesize", "synthesise",
    "design", "architect", "architecture",
    "evaluate", "assess", "compare",
    "strategize", "strategy", "plan",
    "recommend", "advise",
    "explain why", "explain how", "how should", "why does", "why is",
    "write a", "write me", "draft a", "draft me",
    "create a comprehensive", "build a", "implement",
}

# Tier 2: post-response uncertainty markers
UNCERTAINTY_MARKERS = [
    "i'm not sure", "i am not sure",
    "i don't know", "i do not know",
    "i cannot determine", "i can't determine",
    "i cannot answer", "i can't answer",
    "it depends", "may require",
    "insufficient information", "unclear",
    "i lack", "i don't have enough context",
    "i am a large language model",
    "i'm a large language model",
    "as an ai language model",
    "as a language model",
    "as an ai,", "as an ai assistant",
    "i am an ai", "i'm an ai",
    "i need more information",
    "i don't have real-time", "i don't have access to real-time",
    "i do not have real-time", "i do not have access to real-time",
    "beyond my", "outside my",
    "i cannot provide real", "i can't provide real",
]


class ComplexityClassifier:
    """
    Tier 1 — pre-route: classify the query before sending to Ollama.
    Tier 2 — post-response: check if the local response signals failure.
    Returns "local" or "escalate".
    """

    def classify_query(self, query: str) -> str:
        lower = query.lower()
        word_count = len(query.split())

        if word_count > 60:
            return "escalate"

        for verb in ESCALATE_VERBS:
            if verb in lower:
                return "escalate"

        # Multiple sentences with a question usually signals complexity
        if query.count("?") > 1:
            return "escalate"

        return "local"

    def check_response(self, query: str, response: str) -> str:
        # Model explicitly requested escalation
        if response.strip().upper().startswith("ESCALATE:"):
            return "escalate"

        lower_resp = response.lower()
        for marker in UNCERTAINTY_MARKERS:
            if marker in lower_resp:
                return "escalate"

        # Thin response for a substantial query
        q_words = len(query.split())
        r_words = len(response.split())
        if q_words > 15 and r_words < 15:
            return "escalate"

        return "local"


# ---------------------------------------------------------------------------
# Context bubble — packages session state for escalation handoff
# ---------------------------------------------------------------------------

class ContextBubble:
    """
    Builds a structured handoff prompt for the external LLM when the
    local kernel escalates. Includes session history, the query, and
    optionally the failed local attempt.
    """

    def __init__(self, session, query: str, reason: str = None, local_attempt: str = None):
        self.session       = session
        self.query         = query
        self.reason        = reason
        self.local_attempt = local_attempt

    def build(self, max_history_turns: int = 6) -> str:
        parts = []

        origin = get_origin()
        parts.append(
            "You are receiving a Servetus escalation.\n"
            "Servetus is a human-readable AI operating system running on a local machine. "
            "The local Ollama kernel has determined this query exceeds its capability "
            "and is handing off to you with full context.\n"
            f"Originating machine: {origin['machine']} | {origin['mac']} | {origin['ip']} | {origin['os']}"
        )

        if self.reason:
            parts.append(f"Escalation reason: {self.reason}")

        # Recent conversation history (skip system message)
        turns = [m for m in self.session.history if m["role"] in ("user", "assistant")]
        recent = turns[-(max_history_turns * 2):]
        if recent:
            history_lines = []
            for m in recent:
                label = "User" if m["role"] == "user" else "Kernel"
                # Truncate very long messages
                content = m["content"][:800] + "..." if len(m["content"]) > 800 else m["content"]
                history_lines.append(f"{label}: {content}")
            parts.append("Recent session:\n" + "\n".join(history_lines))

        if self.local_attempt and not self.local_attempt.upper().startswith("ESCALATE:"):
            parts.append(f"Local kernel attempted (insufficient):\n{self.local_attempt}")

        parts.append(f"Query requiring escalation:\n{self.query}")

        return "\n\n---\n\n".join(parts)


# ---------------------------------------------------------------------------
# Context loader — the frontal cortex
# ---------------------------------------------------------------------------

def build_context() -> tuple:
    """
    Returns (system_prompt, file_count).
    Load order: preamble → VERSION → VAULT_STRUCTURE → Toolkit → config.
    """
    parts = [KERNEL_PREAMBLE.strip()]

    version_file = SYSTEM_DIR / "VERSION"
    if version_file.exists():
        parts.append(f"# Servetus Version\n{version_file.read_text().strip()}")

    vault_structure = VAULT_ROOT / "VAULT_STRUCTURE.md"
    if vault_structure.exists():
        parts.append(vault_structure.read_text().strip())

    if TOOLKIT_DIR.exists():
        for f in sorted(TOOLKIT_DIR.glob("S*.md")):
            parts.append(f.read_text().strip())

    for name in ["overrides.md", "projects.md", "tags.md"]:
        f = CONFIG_DIR / name
        if f.exists():
            parts.append(f.read_text().strip())

    # Subtract 1 for the preamble (not a file)
    file_count = len(parts) - 1
    return "\n\n---\n\n".join(parts), file_count


# ---------------------------------------------------------------------------
# PII Scrubber / Re-hydrator
# ---------------------------------------------------------------------------

class PIIScrubber:
    def __init__(self, map_file: Path):
        self.forward = {}
        self.reverse = {}
        if map_file.exists():
            try:
                data = json.loads(map_file.read_text())
                self.forward = data.get("entities", {})
                self.reverse = {}
                for k, v in self.forward.items():
                    if v not in self.reverse:
                        self.reverse[v] = k
            except Exception as e:
                print(f"[router] Warning: could not load PII map: {e}")

    def scrub(self, text: str) -> str:
        for real, token in self.forward.items():
            text = text.replace(real, token)
        return text

    def rehydrate(self, text: str) -> str:
        for token, real in self.reverse.items():
            text = text.replace(token, real)
        return text


# ---------------------------------------------------------------------------
# Ollama session — stateful, context-aware
# ---------------------------------------------------------------------------

class OllamaSession:
    def __init__(self, model: str, system_prompt: str = None):
        self.model   = model
        self.history = []
        if system_prompt:
            self.history.append({"role": "system", "content": system_prompt})

    def chat(self, user_input: str, timeout: int = 120) -> str:
        self.history.append({"role": "user", "content": user_input})
        payload = json.dumps({
            "model":    self.model,
            "messages": self.history,
            "stream":   False,
        }).encode()

        req = urllib.request.Request(
            OLLAMA_API,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data  = json.loads(resp.read())
                reply = data["message"]["content"]
                self.history.append({"role": "assistant", "content": reply})
                return reply
        except urllib.error.URLError as e:
            return f"[ollama error] Could not reach Ollama API: {e.reason}"
        except TimeoutError:
            return "[ollama error] Query timed out."
        except Exception as e:
            return f"[ollama error] {e}"

    def pop_last_turn(self):
        """Remove the last user+assistant exchange from history."""
        if len(self.history) >= 2 and self.history[-1]["role"] == "assistant":
            self.history.pop()
        if len(self.history) >= 1 and self.history[-1]["role"] == "user":
            self.history.pop()

    def inject_turn(self, user_input: str, response: str):
        """Add a turn to history without going through Ollama (for escalated responses)."""
        self.history.append({"role": "user",      "content": user_input})
        self.history.append({"role": "assistant",  "content": response})

    @property
    def turn_count(self) -> int:
        return sum(1 for m in self.history if m["role"] == "user")

    @property
    def escalation_count(self) -> int:
        return sum(1 for m in self.history
                   if m["role"] == "assistant" and "[escalated" in m.get("content", ""))


# ---------------------------------------------------------------------------
# External backends
# ---------------------------------------------------------------------------

def query_claude(prompt: str) -> str:
    try:
        result = subprocess.run(
            ["claude", "-p", prompt],
            capture_output=True, text=True, timeout=180,
        )
        if result.returncode != 0:
            return f"[claude error] {result.stderr.strip()}"
        return result.stdout.strip()
    except FileNotFoundError:
        return "[claude error] claude CLI not found on PATH."
    except subprocess.TimeoutExpired:
        return "[claude error] Query timed out after 180s."


def query_grok(prompt: str, api_key: str = None) -> str:
    if not api_key:
        return "[grok] Not configured. Add grok_api_key to config/router_config.json."
    return "[grok] Stub not yet implemented."


def query_gemini(prompt: str, api_key: str = None) -> str:
    if not api_key:
        return "[gemini] Not configured. Add gemini_api_key to config/router_config.json."
    return "[gemini] Stub not yet implemented."


def query_external(target: str, prompt: str, config: dict) -> str:
    if target == "claude":
        return query_claude(prompt)
    elif target == "grok":
        return query_grok(prompt, config.get("grok_api_key"))
    elif target == "gemini":
        return query_gemini(prompt, config.get("gemini_api_key"))
    return f"[router] Unknown escalation target: {target}"


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

EXTERNAL = {"claude", "grok", "gemini"}
PREFIXES = {
    "@claude": "claude",
    "@grok":   "grok",
    "@gemini": "gemini",
    "@local":  "local",
}


class Router:
    def __init__(self, session: OllamaSession, config: dict):
        self.config             = config
        self.model              = config.get("local_model", "llama3.1:8b")
        self.default            = config.get("default_target", "local")
        self.escalation_target  = config.get("escalation_target", "claude")
        self.scrubber           = PIIScrubber(PII_MAP_FILE)
        self.session            = session
        self.classifier         = ComplexityClassifier()

    def _parse(self, raw: str):
        """Returns (target, query, forced).
        forced=True means the user typed an explicit @prefix — respect it, no escalation override.
        forced=False means plain text defaulted to local — escalation is allowed.
        """
        lower = raw.lower()
        for prefix, target in PREFIXES.items():
            if lower.startswith(prefix):
                return target, raw[len(prefix):].strip(), True
        return self.default, raw, False

    def _escalate(self, query: str, reason: str, local_attempt: str = None) -> str:
        bubble = ContextBubble(self.session, query, reason=reason, local_attempt=local_attempt)
        clean  = self.scrubber.scrub(bubble.build())
        raw    = query_external(self.escalation_target, clean, self.config)
        return self.scrubber.rehydrate(raw)

    def route(self, raw: str) -> tuple:
        target, query, forced = self._parse(raw)

        # Explicit external route — PII scrub, send, rehydrate, no escalation logic
        if target in EXTERNAL:
            clean    = self.scrubber.scrub(query)
            raw_resp = query_external(target, clean, self.config)
            return target, self.scrubber.rehydrate(raw_resp)

        # @local explicitly typed — force Ollama, skip all escalation
        if forced and target == "local":
            return "local", self.session.chat(query)

        # Default path — local with auto-escalation
        # Tier 1: pre-route complexity check
        if self.classifier.classify_query(query) == "escalate":
            response = self._escalate(query, reason="query complexity")
            self.session.inject_turn(query, response)
            return f"escalated→{self.escalation_target}", response

        # Try local
        local_response = self.session.chat(query)

        # Tier 2: post-response quality check
        if self.classifier.check_response(query, local_response) == "escalate":
            reason = "local response insufficient"
            if local_response.strip().upper().startswith("ESCALATE:"):
                reason = local_response.strip()[9:].split("\n")[0].strip() or reason
            self.session.pop_last_turn()
            response = self._escalate(query, reason=reason, local_attempt=local_response)
            self.session.inject_turn(query, response)
            return f"escalated→{self.escalation_target}", response

        return "local", local_response

    def log(self, user_input: str, target: str, response: str, origin: dict = None):
        cli = SYSTEM_DIR / "servetus_cli.py"
        if not cli.exists():
            return
        origin_line = ""
        if origin:
            origin_line = f"<!-- origin: {origin['machine']} | {origin['mac']} | {origin['ip']} | {origin['os']} -->\n"
        entry = f"[router/{target}]\n{origin_line}Q: {user_input}\nA: {response}"
        subprocess.run(
            [sys.executable, str(cli), "log", entry],
            capture_output=True,
        )


# ---------------------------------------------------------------------------
# Boot + REPL
# ---------------------------------------------------------------------------

def boot(config: dict) -> tuple:
    model = config.get("local_model", "llama3.1:8b")
    print("Loading Servetus context...", end=" ", flush=True)
    system_prompt, file_count = build_context()
    print(f"{file_count} files loaded.")
    session = OllamaSession(model, system_prompt)
    return session, file_count


def banner(router: Router, file_count: int, origin: dict):
    version_file = SYSTEM_DIR / "VERSION"
    version = version_file.read_text().strip() if version_file.exists() else "?"

    print(f"\n┌─ Servetus Router  v{version}")
    print(f"│  machine    : {origin['machine']}  {origin['mac']}  {origin['ip']}  {origin['os']}")
    print(f"│  kernel     : {router.model} via Ollama")
    print(f"│  context    : {file_count} files loaded")
    print(f"│  default    : {router.default}")
    print(f"│  escalates→ : {router.escalation_target}")
    print(f"│  pii map    : {len(router.scrubber.forward)} entities")
    print(f"└─ vault      : {VAULT_ROOT}")
    print()
    print("  prefixes : @claude  @grok  @gemini  @local")
    print("  commands : /status  /exit")
    print()


def cmd_status(router: Router, origin: dict):
    print(f"  machine     : {origin['machine']}")
    print(f"  mac         : {origin['mac']}")
    print(f"  ip          : {origin['ip']}")
    print(f"  os          : {origin['os']}")
    print(f"  model       : {router.model}")
    print(f"  default     : {router.default}")
    print(f"  escalates→  : {router.escalation_target}")
    print(f"  turns       : {router.session.turn_count}")
    print(f"  vault       : {VAULT_ROOT}")
    print(f"  pii map     : {len(router.scrubber.forward)} entries")


def repl(router: Router, file_count: int, origin: dict, inline: str = None):
    if inline:
        target, response = router.route(inline)
        print(f"[{target}] {response}")
        router.log(inline, target, response, origin)
        return

    banner(router, file_count, origin)

    while True:
        try:
            raw = input("servetus> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            break

        if not raw:
            continue

        if raw.startswith("/"):
            cmd = raw.lower()
            if cmd in ("/exit", "/quit"):
                print("Bye.")
                break
            elif cmd == "/status":
                cmd_status(router, origin)
            else:
                print(f"  Unknown command: {raw}")
            continue

        target, response = router.route(raw)
        print(f"\n[{target}]\n{response}\n")
        router.log(raw, target, response, origin)


def main():
    config = {}
    if ROUTER_CFG_FILE.exists():
        try:
            config = json.loads(ROUTER_CFG_FILE.read_text())
        except Exception:
            pass

    session, file_count = boot(config)
    origin = get_origin()
    router = Router(session, config)
    inline = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else None
    repl(router, file_count, origin, inline)


if __name__ == "__main__":
    main()
