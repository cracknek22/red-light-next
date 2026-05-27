# Red Light Next

Safe rebuild of the Red Light Kodi add-on.

## Features

- **No exec()/eval()**: Secure dispatch-table routing and JSON serialization only
- **SHA256-verified updater**: Automatic updates with hash verification and rollback
- **Parallel scraping**: ThreadPoolExecutor with cancellation support
- **Real-Debrid support**: Built-in provider with health checks
- **Typed settings**: Full settings dataclass with Kodi integration
- **96 tests**: Full test coverage for core modules

## Install

### Method 1: Repository ZIP (recommended)

1. Download `repository.redlightnext-1.0.0.zip`:
   https://github.com/cracknek22/red-light-next/raw/main/repo/repository.redlightnext/repository.redlightnext-1.0.0.zip

2. In Kodi: **Add-ons** → **Install from ZIP file** → Select the downloaded ZIP

3. Go to **Install from repository** → **Red Light Next Repository** → **Video add-ons** → **Red Light Next** → Install

### Method 2: Direct ZIP Install

1. Download `plugin.video.redlightnext-0.1.0.zip`:
   https://github.com/cracknek22/red-light-next/raw/main/repo/plugin.video.redlightnext/plugin.video.redlightnext-0.1.0.zip

2. In Kodi: **Add-ons** → **Install from ZIP file** → Select the downloaded ZIP

## Requirements

- Kodi 19+ (Matrix/Omega)
- `script.module.requests` addon (usually pre-installed)

## Development

```bash
# Clone
git clone https://github.com/cracknek22/red-light-next.git
cd red-light-next

# Setup venv
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Run tests
pytest -q

# Security scan
python tools/security_scan.py src tests tools
```

## Security

- Static scan blocks `exec()`, `eval()`, and bare `except: pass`
- Secret redaction for API tokens in logs
- Safe ZIP extraction with path traversal protection
- SHA256 hash verification for all updates

## Architecture

- `core/`: Pure Python, no Kodi imports
- `kodi/`: Thin adapter layer
- `providers/`: Debrid provider implementations
- `scraping/`: Source orchestration
- `updater/`: Safe update manager
- `ui/`: Wizard and diagnostic contracts
