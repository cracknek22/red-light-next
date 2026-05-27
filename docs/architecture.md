# Red Light Next Architecture

Goal: rebuild the Red Light Kodi add-on with a safer, testable architecture.

## Boundaries

- `redlight_next.core`: pure Python runtime primitives. No Kodi imports.
- `redlight_next.security`: redaction, validation, and static safety helpers.
- `redlight_next.updater`: package/update validation and safe extraction.
- Future `redlight_next.kodi`: thin Kodi adapter layer.
- Future `redlight_next.providers`: debrid/Easynews/provider implementations.
- Future `redlight_next.scraping`: source orchestration and filtering.

## Hard rules

- No `exec()` routing.
- No `eval()` data parsing.
- No `except: pass` in production source.
- All HTTP calls go through the central HTTP client.
- Secrets are redacted before logging or debug export.
- Update ZIPs are validated before extraction.

## Milestone 1 Scope

Milestone 1 creates a safe scaffold and proves the core security controls with tests:

- dispatch-table router
- JSON serialization helper with legacy migration support
- central HTTP client wrapper
- structured errors and logger
- secret redaction
- safe ZIP extraction
- static scan gate
