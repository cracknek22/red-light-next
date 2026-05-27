import subprocess
import sys


def test_security_scan_passes_for_project_source():
    result = subprocess.run(
        [sys.executable, "tools/security_scan.py", "src", "tools"],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "Security scan passed" in result.stdout
