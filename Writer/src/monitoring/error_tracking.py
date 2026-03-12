# src/monitoring/error_tracking.py
"""Error tracking and reporting system."""

import logging
import traceback
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from functools import wraps
from threading import Lock
from typing import Any, ParamSpec, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")
P = ParamSpec("P")


class ErrorBackendType(str, Enum):
    """Supported error backends."""

    LOG = "log"
    SENTRY = "sentry"
    WEBHOOK = "webhook"


@dataclass
class ErrorEvent:
    """An error event to be tracked."""

    exception_type: str
    message: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    stacktrace: str = ""
    context: dict[str, Any] = field(default_factory=dict)
    tags: dict[str, str] = field(default_factory=dict)
    level: str = "error"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "exception_type": self.exception_type,
            "message": self.message,
            "timestamp": self.timestamp,
            "stacktrace": self.stacktrace,
            "context": self.context,
            "tags": self.tags,
            "level": self.level,
        }


class BaseErrorBackend(ABC):
    """Base class for error backends."""

    @abstractmethod
    async def capture(self, event: ErrorEvent) -> None:
        """Capture an error event.

        Args:
            event: Error event to capture
        """
        pass


class LogBackend(BaseErrorBackend):
    """Logging backend for errors."""

    def __init__(self, log_level: int = logging.ERROR) -> None:
        """Initialize log backend.

        Args:
            log_level: Log level to use
        """
        self.log_level = log_level

    async def capture(self, event: ErrorEvent) -> None:
        """Capture an error event.

        Args:
            event: Error event to capture
        """
        log_message = (
            f"[ERROR] {event.exception_type}: {event.message}\nStacktrace:\n{event.stacktrace}"
        )
        if event.context:
            log_message += f"\nContext: {event.context}"
        if event.tags:
            log_message += f"\nTags: {event.tags}"

        logger.log(self.log_level, log_message)


class SentryBackend(BaseErrorBackend):
    """Sentry backend for errors (optional)."""

    def __init__(self, dsn: str | None = None) -> None:
        """Initialize Sentry backend.

        Args:
            dsn: Sentry DSN (optional, uses environment if not provided)
        """
        self.dsn = dsn
        self._initialized = False
        self._sentry = None

        try:
            import sentry_sdk

            self._sentry = sentry_sdk
            if dsn:
                self._sentry.init(dsn=dsn)
                self._initialized = True
            logger.debug("Sentry SDK available")
        except ImportError:
            logger.debug("Sentry SDK not available")

    async def capture(self, event: ErrorEvent) -> None:
        """Capture an error event.

        Args:
            event: Error event to capture
        """
        if not self._sentry:
            return

        with self._sentry.configure_scope() as scope:
            for key, value in event.tags.items():
                scope.set_tag(key, value)
            for key, value in event.context.items():
                scope.set_context(key, value)

            # Create exception for Sentry
            try:
                exc = type(event.exception_type, (Exception,), {})(event.message)
                self._sentry.capture_exception(exc)
            except Exception as e:
                logger.debug(f"Failed to send to Sentry: {e}")


class WebhookBackend(BaseErrorBackend):
    """Webhook backend for errors."""

    def __init__(self, webhook_url: str) -> None:
        """Initialize webhook backend.

        Args:
            webhook_url: Webhook URL to send events to
        """
        self.webhook_url = webhook_url
        self._requests = None

        try:
            import requests

            self._requests = requests
            logger.debug("Requests library available for webhook")
        except ImportError:
            logger.debug("Requests library not available for webhook")

    async def capture(self, event: ErrorEvent) -> None:
        """Capture an error event.

        Args:
            event: Error event to capture
        """
        if not self._requests or not self.webhook_url:
            return

        try:
            _ = self._requests.post(self.webhook_url, json=event.to_dict(), timeout=5)
        except Exception as e:
            logger.debug(f"Failed to send to webhook: {e}")


class ErrorTracker:
    """Central error tracking manager."""

    def __init__(self, max_history: int = 1000) -> None:
        """Initialize error tracker.

        Args:
            max_history: Maximum number of error events to keep in history
        """
        self._backends: list[BaseErrorBackend] = []
        self._error_history: list[ErrorEvent] = []
        self._max_history = max_history
        self._error_counts: dict[str, int] = {}
        self._context: dict[str, Any] = {}
        self._tags: dict[str, str] = {}
        self._lock = Lock()

    def add_backend(self, backend: BaseErrorBackend) -> None:
        """Add an error backend.

        Args:
            backend: Error backend to add
        """
        self._backends.append(backend)

    def add_log_backend(self, log_level: int = logging.ERROR) -> None:
        """Add a logging backend.

        Args:
            log_level: Log level to use
        """
        self.add_backend(LogBackend(log_level))

    def add_sentry_backend(self, dsn: str | None = None) -> None:
        """Add a Sentry backend (optional).

        Args:
            dsn: Sentry DSN
        """
        self.add_backend(SentryBackend(dsn))

    def add_webhook_backend(self, webhook_url: str) -> None:
        """Add a webhook backend.

        Args:
            webhook_url: Webhook URL
        """
        self.add_backend(WebhookBackend(webhook_url))

    def set_context(self, key: str, value: Any) -> None:
        """Set global context for all error events.

        Args:
            key: Context key
            value: Context value
        """
        with self._lock:
            self._context[key] = value

    def set_tag(self, key: str, value: str) -> None:
        """Set global tag for all error events.

        Args:
            key: Tag key
            value: Tag value
        """
        with self._lock:
            self._tags[key] = value

    def capture_exception(
        self,
        exc: Exception,
        context: dict[str, Any] | None = None,
        tags: dict[str, str] | None = None,
    ) -> ErrorEvent:
        """Capture an exception.

        Args:
            exc: Exception to capture
            context: Additional context
            tags: Additional tags

        Returns:
            Created error event
        """
        # Merge contexts and tags
        with self._lock:
            merged_context = {**self._context, **(context or {})}
            merged_tags = {**self._tags, **(tags or {})}

        event = ErrorEvent(
            exception_type=type(exc).__name__,
            message=str(exc),
            stacktrace=traceback.format_exc(),
            context=merged_context,
            tags=merged_tags,
        )

        # Add to history
        with self._lock:
            self._error_history.append(event)
            if len(self._error_history) > self._max_history:
                self._error_history = self._error_history[-self._max_history :]

            # Update counts
            key = type(exc).__name__
            self._error_counts[key] = self._error_counts.get(key, 0) + 1

        # Send to backends (fire and forget, don't block)
        for backend in self._backends:
            try:
                import asyncio

                _ = asyncio.create_task(backend.capture(event))
            except Exception:
                pass

        return event

    def capture_message(
        self,
        message: str,
        level: str = "error",
        context: dict[str, Any] | None = None,
        tags: dict[str, str] | None = None,
    ) -> ErrorEvent:
        """Capture a message as an error event.

        Args:
            message: Message to capture
            level: Error level
            context: Additional context
            tags: Additional tags

        Returns:
            Created error event
        """
        with self._lock:
            merged_context = {**self._context, **(context or {})}
            merged_tags = {**self._tags, **(tags or {})}

        event = ErrorEvent(
            exception_type="Message",
            message=message,
            context=merged_context,
            tags=merged_tags,
            level=level,
        )

        with self._lock:
            self._error_history.append(event)
            if len(self._error_history) > self._max_history:
                self._error_history = self._error_history[-self._max_history :]

            key = f"message:{level}"
            self._error_counts[key] = self._error_counts.get(key, 0) + 1

        for backend in self._backends:
            try:
                import asyncio

                _ = asyncio.create_task(backend.capture(event))
            except Exception:
                pass

        return event

    def track_errors(
        self,
        context: dict[str, Any] | None = None,
        tags: dict[str, str] | None = None,
        reraise: bool = True,
    ) -> Callable[[Callable[P, T]], Callable[P, T]]:
        """Decorator to track errors in functions.

        Args:
            context: Additional context for errors
            tags: Additional tags for errors
            reraise: Whether to re-raise the exception after capturing

        Returns:
            Decorator function
        """

        def decorator(func: Callable[P, T]) -> Callable[P, T]:
            @wraps(func)
            def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    self.capture_exception(
                        e,
                        context={
                            "function": func.__name__,
                            "module": func.__module__,
                            **(context or {}),
                        },
                        tags=tags,
                    )
                    if reraise:
                        raise
                    # We shouldn't reach here if reraise is True, but for type safety
                    # we re-raise in all cases to maintain return type contract
                    raise

            return wrapper

        return decorator

    def async_track_errors(
        self,
        context: dict[str, Any] | None = None,
        tags: dict[str, str] | None = None,
        reraise: bool = True,
    ) -> Callable[[Callable[P, Any]], Callable[P, Any]]:
        """Decorator to track errors in async functions.

        Args:
            context: Additional context for errors
            tags: Additional tags for errors
            reraise: Whether to re-raise the exception after capturing

        Returns:
            Decorator function
        """

        def decorator(func: Callable[P, Any]) -> Callable[P, Any]:
            @wraps(func)
            async def wrapper(*args: P.args, **kwargs: P.kwargs) -> Any:
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    self.capture_exception(
                        e,
                        context={
                            "function": func.__name__,
                            "module": func.__module__,
                            **(context or {}),
                        },
                        tags=tags,
                    )
                    if reraise:
                        raise
                    return None

            return wrapper

        return decorator

    def get_history(
        self,
        exception_type: str | None = None,
        limit: int = 100,
    ) -> list[ErrorEvent]:
        """Get error history.

        Args:
            exception_type: Filter by exception type
            limit: Maximum errors to return

        Returns:
            List of error events
        """
        with self._lock:
            events = self._error_history.copy()

        if exception_type:
            events = [e for e in events if e.exception_type == exception_type]

        return events[-limit:]

    def get_stats(self) -> dict[str, Any]:
        """Get error statistics.

        Returns:
            Error statistics
        """
        with self._lock:
            return {
                "total_errors": len(self._error_history),
                "by_type": dict(self._error_counts),
            }

    def clear_history(self) -> None:
        """Clear error history."""
        with self._lock:
            self._error_history.clear()
            self._error_counts.clear()


# Global error tracker
_error_tracker: ErrorTracker | None = None


def get_error_tracker() -> ErrorTracker:
    """Get global error tracker.

    Returns:
        Global ErrorTracker instance
    """
    global _error_tracker
    if _error_tracker is None:
        _error_tracker = ErrorTracker()
        # Add default log backend
        _error_tracker.add_log_backend()
    return _error_tracker
