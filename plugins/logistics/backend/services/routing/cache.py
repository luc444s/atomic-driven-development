from __future__ import annotations

from dataclasses import dataclass
from time import time


@dataclass(slots=True)
class CacheEntry[T]:
    value: T
    expires_at: float


class RoutingCache:
    def __init__(self, *, ttl_seconds: int) -> None:
        self.ttl_seconds = ttl_seconds
        self._entries: dict[str, CacheEntry[object]] = {}

    def get(self, key: str) -> object | None:
        entry = self._entries.get(key)
        if entry is None:
            return None
        if entry.expires_at <= time():
            self._entries.pop(key, None)
            return None
        return entry.value

    def set(self, key: str, value: object) -> None:
        self._entries[key] = CacheEntry(value=value, expires_at=time() + self.ttl_seconds)
