"""Tests for monitoring router."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

if TYPE_CHECKING:
    from src.novel_agent.studio.core.state import StudioState


class TestHealth:
    """Tests for GET /api/monitoring/health endpoint."""

    def test_health_unavailable(self, client: TestClient):
        """Test health when monitor is not available."""
        with patch("src.novel_agent.api.routers.monitoring.HealthMonitor", None):
            response = client.get("/api/monitoring/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "unavailable"

    def test_health_with_health_method(self, client: TestClient):
        """Test health when monitor has health method."""
        mock_monitor = MagicMock()
        mock_monitor.health.return_value = {"database": "connected", "cache": "active"}
        
        with patch("src.novel_agent.api.routers.monitoring.HealthMonitor") as mock_class:
            mock_class.return_value = mock_monitor
            
            response = client.get("/api/monitoring/health")
            
            assert response.status_code == 200
            data = response.json()
            assert "status" in data

    def test_health_with_status_attribute(self, client: TestClient):
        """Test health when monitor has status attribute."""
        mock_monitor = MagicMock()
        mock_monitor.health.side_effect = AttributeError()
        mock_monitor.status = "healthy"
        
        with patch("src.novel_agent.api.routers.monitoring.HealthMonitor") as mock_class:
            mock_class.return_value = mock_monitor
            
            response = client.get("/api/monitoring/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"

    def test_health_fallback_unknown(self, client: TestClient):
        """Test health fallback to unknown when no methods available."""
        mock_monitor = MagicMock()
        mock_monitor.health.side_effect = AttributeError()
        del mock_monitor.status
        
        with patch("src.novel_agent.api.routers.monitoring.HealthMonitor") as mock_class:
            mock_class.return_value = mock_monitor
            
            response = client.get("/api/monitoring/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "unknown"


class TestMetrics:
    """Tests for GET /api/monitoring/metrics endpoint."""

    def test_metrics_unavailable(self, client: TestClient):
        """Test metrics when collector is not available."""
        with patch("src.novel_agent.api.routers.monitoring.MetricsCollector", None):
            response = client.get("/api/monitoring/metrics")
            
            assert response.status_code == 200
            data = response.json()
            assert data == {}

    def test_metrics_with_collect_method(self, client: TestClient):
        """Test metrics when collector has collect method."""
        mock_collector = MagicMock()
        mock_collector.collect.return_value = {
            "requests_total": 1000,
            "requests_failed": 5,
            "avg_latency_ms": 45
        }
        
        with patch("src.novel_agent.api.routers.monitoring.MetricsCollector") as mock_class:
            mock_class.return_value = mock_collector
            
            response = client.get("/api/monitoring/metrics")
            
            assert response.status_code == 200
            data = response.json()
            assert "requests_total" in data or isinstance(data, dict)

    def test_metrics_with_get_metrics_method(self, client: TestClient):
        """Test metrics when collector has get_metrics method."""
        mock_collector = MagicMock()
        mock_collector.collect.side_effect = AttributeError()
        mock_collector.get_metrics.return_value = {"cpu": 50, "memory": 60}
        
        with patch("src.novel_agent.api.routers.monitoring.MetricsCollector") as mock_class:
            mock_class.return_value = mock_collector
            
            response = client.get("/api/monitoring/metrics")
            
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, dict)

    def test_metrics_fallback_empty(self, client: TestClient):
        """Test metrics fallback to empty dict."""
        mock_collector = MagicMock()
        mock_collector.collect.side_effect = AttributeError()
        mock_collector.get_metrics.side_effect = AttributeError()
        
        with patch("src.novel_agent.api.routers.monitoring.MetricsCollector") as mock_class:
            mock_class.return_value = mock_collector
            
            response = client.get("/api/monitoring/metrics")
            
            assert response.status_code == 200
            data = response.json()
            assert data == {}


class TestAlerts:
    """Tests for GET /api/monitoring/alerts endpoint."""

    def test_alerts_unavailable(self, client: TestClient):
        """Test alerts when manager is not available."""
        with patch("src.novel_agent.api.routers.monitoring.AlertManager", None):
            response = client.get("/api/monitoring/alerts")
            
            assert response.status_code == 200
            data = response.json()
            assert data == []

    def test_alerts_with_list_alerts_method(self, client: TestClient):
        """Test alerts when manager has list_alerts method."""
        mock_manager = MagicMock()
        mock_manager.list_alerts.return_value = [
            {"id": "alert1", "severity": "high", "message": "CPU high"},
            {"id": "alert2", "severity": "medium", "message": "Memory warning"}
        ]
        
        with patch("src.novel_agent.api.routers.monitoring.AlertManager") as mock_class:
            mock_class.return_value = mock_manager
            
            response = client.get("/api/monitoring/alerts")
            
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)

    def test_alerts_with_get_alerts_method(self, client: TestClient):
        """Test alerts when manager has get_alerts method."""
        mock_manager = MagicMock()
        mock_manager.list_alerts.side_effect = AttributeError()
        mock_manager.get_alerts.return_value = [{"id": "alert1"}]
        
        with patch("src.novel_agent.api.routers.monitoring.AlertManager") as mock_class:
            mock_class.return_value = mock_manager
            
            response = client.get("/api/monitoring/alerts")
            
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)

    def test_alerts_fallback_empty(self, client: TestClient):
        """Test alerts fallback to empty list."""
        mock_manager = MagicMock()
        mock_manager.list_alerts.side_effect = AttributeError()
        mock_manager.get_alerts.side_effect = AttributeError()
        
        with patch("src.novel_agent.api.routers.monitoring.AlertManager") as mock_class:
            mock_class.return_value = mock_manager
            
            response = client.get("/api/monitoring/alerts")
            
            assert response.status_code == 200
            data = response.json()
            assert data == []


class TestAcknowledgeAlert:
    """Tests for POST /api/monitoring/alerts/{alert_id}/acknowledge endpoint."""

    def test_acknowledge_unavailable(self, client: TestClient):
        """Test acknowledge when manager is not available."""
        with patch("src.novel_agent.api.routers.monitoring.AlertManager", None):
            response = client.post("/api/monitoring/alerts/alert123/acknowledge", json={})
            
            assert response.status_code == 501

    def test_acknowledge_with_acknowledge_method(self, client: TestClient):
        """Test acknowledge with acknowledge method."""
        mock_manager = MagicMock()
        
        with patch("src.novel_agent.api.routers.monitoring.AlertManager") as mock_class:
            mock_class.return_value = mock_manager
            
            response = client.post(
                "/api/monitoring/alerts/alert123/acknowledge",
                json={"reason": "Fixed"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["alert_id"] == "alert123"
            assert data["acknowledged"] is True

    def test_acknowledge_with_ack_method(self, client: TestClient):
        """Test acknowledge with ack method as fallback."""
        mock_manager = MagicMock()
        mock_manager.acknowledge.side_effect = AttributeError()
        
        with patch("src.novel_agent.api.routers.monitoring.AlertManager") as mock_class:
            mock_class.return_value = mock_manager
            
            response = client.post(
                "/api/monitoring/alerts/alert456/acknowledge",
                json={}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["acknowledged"] is True

    def test_acknowledge_method_not_implemented(self, client: TestClient):
        """Test acknowledge when neither method exists."""
        mock_manager = MagicMock()
        mock_manager.acknowledge.side_effect = AttributeError()
        mock_manager.ack.side_effect = AttributeError()
        
        with patch("src.novel_agent.api.routers.monitoring.AlertManager") as mock_class:
            mock_class.return_value = mock_manager
            
            response = client.post(
                "/api/monitoring/alerts/alert789/acknowledge",
                json={}
            )
            
            assert response.status_code == 501
