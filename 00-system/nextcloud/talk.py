"""
Nextcloud Talk adapter — chat listener for Servetus.

This is the same kernel, accessed through Nextcloud Talk.
Messages come in from Talk, get processed by the Toolkit,
and responses go back through Talk.

This is one of several I/O adapters (CLI, Obsidian plugin,
Talk, system tray). All share the same interpreter.
"""

import time
import requests
from typing import Callable, Optional

from .config import NextcloudConfig


class TalkListener:
    """
    Polls a Nextcloud Talk room for new messages and dispatches them
    to a handler function (the Servetus interpreter).
    """

    def __init__(self, config: NextcloudConfig):
        self.config = config
        self.session = requests.Session()
        self.session.auth = (config.username, config.app_password)
        self.session.headers.update({
            "OCS-APIRequest": "true",
            "Accept": "application/json",
        })
        self._last_known_id = 0
        self._running = False

    def _chat_url(self) -> str:
        """API endpoint for chat messages in the configured room."""
        return (
            f"{self.config.talk_api_url}"
            f"/chat/{self.config.talk_room_token}"
        )

    def get_new_messages(self) -> list:
        """
        Fetch messages newer than the last known message ID.

        Returns list of message dicts with keys:
        id, actorId, actorDisplayName, message, timestamp
        """
        params = {
            "lookIntoFuture": 0,
            "limit": 50,
            "format": "json",
        }
        if self._last_known_id:
            params["lastKnownMessageId"] = self._last_known_id
            params["lookIntoFuture"] = 1

        try:
            response = self.session.get(self._chat_url(), params=params, timeout=30)
        except requests.ConnectionError:
            return []

        if response.status_code != 200:
            return []

        data = response.json()
        messages = data.get("ocs", {}).get("data", [])

        if messages:
            self._last_known_id = messages[-1]["id"]

        # Filter out our own messages and system messages
        return [
            m for m in messages
            if m.get("actorId") != self.config.username
            and m.get("actorType") != "bots"
            and m.get("systemMessage", "") == ""
        ]

    def send_message(self, text: str) -> bool:
        """Send a message to the Talk room."""
        response = self.session.post(
            self._chat_url(),
            json={"message": text},
        )
        return response.status_code in (200, 201)

    def listen(self, handler: Callable[[dict], Optional[str]]):
        """
        Main loop: poll for messages, dispatch to handler, send responses.

        handler receives a message dict and returns a response string
        (or None to not reply).

        This is where Talk becomes an I/O adapter for the Servetus kernel.
        The handler IS the kernel — same interpreter, different mouth.
        """
        print(f"  Listening on Talk room: {self.config.talk_room_token}")
        print(f"  Poll interval: {self.config.talk_poll_interval}s")
        print(f"  Press Ctrl+C to stop.\n")

        self._running = True

        # Get current message ID so we don't replay history
        messages = self.get_new_messages()
        if messages:
            self._last_known_id = messages[-1]["id"]

        while self._running:
            try:
                new_messages = self.get_new_messages()
                for msg in new_messages:
                    actor = msg.get("actorDisplayName", "unknown")
                    text = msg.get("message", "")
                    print(f"  [{actor}]: {text}")

                    response = handler(msg)
                    if response:
                        self.send_message(response)
                        print(f"  [Servetus]: {response[:80]}...")

                time.sleep(self.config.talk_poll_interval)

            except KeyboardInterrupt:
                self._running = False
                print("\n  Talk listener stopped.")

    def stop(self):
        """Signal the listen loop to stop."""
        self._running = False
