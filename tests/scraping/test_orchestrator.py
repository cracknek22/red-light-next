import time
from typing import Any, List

import pytest

from redlight_next.scraping.orchestrator import (
    ScrapeFilter,
    ScrapeProgress,
    ScrapingOrchestrator,
    ScraperError,
)
from redlight_next.ui.wizard import SourceResult


class FakeScraper:
    def __init__(self, name: str, enabled: bool = True, results: List[SourceResult] = None, delay: float = 0):
        self._name = name
        self._enabled = enabled
        self._results = results or []
        self._delay = delay

    @property
    def name(self) -> str:
        return self._name

    @property
    def enabled(self) -> bool:
        return self._enabled

    def search(self, query: str, **kwargs: Any) -> List[SourceResult]:
        if self._delay:
            time.sleep(self._delay)
        return self._results


class TestScrapeFilter:
    def test_no_filter_matches_all(self):
        filt = ScrapeFilter()
        result = SourceResult(title="Movie", provider="RD", quality="1080p", size_label="1 GB")
        assert filt.matches(result) is True

    def test_debrid_only_filter(self):
        filt = ScrapeFilter(debrid_only=True)
        debrid_result = SourceResult(title="Movie", provider="RD", quality="1080p", size_label="1 GB", debrid_only=True)
        free_result = SourceResult(title="Movie", provider="Host", quality="1080p", size_label="1 GB")
        assert filt.matches(debrid_result) is True
        assert filt.matches(free_result) is False

    def test_hdr_filter(self):
        filt = ScrapeFilter(exclude_hdr=True)
        hdr = SourceResult(title="Movie", provider="RD", quality="4K", size_label="10 GB", has_hdr=True)
        sdr = SourceResult(title="Movie", provider="RD", quality="1080p", size_label="1 GB")
        assert filt.matches(hdr) is False
        assert filt.matches(sdr) is True


class TestScrapeProgress:
    def test_initial_state(self):
        p = ScrapeProgress(total_scrapers=2)
        assert p.completed == 0
        assert p.results == []
        assert not p.is_complete

    def test_add_results(self):
        p = ScrapeProgress(total_scrapers=1)
        results = [SourceResult(title="A", provider="RD", quality="1080p", size_label="1 GB")]
        p.add_results("scraper1", results)
        assert p.completed == 1
        assert len(p.results) == 1
        assert p.is_complete

    def test_add_error(self):
        p = ScrapeProgress(total_scrapers=1)
        p.add_error("scraper1", "Timeout")
        assert p.completed == 1
        assert p.errors["scraper1"] == "Timeout"

    def test_cancelled(self):
        p = ScrapeProgress(total_scrapers=1)
        p.cancelled = True
        assert p.is_complete


class TestScrapingOrchestrator:
    def test_single_scraper(self):
        results = [SourceResult(title="Movie A", provider="RD", quality="1080p", size_label="1 GB")]
        scraper = FakeScraper("test", results=results)
        orch = ScrapingOrchestrator()
        progress = orch.scrape([scraper], "test query")
        assert len(progress.results) == 1
        assert progress.results[0].title == "Movie A"

    def test_parallel_scrapers(self):
        scraper1 = FakeScraper("s1", results=[
            SourceResult(title="A", provider="RD", quality="1080p", size_label="1 GB"),
        ])
        scraper2 = FakeScraper("s2", results=[
            SourceResult(title="B", provider="PM", quality="720p", size_label="500 MB"),
        ])
        orch = ScrapingOrchestrator(max_workers=2)
        progress = orch.scrape([scraper1, scraper2], "test")
        assert len(progress.results) == 2
        titles = {r.title for r in progress.results}
        assert titles == {"A", "B"}

    def test_disabled_scraper_skipped(self):
        enabled = FakeScraper("enabled", enabled=True, results=[
            SourceResult(title="Found", provider="RD", quality="1080p", size_label="1 GB"),
        ])
        disabled = FakeScraper("disabled", enabled=False, results=[
            SourceResult(title="Lost", provider="PM", quality="1080p", size_label="1 GB"),
        ])
        orch = ScrapingOrchestrator()
        progress = orch.scrape([enabled, disabled], "test")
        assert len(progress.results) == 1
        assert progress.results[0].title == "Found"

    def test_filter_applied(self):
        scraper = FakeScraper("test", results=[
            SourceResult(title="HDR Movie", provider="RD", quality="4K", size_label="10 GB", has_hdr=True),
            SourceResult(title="SDR Movie", provider="RD", quality="1080p", size_label="1 GB"),
        ])
        filt = ScrapeFilter(exclude_hdr=True)
        orch = ScrapingOrchestrator()
        progress = orch.scrape([scraper], "test", filt=filt)
        assert len(progress.results) == 1
        assert progress.results[0].title == "SDR Movie"

    def test_error_handling(self):
        class BrokenScraper(FakeScraper):
            def search(self, query, **kwargs):
                raise RuntimeError("Network error")

        scraper = BrokenScraper("broken")
        orch = ScrapingOrchestrator()
        progress = orch.scrape([scraper], "test")
        assert len(progress.results) == 0
        assert "broken" in progress.errors
        assert "Network error" in progress.errors["broken"]

    def test_cancellation(self):
        slow = FakeScraper("slow", delay=2.0, results=[
            SourceResult(title="Late", provider="RD", quality="1080p", size_label="1 GB"),
        ])
        orch = ScrapingOrchestrator()
        orch.cancel("test_id")
        progress = orch.scrape([slow], "test", scrape_id="test_id")
        assert progress.cancelled is True

    def test_scrape_sync_convenience(self):
        results = [SourceResult(title="Quick", provider="RD", quality="1080p", size_label="1 GB")]
        scraper = FakeScraper("test", results=results)
        orch = ScrapingOrchestrator()
        out = orch.scrape_sync([scraper], "test")
        assert len(out) == 1
        assert out[0].title == "Quick"

    def test_empty_scrapers(self):
        orch = ScrapingOrchestrator()
        progress = orch.scrape([], "test")
        assert progress.results == []
        assert progress.is_complete
