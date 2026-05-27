from __future__ import annotations

import zipfile
from pathlib import Path

from redlight_next.core.errors import UnsafeArchiveError


def _target_path(destination: Path, member_name: str) -> Path:
    destination_resolved = destination.resolve()
    target = (destination / member_name).resolve()
    try:
        target.relative_to(destination_resolved)
    except ValueError as exc:
        raise UnsafeArchiveError(f"Unsafe archive path: {member_name}") from exc
    return target


def validate_zip_members(zip_path: str | Path, required_prefix: str | None = None) -> list[str]:
    """Validate ZIP members and return safe member names."""
    names: list[str] = []
    with zipfile.ZipFile(zip_path) as archive:
        for info in archive.infolist():
            name = info.filename
            if not name or name.startswith(("/", "\\")) or "\x00" in name:
                raise UnsafeArchiveError(f"Unsafe archive path: {name!r}")
            parts = Path(name).parts
            if ".." in parts:
                raise UnsafeArchiveError(f"Unsafe archive path: {name}")
            if required_prefix and not name.startswith(required_prefix):
                raise UnsafeArchiveError(f"Archive member outside required prefix: {name}")
            names.append(name)
    return names


def safe_extract_zip(zip_path: str | Path, destination: str | Path, required_prefix: str | None = None) -> list[Path]:
    """Extract a ZIP after rejecting path traversal and wrong-prefix entries."""
    destination_path = Path(destination)
    destination_path.mkdir(parents=True, exist_ok=True)
    extracted: list[Path] = []
    with zipfile.ZipFile(zip_path) as archive:
        validate_zip_members(zip_path, required_prefix=required_prefix)
        for info in archive.infolist():
            target = _target_path(destination_path, info.filename)
            if info.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(info) as source, open(target, "wb") as output:
                output.write(source.read())
            extracted.append(target)
    return extracted
