# -*- coding: utf-8 -*-
"""Red Light Next - Kodi plugin entry point."""

from __future__ import annotations

import sys
import urllib.parse
from pathlib import Path

# Add lib directory to path for Kodi
addon_dir = Path(__file__).parent
sys.path.insert(0, str(addon_dir / "lib"))

from redlight_next.core.router import Router, RouteResult
from redlight_next.core.errors import RouteNotFoundError
from redlight_next.kodi.adapter import KodiListItem, ListItemInfo, Artwork


def get_params() -> dict:
    """Parse Kodi plugin URL parameters."""
    params = {}
    if len(sys.argv) >= 2:
        param_string = sys.argv[2]
        if param_string.startswith("?"):
            param_string = param_string[1:]
        params = dict(urllib.parse.parse_qsl(param_string))
    return params


def build_routes() -> Router:
    """Build the route dispatch table."""
    from redlight_next.ui.navigator import main_menu, movies_menu, settings_menu

    return Router({
        "navigator.main": main_menu,
        "navigator.movies": movies_menu,
        "navigator.settings": settings_menu,
    })


def run() -> None:
    """Main entry point called by Kodi."""
    params = get_params()
    mode = params.get("mode", "navigator.main")

    router = build_routes()

    try:
        result = router.dispatch(mode, params)
    except RouteNotFoundError:
        # Fallback to main menu
        result = router.dispatch("navigator.main", params)

    # Result should be a list of KodiListItems or None
    if result.value is not None:
        # Render items via Kodi adapter
        pass


if __name__ == "__main__":
    run()
