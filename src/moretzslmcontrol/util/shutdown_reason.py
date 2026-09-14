"""Helpers for reporting why the application is shutting down."""

from __future__ import annotations

from datetime import datetime


class ShutdownReason:
    """Store the first specific reason reported for an application shutdown."""

    _DEFAULT_REASON = "Qt event loop ended without a reported shutdown request"

    def __init__(self) -> None:
        self._reason = self._DEFAULT_REASON

    @property
    def value(self) -> str:
        """Return the currently known shutdown reason."""
        return self._reason

    def record(self, reason: str) -> None:
        """Keep the first specific reason because it is the closest to the cause."""
        if self._reason == self._DEFAULT_REASON:
            self._reason = reason


def shutdown_timestamp() -> str:
    """Return a timestamp in the same format as the application console."""
    return datetime.now().astimezone().strftime("%Y/%m/%d %H:%M:%S")
