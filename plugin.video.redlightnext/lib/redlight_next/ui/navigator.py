from __future__ import annotations

from typing import List, Mapping

from redlight_next.kodi.adapter import KodiListItem, ListItemInfo


def main_menu(params: Mapping[str, str]) -> List[KodiListItem]:
    return [
        KodiListItem(label="Movies", path="plugin://plugin.video.redlightnext/?mode=navigator.movies", is_folder=True),
        KodiListItem(label="TV Shows", path="plugin://plugin.video.redlightnext/?mode=navigator.tvshows", is_folder=True),
        KodiListItem(label="Settings", path="plugin://plugin.video.redlightnext/?mode=navigator.settings", is_folder=True),
    ]


def movies_menu(params: Mapping[str, str]) -> List[KodiListItem]:
    return [
        KodiListItem(label="Popular", path="plugin://plugin.video.redlightnext/?mode=movies.popular", is_folder=True),
        KodiListItem(label="Search", path="plugin://plugin.video.redlightnext/?mode=movies.search", is_folder=True),
    ]


def settings_menu(params: Mapping[str, str]) -> List[KodiListItem]:
    return [
        KodiListItem(label="General", path="plugin://plugin.video.redlightnext/?mode=settings.general", is_folder=False),
        KodiListItem(label="Providers", path="plugin://plugin.video.redlightnext/?mode=settings.providers", is_folder=False),
    ]
