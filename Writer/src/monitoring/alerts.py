# src/monitoring/alerts.py
"""Alerting system for monitoring."""

import logging
from collections.abc import Callable, Coroutine
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertType(str, Enum):
    """Types of alerts."""
    SYSTEM_ERROR = "system_error"
    API_ERROR = "api_error"
    COST_THRESHOLD = "cost_threshold"
    QUALITY_THRESHOLD = "quality_threshold"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    CONTENT_DEVIATION = "content_deviation"
    PUBLISHING_FAILURE = "publishing_failure"
    MEMORY_LIMIT = "memory_limit"


@dataclass
class Alert:
    """An alert object."""
    alert_type: AlertType
    severity: AlertSeverity
    message: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    details: dict[str, Any] = field(default_factory=dict)
    acknowledged: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "alert_type": self.alert_type.value,
            "severity": self.severity.value,
            "message": self.message,
            "timestamp": self.timestamp,
            "details": self.details,
            "acknowledged": self.acknowledged,
        }


AlertHandler = Callable[[Alert], Coroutine[Any, Any, None]]


class AlertManager:
    """Manages alerts and notifications."""

    def __init__(self, max_history: int = 1000) -> None:
        """Initialize alert manager.

        Args:
            max_history: Maximum number of alerts to keep in history
        """
        self._handlers: list[AlertHandler] = []
        self._alert_history: list[Alert] = []
        self._max_history = max_history
        self._alert_counts: dict[str, int] = {}

    def add_handler(self, handler: AlertHandler) -> None:
        """Add an alert handler.

        Args:
            handler: Async function to handle alerts
        """
        self._handlers.append(handler)

    async def trigger(self, alert: Alert) -> None:
        """Trigger an alert.

        Args:
            alert: Alert to trigger
        """
        # Add to history
        self._alert_history.append(alert)
        if len(self._alert_history) > self._max_history:
            self._alert_history = self._alert_history[-self._max_history:]

        # Update counts
        key = f"{alert.alert_type.value}:{alert.severity.value}"
        self._alert_counts[key] = self._alert_counts.get(key, 0) + 1

        # Log the alert
        log_level = {
            AlertSeverity.INFO: logging.INFO,
            AlertSeverity.WARNING: logging.WARNING,
            AlertSeverity.ERROR: logging.ERROR,
            AlertSeverity.CRITICAL: logging.CRITICAL,
        }.get(alert.severity, logging.INFO)

        logger.log(log_level, f"[ALERT] {alert.alert_type.value}: {alert.message}")

        # Call handlers
        for handler in self._handlers:
            try:
                await handler(alert)
            except Exception as e:
                logger.error(f"Alert handler failed: {e}")

    async def trigger_simple(
        self,
        alert_type: AlertType,
        severity: AlertSeverity,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Trigger a simple alert.

        Args:
            alert_type: Type of alert
            severity: Alert severity
            message: Alert message
            details: Additional details
        """
        alert = Alert(
            alert_type=alert_type,
            severity=severity,
            message=message,
            details=details or {},
        )
        await self.trigger(alert)

    def get_history(
        self,
        severity: AlertSeverity | None = None,
        alert_type: AlertType | None = None,
        limit: int = 100,
    ) -> list[Alert]:
        """Get alert history.

        Args:
            severity: Filter by severity
            alert_type: Filter by type
            limit: Maximum alerts to return

        Returns:
            List of alerts
        """
        alerts = self._alert_history

        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        if alert_type:
            alerts = [a for a in alerts if a.alert_type == alert_type]

        return alerts[-limit:]

    def get_stats(self) -> dict[str, Any]:
        """Get alert statistics.

        Returns:
            Alert statistics
        """
        return {
            "total_alerts": len(self._alert_history),
            "unacknowledged": len([a for a in self._alert_history if not a.acknowledged]),
            "by_type": {
                alert_type.value: len([
                    a for a in self._alert_history
                    if a.alert_type == alert_type
                ])
                for alert_type in AlertType
            },
            "by_severity": {
                severity.value: len([
                    a for a in self._alert_history
                    if a.severity == severity
                ])
                for severity in AlertSeverity
            },
            "counts": dict(self._alert_counts),
        }

    def acknowledge(self, alert_index: int) -> bool:
        """Acknowledge an alert.

        Args:
            alert_index: Index of alert in history

        Returns:
            True if acknowledged
        """
        if 0 <= alert_index < len(self._alert_history):
            self._alert_history[alert_index].acknowledged = True
            return True
        return False

    def clear_history(self) -> None:
        """Clear alert history."""
        self._alert_history.clear()
        self._alert_counts.clear()


# Alert handlers

async def log_alert_handler(alert: Alert) -> None:
    """Simple handler that logs alerts."""
    logger.info(f"Alert: {alert.alert_type.value} - {alert.message}")


async def email_alert_handler(
    smtp_server: str,
    sender: str,
    recipients: list[str],
) -> AlertHandler:
    """Create an email alert handler.

    Args:
        smtp_server: SMTP server address
        sender: Sender email address
        recipients: List of recipient emails

    Returns:
        Alert handler function
    """
    async def handler(alert: Alert) -> None:
        # In production, this would send an email
        # For MVP, just log it
        logger.info(
            f"Would send email to {recipients}: "
            f"[{alert.severity.value.upper()}] {alert.message}"
        )

    return handler


async def webhook_alert_handler(webhook_url: str) -> AlertHandler:
    """Create a webhook alert handler.

    Args:
        webhook_url: Webhook URL to post alerts

    Returns:
        Alert handler function
    """
    async def handler(alert: Alert) -> None:
        # In production, this would POST to webhook
        # For MVP, just log it
        logger.info(f"Would POST to {webhook_url}: {alert.to_dict()}")

    return handler


# Global alert manager
_alert_manager: AlertManager | None = None


def get_alert_manager() -> AlertManager:
    """Get global alert manager."""
    global _alert_manager
    if _alert_manager is None:
        _alert_manager = AlertManager()
        # Add default handler
        _alert_manager.add_handler(log_alert_handler)
    return _alert_manager
