# src/monitoring/exporters.py
"""Metrics exporters for monitoring systems."""

import logging
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger(__name__)


class BaseExporter(ABC):
    """Base interface for metrics exporters."""

    @abstractmethod
    def export(self, metrics: dict[str, Any]) -> None:
        """Export metrics data.

        Args:
            metrics: Metrics data dictionary from MetricsCollector.collect_all()
        """
        pass


class LogExporter(BaseExporter):
    """Metrics exporter that logs metrics for debugging purposes."""

    def __init__(self, level: int = logging.INFO) -> None:
        """Initialize log exporter.

        Args:
            level: Logging level to use
        """
        self.level = level

    def export(self, metrics: dict[str, Any]) -> None:
        """Export metrics to logs.

        Args:
            metrics: Metrics data dictionary
        """
        logger.log(self.level, "Metrics export: %s", metrics)


class PrometheusExporter(BaseExporter):
    """Metrics exporter that provides Prometheus HTTP endpoint."""

    def __init__(self, port: int = 8000, addr: str = "0.0.0.0") -> None:
        """Initialize Prometheus exporter.

        Args:
            port: HTTP port to listen on
            addr: Address to bind to
        """
        self.port = port
        self.addr = addr
        self._metrics: dict[str, Any] = {}
        self._server = None
        self._thread = None

    def export(self, metrics: dict[str, Any]) -> None:
        """Store metrics for Prometheus scraping.

        Args:
            metrics: Metrics data dictionary
        """
        self._metrics = metrics

    def _to_prometheus_format(self) -> str:
        """Convert internal metrics to Prometheus text format.

        Returns:
            Prometheus formatted metrics string
        """
        lines = []

        # Process counters
        for counter in self._metrics.get("counters", []):
            name = counter["name"]
            description = counter.get("description", "")
            if description:
                lines.append(f"# HELP {name} {description}")
            lines.append(f"# TYPE {name} counter")
            for value in counter.get("values", []):
                labels = value.get("labels", {})
                label_str = ",".join([f'{k}="{v}"' for k, v in labels.items()])
                if label_str:
                    lines.append(f"{name}{{{label_str}}} {value['value']}")
                else:
                    lines.append(f"{name} {value['value']}")

        # Process gauges
        for gauge in self._metrics.get("gauges", []):
            name = gauge["name"]
            description = gauge.get("description", "")
            if description:
                lines.append(f"# HELP {name} {description}")
            lines.append(f"# TYPE {name} gauge")
            for value in gauge.get("values", []):
                labels = value.get("labels", {})
                label_str = ",".join([f'{k}="{v}"' for k, v in labels.items()])
                if label_str:
                    lines.append(f"{name}{{{label_str}}} {value['value']}")
                else:
                    lines.append(f"{name} {value['value']}")

        # Process histograms
        for histogram in self._metrics.get("histograms", []):
            name = histogram["name"]
            description = histogram.get("description", "")
            if description:
                lines.append(f"# HELP {name} {description}")
            lines.append(f"# TYPE {name} histogram")
            for value in histogram.get("values", []):
                labels = value.get("labels", {})
                label_str = ",".join([f'{k}="{v}"' for k, v in labels.items()])
                if label_str:
                    label_str = "{" + label_str + "}"

                # Count and sum
                lines.append(f"{name}_count{label_str} {value['count']}")
                lines.append(f"{name}_sum{label_str} {value['sum']}")

                # Buckets
                for bucket in value.get("buckets", []):
                    bucket_labels = labels.copy()
                    bucket_labels["le"] = str(bucket["le"])
                    bucket_label_str = ",".join([f'{k}="{v}"' for k, v in bucket_labels.items()])
                    lines.append(f"{name}_bucket{{{bucket_label_str}}} {bucket['count']}")

        # Process summaries
        for summary in self._metrics.get("summaries", []):
            name = summary["name"]
            description = summary.get("description", "")
            if description:
                lines.append(f"# HELP {name} {description}")
            lines.append(f"# TYPE {name} summary")
            for value in summary.get("values", []):
                labels = value.get("labels", {})
                label_str = ",".join([f'{k}="{v}"' for k, v in labels.items()])
                if label_str:
                    label_str = "{" + label_str + "}"

                lines.append(f"{name}_count{label_str} {value['count']}")
                lines.append(f"{name}_sum{label_str} {value['sum']}")

        return "\n".join(lines) + "\n"

    def start_server(self) -> None:
        """Start HTTP server for Prometheus scraping."""
        try:
            from http.server import BaseHTTPRequestHandler, HTTPServer
            import threading

            class MetricsHandler(BaseHTTPRequestHandler):
                def do_GET(self) -> None:
                    if self.path == "/metrics":
                        self.send_response(200)
                        self.send_header("Content-Type", "text/plain; version=0.0.4")
                        self.end_headers()
                        self.wfile.write(
                            self.server.exporter._to_prometheus_format().encode("utf-8")
                        )
                    else:
                        self.send_response(404)
                        self.end_headers()

            server = HTTPServer((self.addr, self.port), MetricsHandler)
            server.exporter = self  # type: ignore
            self._server = server

            self._thread = threading.Thread(target=server.serve_forever, daemon=True)
            self._thread.start()
            logger.info("Prometheus exporter started on %s:%d/metrics", self.addr, self.port)
        except ImportError:
            logger.warning("HTTP server not available, Prometheus scraping disabled")
        except Exception as e:
            logger.error("Failed to start Prometheus exporter: %s", e)

    def stop_server(self) -> None:
        """Stop HTTP server."""
        if self._server:
            self._server.shutdown()
            self._server = None
        if self._thread:
            self._thread.join(timeout=5.0)
            self._thread = None


class OpenTelemetryExporter(BaseExporter):
    """Metrics exporter that sends data via OpenTelemetry OTLP."""

    def __init__(self, endpoint: str = "http://localhost:4317") -> None:
        """Initialize OpenTelemetry exporter.

        Args:
            endpoint: OTLP endpoint URL
        """
        self.endpoint = endpoint
        self._provider = None
        self._reader = None
        self._initialized = False

    def _initialize(self) -> None:
        """Initialize OpenTelemetry components if available."""
        if self._initialized:
            return

        try:
            # Try to import OpenTelemetry packages (optional dependencies)
            from opentelemetry import metrics
            from opentelemetry.sdk.metrics import MeterProvider
            from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
            from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter

            # Create meter provider
            self._provider = MeterProvider()

            # Create OTLP exporter
            otlp_exporter = OTLPMetricExporter(endpoint=self.endpoint, insecure=True)

            # Create metric reader
            self._reader = PeriodicExportingMetricReader(otlp_exporter)
            self._provider.add_metric_reader(self._reader)

            # Set global meter provider
            metrics.set_meter_provider(self._provider)

            self._initialized = True
            logger.info("OpenTelemetry exporter initialized with endpoint: %s", self.endpoint)
        except ImportError:
            logger.warning("OpenTelemetry packages not available, OTLP export disabled")
        except Exception as e:
            logger.error("Failed to initialize OpenTelemetry exporter: %s", e)

    def export(self, metrics: dict[str, Any]) -> None:
        """Export metrics via OpenTelemetry.

        Args:
            metrics: Metrics data dictionary
        """
        self._initialize()

        if not self._initialized or not self._provider:
            return

        try:
            from opentelemetry import metrics

            meter = metrics.get_meter("novel-agent")

            # Process counters
            for counter in metrics.get("counters", []):
                otel_counter = meter.create_counter(
                    name=counter["name"],
                    description=counter.get("description", ""),
                )
                for value in counter.get("values", []):
                    otel_counter.add(int(value["value"]), value.get("labels", {}))

            # Process gauges (using observable gauge)
            for gauge in metrics.get("gauges", []):

                def create_gauge_callback(gauge_data):
                    def callback(observer):
                        for value in gauge_data.get("values", []):
                            observer.observe(value["value"], value.get("labels", {}))

                    return callback

                meter.create_observable_gauge(
                    name=gauge["name"],
                    description=gauge.get("description", ""),
                    callbacks=[create_gauge_callback(gauge)],
                )

            # Process histograms
            for histogram in metrics.get("histograms", []):
                otel_histogram = meter.create_histogram(
                    name=histogram["name"],
                    description=histogram.get("description", ""),
                )
                for value in histogram.get("values", []):
                    if value.get("mean") is not None:
                        otel_histogram.record(value["mean"], value.get("labels", {}))

        except Exception as e:
            logger.error("Failed to export metrics via OpenTelemetry: %s", e)

    def shutdown(self) -> None:
        """Shut down OpenTelemetry components."""
        if self._provider:
            self._provider.shutdown()
            self._provider = None
            self._initialized = False


# Global exporters
_log_exporter: LogExporter | None = None
_prometheus_exporter: PrometheusExporter | None = None
_otel_exporter: OpenTelemetryExporter | None = None


def get_log_exporter() -> LogExporter:
    """Get global log exporter.

    Returns:
        Global LogExporter instance
    """
    global _log_exporter
    if _log_exporter is None:
        _log_exporter = LogExporter()
    return _log_exporter


def get_prometheus_exporter() -> PrometheusExporter:
    """Get global Prometheus exporter.

    Returns:
        Global PrometheusExporter instance
    """
    global _prometheus_exporter
    if _prometheus_exporter is None:
        _prometheus_exporter = PrometheusExporter()
    return _prometheus_exporter


def get_otel_exporter() -> OpenTelemetryExporter:
    """Get global OpenTelemetry exporter.

    Returns:
        Global OpenTelemetryExporter instance
    """
    global _otel_exporter
    if _otel_exporter is None:
        _otel_exporter = OpenTelemetryExporter()
    return _otel_exporter
