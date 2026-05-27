from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Mapping, MutableMapping, Protocol, TypeVar

from redlight_next.core.errors import RouteNotFoundError

T = TypeVar("T")
RouteHandler = Callable[[Mapping[str, str]], T]


@dataclass(frozen=True)
class RouteResult:
    mode: str
    value: object


class Router:
    """Whitelist dispatch-table router for Kodi plugin modes."""

    def __init__(self, routes: Mapping[str, RouteHandler[object]]):
        self._routes: Dict[str, RouteHandler[object]] = dict(routes)

    @property
    def modes(self) -> tuple[str, ...]:
        return tuple(sorted(self._routes))

    def dispatch(self, mode: str, params: Mapping[str, str] | None = None) -> RouteResult:
        selected_mode = mode or "navigator.main"
        try:
            handler = self._routes[selected_mode]
        except KeyError as exc:
            raise RouteNotFoundError(f"Unknown route mode: {selected_mode}") from exc
        return RouteResult(mode=selected_mode, value=handler(params or {}))


def make_router(routes: Mapping[str, RouteHandler[object]]) -> Router:
    return Router(routes)
