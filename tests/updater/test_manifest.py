import shutil
from pathlib import Path

import pytest

from redlight_next.core.http import HTTPClient, HTTPResponse
from redlight_next.updater.manifest import (
    FileHash,
    UpdateError,
    UpdateManifest,
    UpdateManager,
    sha256_file,
)


class TestSha256File:
    def test_hash_known_content(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("hello")
        h = sha256_file(f)
        assert h == "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"

    def test_hash_empty_file(self, tmp_path):
        f = tmp_path / "empty.txt"
        f.write_text("")
        h = sha256_file(f)
        assert h == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"


class TestUpdateManifest:
    def test_verify_pass(self, tmp_path):
        f = tmp_path / "addon.py"
        f.write_text("print('hello')")
        h = sha256_file(f)
        manifest = UpdateManifest(
            version="1.0.0",
            addon_id="plugin.video.test",
            download_url="http://example.com/update.zip",
            published_at="2024-01-01",
            files=[FileHash(path="addon.py", sha256=h)],
        )
        assert manifest.verify(tmp_path) == []

    def test_verify_fail_wrong_hash(self, tmp_path):
        f = tmp_path / "addon.py"
        f.write_text("print('hello')")
        manifest = UpdateManifest(
            version="1.0.0",
            addon_id="plugin.video.test",
            download_url="http://example.com/update.zip",
            published_at="2024-01-01",
            files=[FileHash(path="addon.py", sha256="0000000000000000000000000000000000000000000000000000000000000000")],
        )
        failed = manifest.verify(tmp_path)
        assert "addon.py" in failed

    def test_verify_fail_missing_file(self, tmp_path):
        manifest = UpdateManifest(
            version="1.0.0",
            addon_id="plugin.video.test",
            download_url="http://example.com/update.zip",
            published_at="2024-01-01",
            files=[FileHash(path="missing.py", sha256="abc")],
        )
        failed = manifest.verify(tmp_path)
        assert "missing.py" in failed

    def test_to_dict_roundtrip(self):
        manifest = UpdateManifest(
            version="1.0.0",
            addon_id="plugin.video.test",
            download_url="http://example.com/update.zip",
            published_at="2024-01-01",
            changelog="Fixed bugs",
            files=[FileHash(path="addon.py", sha256="abc123")],
        )
        d = manifest.to_dict()
        restored = UpdateManifest.from_dict(d)
        assert restored == manifest


class FakeHTTPClient:
    def __init__(self, content=b"PK\x03\x04 fake zip"):
        self.content = content
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append(("GET", url))
        return HTTPResponse(status_code=200, text=self.content.decode("utf-8", errors="replace"), content=self.content, headers={})

    def request(self, method, url, **kwargs):
        self.calls.append((method, url))
        return HTTPResponse(status_code=200, text=self.content.decode("utf-8", errors="replace"), content=self.content, headers={})


class TestUpdateManager:
    def test_backup_and_restore(self, tmp_path):
        addon = tmp_path / "addon"
        addon.mkdir()
        (addon / "main.py").write_text("old")
        backup = tmp_path / "backups"
        mgr = UpdateManager(addon, backup)
        mgr.create_backup("1.0.0")
        (addon / "main.py").write_text("new")
        assert (addon / "main.py").read_text() == "new"
        mgr.restore_backup("1.0.0")
        assert (addon / "main.py").read_text() == "old"

    def test_download_and_verify_zip(self, tmp_path):
        import zipfile
        import io

        # Create a real zip file in memory
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("addon.py", "print('hello')")
        zip_bytes = zip_buffer.getvalue()

        client = FakeHTTPClient(content=zip_bytes)
        addon = tmp_path / "addon"
        addon.mkdir()
        backup = tmp_path / "backups"
        mgr = UpdateManager(addon, backup, client=client)

        manifest = UpdateManifest(
            version="1.0.0",
            addon_id="plugin.video.test",
            download_url="http://example.com/update.zip",
            published_at="2024-01-01",
            files=[FileHash(path="addon.py", sha256=sha256_file(Path("/dev/null")))],  # wrong hash
        )
        extract_dir = tmp_path / "extract"
        with pytest.raises(UpdateError) as exc_info:
            mgr.download_and_verify(manifest, extract_dir)
        assert "Hash verification failed" in str(exc_info.value)

    def test_download_and_verify_success(self, tmp_path):
        import zipfile
        import io

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("addon.py", "print('hello')")
        zip_bytes = zip_buffer.getvalue()

        client = FakeHTTPClient(content=zip_bytes)
        addon = tmp_path / "addon"
        addon.mkdir()
        backup = tmp_path / "backups"
        mgr = UpdateManager(addon, backup, client=client)

        extract_dir = tmp_path / "extract"
        extract_dir.mkdir()
        # Create the file that will be in the zip
        addon_py = extract_dir / "addon.py"
        addon_py.write_text("print('hello')")
        h = sha256_file(addon_py)
        # Remove it so extractall can recreate it
        addon_py.unlink()

        manifest = UpdateManifest(
            version="1.0.0",
            addon_id="plugin.video.test",
            download_url="http://example.com/update.zip",
            published_at="2024-01-01",
            files=[FileHash(path="addon.py", sha256=h)],
        )
        mgr.download_and_verify(manifest, extract_dir)
        assert (extract_dir / "addon.py").exists()

    def test_apply_update(self, tmp_path):
        addon = tmp_path / "addon"
        addon.mkdir()
        (addon / "main.py").write_text("old")
        (addon / "userdata").mkdir()
        (addon / "userdata" / "settings.json").write_text("user data")
        backup = tmp_path / "backups"
        mgr = UpdateManager(addon, backup)

        extract_dir = tmp_path / "extract"
        extract_dir.mkdir()
        (extract_dir / "main.py").write_text("new")
        (extract_dir / "new_file.py").write_text("new content")

        manifest = UpdateManifest(
            version="1.0.0",
            addon_id="plugin.video.test",
            download_url="http://example.com/update.zip",
            published_at="2024-01-01",
        )
        mgr.apply_update(manifest, extract_dir)
        assert (addon / "main.py").read_text() == "new"
        assert (addon / "new_file.py").read_text() == "new content"
        assert (addon / "userdata" / "settings.json").read_text() == "user data"
