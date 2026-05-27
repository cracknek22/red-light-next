import pytest

from redlight_next.core.errors import RouteNotFoundError
from redlight_next.core.router import Router


def test_dispatch_known_route_returns_result():
    router = Router({"navigator.main": lambda params: f"hello {params['name']}"})

    result = router.dispatch("navigator.main", {"name": "Niels"})

    assert result.mode == "navigator.main"
    assert result.value == "hello Niels"


def test_dispatch_default_route_when_mode_empty():
    router = Router({"navigator.main": lambda params: "home"})

    assert router.dispatch("").value == "home"


def test_dispatch_unknown_route_raises_without_exec_fallback():
    router = Router({"navigator.main": lambda params: "home"})

    with pytest.raises(RouteNotFoundError):
        router.dispatch("__import__('os').system('echo nope')")


def test_modes_are_sorted_tuple():
    router = Router({"b": lambda p: 2, "a": lambda p: 1})

    assert router.modes == ("a", "b")
