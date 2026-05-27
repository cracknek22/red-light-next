import pytest

from redlight_next.ui.wizard import (
    DiagnosticResult,
    DiagnosticStatus,
    MenuItem,
    MenuPage,
    NoResultsDiagnosis,
    ProviderBadge,
    SetupWizard,
    SourceResult,
)


class FakeAdapter:
    pass


class TestSetupWizard:
    def test_initial_step(self):
        w = SetupWizard(FakeAdapter())
        assert w.step == 0
        assert w.step_name == "welcome"
        assert not w.is_complete()

    def test_next_and_prev(self):
        w = SetupWizard(FakeAdapter())
        assert w.next() == "language"
        assert w.next() == "providers"
        assert w.prev() == "language"

    def test_complete(self):
        w = SetupWizard(FakeAdapter())
        for _ in range(len(SetupWizard.STEPS)):
            w.next()
        assert w.is_complete()

    def test_store_and_retrieve_values(self):
        w = SetupWizard(FakeAdapter())
        w.set_value("language", "nl")
        w.set_value("debug_mode", True)
        assert w.get_value("language") == "nl"
        assert w.get_value("debug_mode") is True
        assert w.get_value("missing", "default") == "default"

    def test_get_all_settings(self):
        w = SetupWizard(FakeAdapter())
        w.set_value("a", 1)
        w.set_value("b", 2)
        assert w.get_all_settings() == {"a": 1, "b": 2}


class TestDiagnosticResult:
    def test_creation(self):
        r = DiagnosticResult(
            component="real_debrid",
            status=DiagnosticStatus.PASS,
            message="OK",
        )
        assert r.component == "real_debrid"
        assert r.status == DiagnosticStatus.PASS


class TestNoResultsDiagnosis:
    def test_format_message(self):
        d = NoResultsDiagnosis(
            query="test movie",
            checked_providers=["rd", "pm"],
            active_filters={"min_quality": "1080p"},
            suggestions=["Try without filters", "Check provider tokens"],
            provider_errors={"rd": "Auth failed"},
        )
        msg = d.format_message()
        assert "test movie" in msg
        assert "Auth failed" in msg
        assert "Try without filters" in msg
        assert "1080p" in msg

    def test_no_errors(self):
        d = NoResultsDiagnosis(
            query="test",
            checked_providers=["rd"],
            active_filters={},
        )
        assert not d.has_provider_errors()


class TestSourceResult:
    def test_defaults(self):
        r = SourceResult(title="Movie", provider="RD", quality="1080p", size_label="1.5 GB")
        assert r.codec is None
        assert r.has_hdr is False
        assert r.badges == []
        assert r.seeds is None

    def test_with_badges(self):
        badge = ProviderBadge(label="HDR", color="yellow")
        r = SourceResult(
            title="Movie",
            provider="RD",
            quality="4K",
            size_label="10 GB",
            has_hdr=True,
            badges=[badge],
        )
        assert r.has_hdr is True
        assert len(r.badges) == 1
        assert r.badges[0].label == "HDR"


class TestMenuPage:
    def test_page(self):
        items = [
            MenuItem(label="Movies", action="movies", is_folder=True),
            MenuItem(label="Settings", action="settings", is_folder=False),
        ]
        page = MenuPage(title="Main Menu", items=items)
        assert page.title == "Main Menu"
        assert len(page.items) == 2
        assert page.content_type == "videos"
