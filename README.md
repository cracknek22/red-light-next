# Red Light Next

Safe rebuild scaffold for the Red Light Kodi add-on.

## Milestone 1

This repository currently contains the first safety scaffold:

- dispatch-table routing instead of `exec()`
- JSON serialization instead of `eval()`
- central HTTP client wrapper
- structured errors/logging
- secret redaction
- safe ZIP validation/extraction
- static security scan

## Run tests

```bash
python3 -m pytest
python3 tools/security_scan.py src tests tools
```

## Current status

Milestone 1 scaffold. Kodi adapter and provider implementations come next.
