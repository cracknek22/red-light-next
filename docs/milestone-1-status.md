# Milestone 1 Status

Status: complete.

Verified commands:

```bash
. .venv/bin/activate && pytest -q
python tools/security_scan.py src tests tools
```

Result:

```text
....................                                                     [100%]
Security scan passed
```

Implemented:

- project scaffold under `src/redlight_next`
- dispatch-table router without `exec()`
- JSON serialization helper without `eval()`
- legacy cache literal migration via `ast.literal_eval`
- central HTTP client wrapper with timeout/retry/status handling
- structured error classes
- central logging helper with secret redaction
- secret redaction helper
- safe ZIP validation/extraction with zip-slip protection
- static security scan for forbidden `exec()`, `eval()`, and bare `except: pass`
- 20 tests covering milestone 1 controls

Next milestone:

1. Add typed settings and cache repository abstraction.
2. Add provider base interface.
3. Add Kodi adapter boundary without importing Kodi in core tests.
4. Add updater manifest/hash verification.
5. Add setup wizard and diagnostic UI contracts.
