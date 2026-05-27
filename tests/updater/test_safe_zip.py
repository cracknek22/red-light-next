import zipfile

import pytest

from redlight_next.core.errors import UnsafeArchiveError
from redlight_next.updater.safe_zip import safe_extract_zip, validate_zip_members


def make_zip(path, members):
    with zipfile.ZipFile(path, "w") as archive:
        for name, content in members.items():
            archive.writestr(name, content)


def test_validate_zip_accepts_required_prefix(tmp_path):
    zip_path = tmp_path / "addon.zip"
    make_zip(zip_path, {"plugin.video.redlight/addon.xml": "<addon />"})

    assert validate_zip_members(zip_path, required_prefix="plugin.video.redlight/") == ["plugin.video.redlight/addon.xml"]


def test_validate_zip_blocks_dotdot_path(tmp_path):
    zip_path = tmp_path / "bad.zip"
    make_zip(zip_path, {"../evil.py": "bad"})

    with pytest.raises(UnsafeArchiveError):
        validate_zip_members(zip_path)


def test_validate_zip_blocks_wrong_prefix(tmp_path):
    zip_path = tmp_path / "bad.zip"
    make_zip(zip_path, {"other/addon.xml": "bad"})

    with pytest.raises(UnsafeArchiveError):
        validate_zip_members(zip_path, required_prefix="plugin.video.redlight/")


def test_safe_extract_zip_writes_safe_file(tmp_path):
    zip_path = tmp_path / "addon.zip"
    out = tmp_path / "out"
    make_zip(zip_path, {"plugin.video.redlight/addon.xml": "<addon />"})

    extracted = safe_extract_zip(zip_path, out, required_prefix="plugin.video.redlight/")

    assert len(extracted) == 1
    assert (out / "plugin.video.redlight" / "addon.xml").read_text() == "<addon />"
