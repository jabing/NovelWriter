# src/monitoring/__init__.py
"""Monitoring and alerting system."""

from src.monitoring.alerts import (
    Alert,
    AlertManager,
    AlertSeverity,
    AlertType,
    get_alert_manager,
)
from src.monitoring.error_tracking import (
    BaseErrorBackend,
    ErrorBackendType,
    ErrorEvent,
    ErrorTracker,
    LogBackend,
    SentryBackend,
    WebhookBackend,
    get_error_tracker,
)
from src.monitoring.exporters import (
    BaseExporter,
    LogExporter,
    OpenTelemetryExporter,
    PrometheusExporter,
    get_log_exporter,
    get_otel_exporter,
    get_prometheus_exporter,
)
from src.monitoring.health import (
    HealthCheckResult,
    HealthMonitor,
    HealthStatus,
    get_health_monitor,
)
from src.monitoring.metrics import (
    Counter,
    Gauge,
    Histogram,
    HistogramData,
    MetricsCollector,
    Summary,
    get_metrics_collector,
)
from src.monitoring.tracing import (
    InMemorySpanExporter,
    Span,
    SpanContext,
    SpanEvent,
    SpanExporter,
    Tracer,
    get_tracer,
)

# Convenience decorators
_metrics = get_metrics_collector()
_tracer = get_tracer()
_error_tracker = get_error_tracker()

timer = _metrics.async_timeit
async_trace = _tracer.async_trace
async_track_errors = _error_tracker.async_track_errors

__all__ = [
    "Alert",
    "AlertManager",
    "AlertSeverity",
    "AlertType",
    "get_alert_manager",
    "BaseErrorBackend",
    "ErrorBackendType",
    "ErrorEvent",
    "ErrorTracker",
    "LogBackend",
    "SentryBackend",
    "WebhookBackend",
    "get_error_tracker",
    "BaseExporter",
    "LogExporter",
    "OpenTelemetryExporter",
    "PrometheusExporter",
    "get_log_exporter",
    "get_otel_exporter",
    "get_prometheus_exporter",
    "HealthCheckResult",
    "HealthMonitor",
    "HealthStatus",
    "get_health_monitor",
    "Counter",
    "Gauge",
    "Histogram",
    "HistogramData",
    "MetricsCollector",
    "Summary",
    "get_metrics_collector",
    "InMemorySpanExporter",
    "Span",
    "SpanContext",
    "SpanEvent",
    "SpanExporter",
    "Tracer",
    "get_tracer",
    # Decorators
    "timer",
    "async_trace",
    "async_track_errors",
]
