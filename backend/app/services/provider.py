"""Model provider seam.

The summarize feature is backed by a provider interface. In CI and local
development the fake provider runs, producing deterministic output with no
network calls. A real provider can be plugged in behind the same interface by
setting ``provider_mode`` to something other than ``fake``.
"""

from __future__ import annotations

from typing import Protocol

from app.core.config import get_settings


class SummaryProvider(Protocol):
    def summarize(self, text: str) -> str: ...


class FakeProvider:
    """Deterministic provider used for tests and local runs.

    Produces the first sentence plus a word count, so the output is stable for
    a given input and asserts cleanly in tests.
    """

    def summarize(self, text: str) -> str:
        stripped = text.strip()
        if not stripped:
            return "Empty note."
        first = stripped.split(".")[0].strip()
        words = len(stripped.split())
        return f"{first}. ({words} words)"


class HttpProvider:
    """Placeholder for a real network-backed provider."""

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    def summarize(self, text: str) -> str:  # pragma: no cover - not used in CI
        raise RuntimeError("HttpProvider requires a configured backend")


def get_provider() -> SummaryProvider:
    settings = get_settings()
    if settings.provider_mode == "fake":
        return FakeProvider()
    return HttpProvider(settings.provider_api_key)
