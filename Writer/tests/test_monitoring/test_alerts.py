# tests/test_monitoring/test_alerts.py
"""Tests for alerting system."""

import pytest

from src.monitoring.alerts import (
    Alert,
    AlertManager,
    AlertSeverity,
    AlertType,
    get_alert_manager,
)


class TestAlert:
    """Tests for Alert dataclass."""

    def test_alert_creation(self) -> None:
        """Test creating an alert."""
        alert = Alert(
            alert_type=AlertType.SYSTEM_ERROR,
            severity=AlertSeverity.ERROR,
            message="Test alert",
        )

        assert alert.alert_type == AlertType.SYSTEM_ERROR
        assert alert.severity == AlertSeverity.ERROR
        assert alert.message == "Test alert"
        assert alert.acknowledged is False
        assert alert.timestamp is not None

    def test_alert_to_dict(self) -> None:
        """Test converting alert to dictionary."""
        alert = Alert(
            alert_type=AlertType.API_ERROR,
            severity=AlertSeverity.WARNING,
            message="API warning",
            details={"code": 500},
        )

        result = alert.to_dict()

        assert result["alert_type"] == "api_error"
        assert result["severity"] == "warning"
        assert result["message"] == "API warning"
        assert result["details"]["code"] == 500
        assert result["acknowledged"] is False


class TestAlertManager:
    """Tests for AlertManager."""

    @pytest.fixture
    def manager(self) -> AlertManager:
        """Create fresh alert manager."""
        return AlertManager()

    def test_manager_initialization(self, manager: AlertManager) -> None:
        """Test manager initializes correctly."""
        assert len(manager._handlers) == 0
        assert len(manager._alert_history) == 0

    @pytest.mark.asyncio
    async def test_trigger_alert(self, manager: AlertManager) -> None:
        """Test triggering an alert."""
        alert = Alert(
            alert_type=AlertType.SYSTEM_ERROR,
            severity=AlertSeverity.ERROR,
            message="Test error",
        )

        await manager.trigger(alert)

        assert len(manager._alert_history) == 1
        assert manager._alert_history[0] == alert

    @pytest.mark.asyncio
    async def test_trigger_simple_alert(self, manager: AlertManager) -> None:
        """Test triggering a simple alert."""
        await manager.trigger_simple(
            alert_type=AlertType.API_ERROR,
            severity=AlertSeverity.WARNING,
            message="API is slow",
            details={"latency_ms": 5000},
        )

        assert len(manager._alert_history) == 1
        alert = manager._alert_history[0]
        assert alert.alert_type == AlertType.API_ERROR
        assert alert.details["latency_ms"] == 5000

    @pytest.mark.asyncio
    async def test_alert_handler(self, manager: AlertManager) -> None:
        """Test alert handler is called."""
        called = []

        async def handler(alert: Alert) -> None:
            called.append(alert)

        manager.add_handler(handler)

        await manager.trigger_simple(
            alert_type=AlertType.SYSTEM_ERROR,
            severity=AlertSeverity.ERROR,
            message="Test",
        )

        assert len(called) == 1

    @pytest.mark.asyncio
    async def test_multiple_handlers(self, manager: AlertManager) -> None:
        """Test multiple handlers are called."""
        call_count = [0, 0]

        async def handler1(alert: Alert) -> None:
            call_count[0] += 1

        async def handler2(alert: Alert) -> None:
            call_count[1] += 1

        manager.add_handler(handler1)
        manager.add_handler(handler2)

        await manager.trigger_simple(
            alert_type=AlertType.SYSTEM_ERROR,
            severity=AlertSeverity.INFO,
            message="Test",
        )

        assert call_count == [1, 1]

    @pytest.mark.asyncio
    async def test_get_history(self, manager: AlertManager) -> None:
        """Test getting alert history."""
        await manager.trigger_simple(AlertType.SYSTEM_ERROR, AlertSeverity.ERROR, "Error 1")
        await manager.trigger_simple(AlertType.API_ERROR, AlertSeverity.WARNING, "Warning 1")
        await manager.trigger_simple(AlertType.SYSTEM_ERROR, AlertSeverity.INFO, "Info 1")

        history = manager.get_history()
        assert len(history) == 3

        # Filter by severity
        errors = manager.get_history(severity=AlertSeverity.ERROR)
        assert len(errors) == 1

        # Filter by type
        system_errors = manager.get_history(alert_type=AlertType.SYSTEM_ERROR)
        assert len(system_errors) == 2

    @pytest.mark.asyncio
    async def test_get_stats(self, manager: AlertManager) -> None:
        """Test getting alert statistics."""
        await manager.trigger_simple(AlertType.SYSTEM_ERROR, AlertSeverity.ERROR, "Error")
        await manager.trigger_simple(AlertType.API_ERROR, AlertSeverity.WARNING, "Warning")

        stats = manager.get_stats()

        assert stats["total_alerts"] == 2
        assert stats["unacknowledged"] == 2
        assert stats["by_severity"]["error"] == 1
        assert stats["by_severity"]["warning"] == 1

    def test_acknowledge(self, manager: AlertManager) -> None:
        """Test acknowledging an alert."""
        alert = Alert(
            alert_type=AlertType.SYSTEM_ERROR,
            severity=AlertSeverity.ERROR,
            message="Test",
        )
        manager._alert_history.append(alert)

        result = manager.acknowledge(0)

        assert result is True
        assert alert.acknowledged is True

    def test_acknowledge_invalid_index(self, manager: AlertManager) -> None:
        """Test acknowledging with invalid index."""
        result = manager.acknowledge(999)
        assert result is False

    @pytest.mark.asyncio
    async def test_max_history(self, manager: AlertManager) -> None:
        """Test max history limit."""
        manager._max_history = 5

        for i in range(10):
            await manager.trigger_simple(
                AlertType.SYSTEM_ERROR,
                AlertSeverity.INFO,
                f"Alert {i}",
            )

        assert len(manager._alert_history) == 5

    def test_clear_history(self, manager: AlertManager) -> None:
        """Test clearing history."""
        manager._alert_history = [Alert(
            alert_type=AlertType.SYSTEM_ERROR,
            severity=AlertSeverity.ERROR,
            message="Test",
        )]

        manager.clear_history()

        assert len(manager._alert_history) == 0


class TestAlertEnums:
    """Tests for alert enums."""

    def test_alert_severity_values(self) -> None:
        """Test alert severity enum values."""
        assert AlertSeverity.INFO.value == "info"
        assert AlertSeverity.WARNING.value == "warning"
        assert AlertSeverity.ERROR.value == "error"
        assert AlertSeverity.CRITICAL.value == "critical"

    def test_alert_type_values(self) -> None:
        """Test alert type enum values."""
        assert AlertType.SYSTEM_ERROR.value == "system_error"
        assert AlertType.API_ERROR.value == "api_error"
        assert AlertType.COST_THRESHOLD.value == "cost_threshold"
        assert AlertType.QUALITY_THRESHOLD.value == "quality_threshold"


class TestGlobalAlertManager:
    """Tests for global alert manager."""

    def test_get_alert_manager(self) -> None:
        """Test getting global alert manager."""
        manager = get_alert_manager()
        assert isinstance(manager, AlertManager)
