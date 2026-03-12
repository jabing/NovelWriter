# src/monitoring/tracing.py
"""Distributed tracing system."""

import time
import uuid
from collections import deque
from contextlib import contextmanager
from dataclasses import dataclass, field
from functools import wraps
from threading import Lock, local
from typing import (
    Any,
    Callable,
    ContextManager,
    Generic,
    Iterator,
    ParamSpec,
    TypeVar,
)

T = TypeVar("T")
P = ParamSpec("P")


@dataclass
class SpanEvent:
    """Event that occurred within a span."""

    name: str
    timestamp: float = field(default_factory=time.time)
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass
class SpanContext:
    """Context for a span containing trace and span IDs."""

    trace_id: str
    span_id: str
    parent_span_id: str | None = None


class Span:
    """Represents a single span in a trace."""

    def __init__(
        self,
        name: str,
        context: SpanContext,
        attributes: dict[str, Any] | None = None,
    ) -> None:
        """Initialize a span.

        Args:
            name: Name of the span
            context: Span context containing trace and span IDs
            attributes: Optional attributes for the span
        """
        self.name = name
        self.context = context
        self.attributes: dict[str, Any] = attributes or {}
        self.events: list[SpanEvent] = []
        self.start_time: float | None = None
        self.end_time: float | None = None
        self._lock = Lock()

    def start(self) -> "Span":
        """Start the span.

        Returns:
            The span instance for chaining
        """
        with self._lock:
            self.start_time = time.time()
        return self

    def end(self) -> None:
        """End the span."""
        with self._lock:
            self.end_time = time.time()

    def set_attribute(self, key: str, value: Any) -> "Span":
        """Set an attribute on the span.

        Args:
            key: Attribute key
            value: Attribute value

        Returns:
            The span instance for chaining
        """
        with self._lock:
            self.attributes[key] = value
        return self

    def add_event(
        self,
        name: str,
        attributes: dict[str, Any] | None = None,
    ) -> "Span":
        """Add an event to the span.

        Args:
            name: Name of the event
            attributes: Optional attributes for the event

        Returns:
            The span instance for chaining
        """
        with self._lock:
            self.events.append(SpanEvent(name=name, attributes=attributes or {}))
        return self

    @property
    def duration(self) -> float | None:
        """Get the duration of the span in seconds.

        Returns:
            Duration in seconds or None if span hasn't ended
        """
        if self.start_time is not None and self.end_time is not None:
            return self.end_time - self.start_time
        return None

    def collect(self) -> dict[str, Any]:
        """Collect span data as a dictionary.

        Returns:
            Dictionary of span data
        """
        with self._lock:
            return {
                "name": self.name,
                "trace_id": self.context.trace_id,
                "span_id": self.context.span_id,
                "parent_span_id": self.context.parent_span_id,
                "attributes": dict(self.attributes),
                "events": [
                    {
                        "name": e.name,
                        "timestamp": e.timestamp,
                        "attributes": dict(e.attributes),
                    }
                    for e in self.events
                ],
                "start_time": self.start_time,
                "end_time": self.end_time,
                "duration": self.duration,
            }


class SpanExporter:
    """Base class for span exporters."""

    def export(self, spans: list[Span]) -> None:
        """Export a list of spans.

        Args:
            spans: List of spans to export
        """
        pass


class InMemorySpanExporter(SpanExporter):
    """Span exporter that stores spans in memory."""

    def __init__(self, max_spans: int = 1000) -> None:
        """Initialize the in-memory exporter.

        Args:
            max_spans: Maximum number of spans to keep
        """
        self._spans: deque[Span] = deque(maxlen=max_spans)
        self._lock = Lock()

    def export(self, spans: list[Span]) -> None:
        """Export spans to memory.

        Args:
            spans: List of spans to export
        """
        with self._lock:
            for span in spans:
                self._spans.append(span)

    def get_spans(self) -> list[Span]:
        """Get all stored spans.

        Returns:
            List of stored spans
        """
        with self._lock:
            return list(self._spans)

    def clear(self) -> None:
        """Clear all stored spans."""
        with self._lock:
            self._spans.clear()

    def collect(self) -> list[dict[str, Any]]:
        """Collect all span data.

        Returns:
            List of span data dictionaries
        """
        with self._lock:
            return [span.collect() for span in self._spans]


class Tracer:
    """Tracer for creating and managing spans."""

    def __init__(
        self,
        name: str = "default",
        exporter: SpanExporter | None = None,
    ) -> None:
        """Initialize the tracer.

        Args:
            name: Name of the tracer
            exporter: Optional span exporter
        """
        self.name = name
        self.exporter = exporter or InMemorySpanExporter()
        self._local = local()
        self._lock = Lock()

    def _generate_trace_id(self) -> str:
        """Generate a new trace ID.

        Returns:
            New trace ID
        """
        return uuid.uuid4().hex

    def _generate_span_id(self) -> str:
        """Generate a new span ID.

        Returns:
            New span ID
        """
        return uuid.uuid4().hex[:16]

    @property
    def current_span(self) -> Span | None:
        """Get the current active span.

        Returns:
            Current span or None
        """
        return getattr(self._local, "current_span", None)

    @current_span.setter
    def current_span(self, span: Span | None) -> None:
        """Set the current active span.

        Args:
            span: Span to set as current or None
        """
        self._local.current_span = span

    def start_span(
        self,
        name: str,
        attributes: dict[str, Any] | None = None,
        parent_context: SpanContext | None = None,
    ) -> Span:
        """Start a new span.

        Args:
            name: Name of the span
            attributes: Optional attributes for the span
            parent_context: Optional parent span context

        Returns:
            New span instance
        """
        if parent_context is None and self.current_span is not None:
            parent_context = self.current_span.context

        if parent_context is not None:
            trace_id = parent_context.trace_id
            parent_span_id = parent_context.span_id
        else:
            trace_id = self._generate_trace_id()
            parent_span_id = None

        span_id = self._generate_span_id()
        context = SpanContext(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
        )

        span = Span(name=name, context=context, attributes=attributes)
        return span.start()

    @contextmanager
    def span(
        self,
        name: str,
        attributes: dict[str, Any] | None = None,
    ) -> Iterator[Span]:
        """Context manager for creating a span.

        Args:
            name: Name of the span
            attributes: Optional attributes for the span

        Yields:
            The created span
        """
        previous_span = self.current_span
        span = self.start_span(name=name, attributes=attributes)

        try:
            self.current_span = span
            yield span
        finally:
            span.end()
            self.current_span = previous_span

            if self.exporter is not None:
                self.exporter.export([span])

    def trace(
        self,
        name: str | None = None,
        attributes: dict[str, Any] | None = None,
    ) -> Callable[[Callable[P, T]], Callable[P, T]]:
        """Decorator to trace a function.

        Args:
            name: Optional name for the span (uses function name if not provided)
            attributes: Optional attributes for the span

        Returns:
            Decorator function
        """

        def decorator(func: Callable[P, T]) -> Callable[P, T]:
            span_name = name or func.__name__

            @wraps(func)
            def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
                with self.span(name=span_name, attributes=attributes):
                    return func(*args, **kwargs)

            return wrapper

        return decorator

    def async_trace(
        self,
        name: str | None = None,
        attributes: dict[str, Any] | None = None,
    ) -> Callable[[Callable[P, Any]], Callable[P, Any]]:
        """Decorator to trace an async function.

        Args:
            name: Optional name for the span (uses function name if not provided)
            attributes: Optional attributes for the span

        Returns:
            Decorator function
        """

        def decorator(func: Callable[P, Any]) -> Callable[P, Any]:
            span_name = name or func.__name__

            @wraps(func)
            async def wrapper(*args: P.args, **kwargs: P.kwargs) -> Any:
                with self.span(name=span_name, attributes=attributes):
                    return await func(*args, **kwargs)

            return wrapper

        return decorator

    def get_current_context(self) -> SpanContext | None:
        """Get the current span context.

        Returns:
            Current span context or None
        """
        if self.current_span is not None:
            return self.current_span.context
        return None


# Global tracer
_tracer: Tracer | None = None


def get_tracer() -> Tracer:
    """Get the global tracer.

    Returns:
        Global Tracer instance
    """
    global _tracer
    if _tracer is None:
        _tracer = Tracer()
    return _tracer
