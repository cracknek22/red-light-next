from __future__ import annotations

from typing import Dict, List, Optional, Type

from redlight_next.providers.base import DebridProvider, ProviderHealth, ProviderStatus, ResolvedLink


class ProviderRegistry:
    """Registry for debrid/premium providers."""

    def __init__(self):
        self._providers: Dict[str, DebridProvider] = {}

    def register(self, provider: DebridProvider) -> None:
        self._providers[provider.name] = provider

    def unregister(self, name: str) -> None:
        self._providers.pop(name, None)

    def get(self, name: str) -> Optional[DebridProvider]:
        return self._providers.get(name)

    def list_enabled(self) -> List[DebridProvider]:
        return [p for p in self._providers.values() if p.enabled]

    def list_all(self) -> List[DebridProvider]:
        return list(self._providers.values())

    def health_summary(self) -> Dict[str, ProviderHealth]:
        return {name: provider.health() for name, provider in self._providers.items()}

    def resolve_first(self, magnet_or_url: str) -> Optional[ResolvedLink]:
        for provider in self.list_enabled():
            try:
                links = provider.resolve(magnet_or_url)
                if links:
                    return links[0]
            except Exception:
                continue
        return None
