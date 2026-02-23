"""
WebDAV client for Nextcloud file operations.

Handles uploading vault files to the Sovereign tier.
Uses only stdlib + requests — no heavy dependencies.
"""

import requests
from pathlib import Path
from typing import Optional

from .config import NextcloudConfig, VAULT_ROOT


class WebDAVClient:
    """Minimal WebDAV client for Nextcloud file sync."""

    def __init__(self, config: NextcloudConfig):
        self.config = config
        self.session = requests.Session()
        self.session.auth = (config.username, config.app_password)
        self.session.headers.update({
            "OCS-APIRequest": "true",
        })

    def _remote_path(self, local_path: Path) -> str:
        """Convert a local vault path to a remote WebDAV path."""
        relative = local_path.relative_to(VAULT_ROOT)
        remote_root = self.config.remote_root.rstrip("/")
        return f"{self.config.webdav_url}{remote_root}/{relative}"

    def upload(self, local_path: Path) -> bool:
        """
        Upload a single file to Nextcloud via WebDAV PUT.

        Respects trust tiers — only uploads files under allowed sync_paths.
        Returns True on success, False on failure.
        """
        relative = str(local_path.relative_to(VAULT_ROOT))

        # Trust tier enforcement: only sync allowed paths
        allowed = any(relative.startswith(sp) for sp in self.config.sync_paths)
        if not allowed:
            print(f"  BLOCKED: {relative} is not in allowed sync paths")
            return False

        remote_url = self._remote_path(local_path)

        # Ensure parent directories exist
        self._ensure_remote_dirs(local_path)

        with open(local_path, "rb") as f:
            response = self.session.put(remote_url, data=f)

        if response.status_code in (200, 201, 204):
            return True
        else:
            print(f"  Upload failed ({response.status_code}): {relative}")
            return False

    def _ensure_remote_dirs(self, local_path: Path):
        """Create remote directories via MKCOL if they don't exist."""
        relative = local_path.relative_to(VAULT_ROOT)
        parts = relative.parts[:-1]  # directories only, not the file

        remote_root = self.config.remote_root.rstrip("/")
        current = f"{self.config.webdav_url}{remote_root}"

        for part in parts:
            current = f"{current}/{part}"
            self.session.request("MKCOL", current)
            # 405 = already exists, that's fine

    def exists(self, local_path: Path) -> bool:
        """Check if a file exists on the remote via PROPFIND."""
        remote_url = self._remote_path(local_path)
        response = self.session.request("PROPFIND", remote_url, headers={"Depth": "0"})
        return response.status_code == 207

    def upload_directory(self, local_dir: Path) -> dict:
        """
        Upload all files in a directory to Nextcloud.

        Returns dict with counts: {"uploaded": N, "skipped": N, "failed": N}
        """
        counts = {"uploaded": 0, "skipped": 0, "failed": 0}

        if not local_dir.exists():
            return counts

        for file_path in sorted(local_dir.rglob("*")):
            if file_path.is_dir():
                continue
            if file_path.name.startswith("."):
                continue

            if self.upload(file_path):
                counts["uploaded"] += 1
            else:
                counts["failed"] += 1

        return counts

    def test_connection(self) -> bool:
        """Test that the Nextcloud connection works."""
        try:
            response = self.session.request(
                "PROPFIND",
                self.config.webdav_url,
                headers={"Depth": "0"},
                timeout=10,
            )
            return response.status_code == 207
        except requests.ConnectionError:
            return False
