from __future__ import annotations

import hashlib
import json
import os
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from redlight_next.core.errors import RedLightNextError
from redlight_next.core.http import HTTPClient
from redlight_next.core.serialization import loads_json


class UpdateError(RedLightNextError):
    pass


@dataclass(frozen=True)
class FileHash:
    """SHA256 hash for a file in an update package."""

    path: str
    sha256: str


@dataclass(frozen=True)
class UpdateManifest:
    """Update manifest for a versioned release."""

    version: str
    addon_id: str
    download_url: str
    published_at: str
    changelog: str = ""
    minimum_kodi_version: str = ""
    files: List[FileHash] = field(default_factory=list)

    def verify(self, package_dir: Path) -> List[str]:
        """Verify all file hashes in package_dir. Returns list of failed paths."""
        failed: List[str] = []
        for fh in self.files:
            file_path = package_dir / fh.path
            if not file_path.exists():
                failed.append(fh.path)
                continue
            actual = sha256_file(file_path)
            if actual != fh.sha256:
                failed.append(fh.path)
        return failed

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "addon_id": self.addon_id,
            "download_url": self.download_url,
            "published_at": self.published_at,
            "changelog": self.changelog,
            "minimum_kodi_version": self.minimum_kodi_version,
            "files": [{"path": f.path, "sha256": f.sha256} for f in self.files],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UpdateManifest":
        files = [FileHash(f["path"], f["sha256"]) for f in data.get("files", [])]
        return cls(
            version=data["version"],
            addon_id=data["addon_id"],
            download_url=data["download_url"],
            published_at=data["published_at"],
            changelog=data.get("changelog", ""),
            minimum_kodi_version=data.get("minimum_kodi_version", ""),
            files=files,
        )


def sha256_file(path: Path) -> str:
    """Compute SHA256 hex digest of file contents."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


class UpdateManager:
    """Manages update downloads with hash verification and rollback support."""

    def __init__(
        self,
        addon_path: Path,
        backup_dir: Path,
        client: Optional[Any] = None,
    ):
        self._addon_path = addon_path
        self._backup_dir = backup_dir
        self._backup_dir.mkdir(parents=True, exist_ok=True)
        self._client = client or HTTPClient(timeout=30)

    def _backup_path(self, version: str) -> Path:
        return self._backup_dir / f"backup_{version}"

    def create_backup(self, version: str) -> Path:
        """Create a backup of the current addon before updating."""
        backup = self._backup_path(version)
        if backup.exists():
            shutil.rmtree(backup)
        shutil.copytree(self._addon_path, backup, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        return backup

    def restore_backup(self, version: str) -> bool:
        """Restore a backup if update failed."""
        backup = self._backup_path(version)
        if not backup.exists():
            return False
        if self._addon_path.exists():
            shutil.rmtree(self._addon_path)
        shutil.copytree(backup, self._addon_path)
        return True

    def download_and_verify(self, manifest: UpdateManifest, extract_dir: Path) -> None:
        """Download update package and verify hashes. Raises UpdateError on failure."""
        try:
            response = self._client.get(manifest.download_url)
        except Exception as exc:
            raise UpdateError(f"Download failed: {exc}") from exc

        if response.status_code != 200:
            raise UpdateError(f"Download returned HTTP {response.status_code}")

        extract_dir.mkdir(parents=True, exist_ok=True)
        zip_path = extract_dir / "update.zip"
        response = self._client.get(manifest.download_url)
        with open(zip_path, "wb") as f:
            f.write(response.content)

        import zipfile

        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(extract_dir)

        failed = manifest.verify(extract_dir)
        if failed:
            raise UpdateError(f"Hash verification failed for files: {', '.join(failed)}")

    def apply_update(self, manifest: UpdateManifest, extract_dir: Path) -> None:
        """Apply verified update: backup current, replace with new files."""
        self.create_backup(manifest.version)

        # Remove old addon files except userdata
        for item in self._addon_path.iterdir():
            if item.name in ("userdata", ".git"):
                continue
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()

        # Copy new files
        for src in extract_dir.iterdir():
            dst = self._addon_path / src.name
            if src.is_dir():
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)
