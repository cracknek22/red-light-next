from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Protocol, Set, runtime_checkable

from redlight_next.core.errors import RedLightNextError
from redlight_next.ui.wizard import SourceResult


class ScraperError(RedLightNextError):
    pass


@runtime_checkable
class SourceScraper(Protocol):
    """Protocol for a source scraper."""

    @property
    def name(self) -> str: ...

    @property
    def enabled(self) -> bool: ...

    def search(self, query: str, **kwargs: Any) -> List[SourceResult]: ...


@dataclass(frozen=True)
class ScrapeFilter:
    """Filter criteria for scraped results."""

    min_quality: Optional[str] = None
    max_quality: Optional[str] = None
    require_hevc: bool = False
    exclude_hdr: bool = False
    exclude_dv: bool = False
    min_size_mb: Optional[int] = None
    max_size_mb: Optional[int] = None
    debrid_only: bool = False

    def matches(self, result: SourceResult) -> bool:
        if self.debrid_only and not result.debrid_only:
            return False
        if self.require_hevc and result.codec != "HEVC":
            return False
        if self.exclude_hdr and result.has_hdr:
            return False
        if self.exclude_dv and result.has_dv:
            return False
        return True


@dataclass
class ScrapeProgress:
    """Tracks progress of a scrape operation."""

    total_scrapers: int
    completed: int = 0
    results: List[SourceResult] = field(default_factory=list)
    errors: Dict[str, str] = field(default_factory=dict)
    cancelled: bool = False

    @property
    def is_complete(self) -> bool:
        return self.completed >= self.total_scrapers or self.cancelled

    def add_results(self, scraper_name: str, results: List[SourceResult]) -> None:
        if not self.cancelled:
            self.results.extend(results)
            self.completed += 1

    def add_error(self, scraper_name: str, error: str) -> None:
        self.errors[scraper_name] = error
        self.completed += 1


class ScrapingOrchestrator:
    """Orchestrates parallel scraping with cancellation support."""

    def __init__(self, max_workers: int = 4, timeout: float = 30.0):
        self._max_workers = max_workers
        self._timeout = timeout
        self._cancelled: Set[str] = set()

    def cancel(self, scrape_id: str) -> None:
        self._cancelled.add(scrape_id)

    def _is_cancelled(self, scrape_id: str) -> bool:
        return scrape_id in self._cancelled

    def _run_scraper(self, scraper: SourceScraper, query: str, scrape_id: str, **kwargs: Any) -> List[SourceResult]:
        if self._is_cancelled(scrape_id):
            return []
        if not scraper.enabled:
            return []
        return scraper.search(query, **kwargs)

    def scrape(
        self,
        scrapers: List[SourceScraper],
        query: str,
        scrape_id: str = "default",
        filt: Optional[ScrapeFilter] = None,
        **kwargs: Any,
    ) -> ScrapeProgress:
        filt = filt or ScrapeFilter()
        progress = ScrapeProgress(total_scrapers=len([s for s in scrapers if s.enabled]))

        if progress.total_scrapers == 0:
            progress.completed = 0
            return progress

        with ThreadPoolExecutor(max_workers=self._max_workers) as executor:
            futures = {
                executor.submit(self._run_scraper, s, query, scrape_id, **kwargs): s
                for s in scrapers
                if s.enabled
            }

            for future in as_completed(futures, timeout=self._timeout):
                scraper = futures[future]
                if self._is_cancelled(scrape_id):
                    progress.cancelled = True
                    break
                try:
                    results = future.result(timeout=5)
                    filtered = [r for r in results if filt.matches(r)]
                    progress.add_results(scraper.name, filtered)
                except Exception as exc:
                    progress.add_error(scraper.name, str(exc))

        # Cancel any remaining futures
        for future in futures:
            if not future.done():
                future.cancel()

        return progress

    def scrape_sync(
        self,
        scrapers: List[SourceScraper],
        query: str,
        filt: Optional[ScrapeFilter] = None,
        **kwargs: Any,
    ) -> List[SourceResult]:
        """Synchronous convenience method returning just the results."""
        progress = self.scrape(scrapers, query, filt=filt, **kwargs)
        return progress.results
