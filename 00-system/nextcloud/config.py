"""
Configuration loader for Nextcloud adapter.

Reads from config/nextcloud.yaml (gitignored, Sovereign tier).
Never falls back to environment variables or hardcoded values.
If the config doesn't exist, the adapter doesn't run.
"""

from pathlib import Path
from dataclasses import dataclass

VAULT_ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG_PATH = VAULT_ROOT / "config" / "nextcloud.yaml"


@dataclass
class NextcloudConfig:
    url: str
    username: str
    app_password: str
    remote_root: str = "/Servetus"
    talk_enabled: bool = False
    talk_room_token: str = ""
    talk_poll_interval: int = 5
    sync_paths: list = None

    def __post_init__(self):
        if self.sync_paths is None:
            self.sync_paths = [
                "01-witnesses/",
                "02-daily-logs/",
                "03-events/",
                "04-projects/",
                "05-arcs/",
                "06-radar/",
                "07-storymap/",
            ]

    @property
    def webdav_url(self) -> str:
        """Full WebDAV endpoint URL."""
        base = self.url.rstrip("/")
        return f"{base}/remote.php/dav/files/{self.username}"

    @property
    def talk_api_url(self) -> str:
        """OCS Talk API base URL."""
        base = self.url.rstrip("/")
        return f"{base}/ocs/v2.php/apps/spreed/api/v1"


def load_config() -> NextcloudConfig:
    """
    Load Nextcloud configuration from config/nextcloud.yaml.

    Returns None if config file doesn't exist (adapter won't run).
    Raises ValueError if config exists but is malformed.
    """
    if not CONFIG_PATH.exists():
        return None

    try:
        import yaml
    except ImportError:
        raise ImportError(
            "PyYAML is required for Nextcloud adapter. "
            "Install with: pip install pyyaml"
        )

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    if not raw or "server" not in raw:
        raise ValueError(f"Malformed config at {CONFIG_PATH}: missing 'server' section")

    server = raw["server"]
    for key in ("url", "username", "app_password"):
        if key not in server or not server[key]:
            raise ValueError(f"Missing required config: server.{key}")

    vault = raw.get("vault", {})
    talk = raw.get("talk", {})

    return NextcloudConfig(
        url=server["url"],
        username=server["username"],
        app_password=server["app_password"],
        remote_root=vault.get("remote_root", "/Servetus"),
        talk_enabled=talk.get("enabled", False),
        talk_room_token=talk.get("room_token", ""),
        talk_poll_interval=talk.get("poll_interval", 5),
        sync_paths=raw.get("sync_paths"),
    )
