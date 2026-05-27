from __future__ import annotations

import ast
import sys
from pathlib import Path

FORBIDDEN_CALLS = {"exec", "eval"}
FORBIDDEN_EXCEPT_PASS = "bare except/pass"


def scan_file(path: Path) -> list[str]:
    issues: list[str] = []
    if path.name == "security_scan.py":
        return issues
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError as exc:
        return [f"{path}: syntax error: {exc}"]

    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in FORBIDDEN_CALLS:
            issues.append(f"{path}:{node.lineno}: forbidden {node.func.id}()")
        if isinstance(node, ast.ExceptHandler) and node.type is None:
            body = node.body
            if len(body) == 1 and isinstance(body[0], ast.Pass):
                issues.append(f"{path}:{node.lineno}: {FORBIDDEN_EXCEPT_PASS}")
    return issues


def iter_python_files(paths: list[str]):
    for raw in paths:
        path = Path(raw)
        if path.is_file() and path.suffix == ".py":
            yield path
        elif path.is_dir():
            yield from path.rglob("*.py")


def main(argv: list[str]) -> int:
    paths = argv or ["src"]
    issues: list[str] = []
    for file_path in iter_python_files(paths):
        issues.extend(scan_file(file_path))
    if issues:
        print("Security scan failed:")
        print("\n".join(issues))
        return 1
    print("Security scan passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
