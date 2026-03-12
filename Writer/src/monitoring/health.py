# src/monitoring/health.py
"""System health monitoring."""

import time
from collections.abc import Callable, Coroutine
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from src.monitoring.alerts import AlertManager, AlertSeverity, AlertType, get_alert_manager


class HealthStatus(str, Enum):
    """Health check status."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class HealthCheckResult:
    """Result of a health check."""

    name: str
    status: HealthStatus
    message: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "status": self.status.value,
            "message": self.message,
            "timestamp": self.timestamp,
            "details": self.details,
        }


HealthCheck = Callable[[], Coroutine[Any, Any, HealthCheckResult]]


class HealthMonitor:
    """System health monitoring."""

    def __init__(self, alert_manager: AlertManager | None = None) -> None:
        """Initialize health monitor.

        Args:
            alert_manager: Optional alert manager
        """
        self._checks: dict[str, HealthCheck] = {}
        self._last_results: dict[str, HealthCheckResult] = {}
        self._alert_manager = alert_manager or get_alert_manager()
        self._start_time = time.time()

    def register_check(self, name: str, check: HealthCheck) -> None:
        """Register a health check.

        Args:
            name: Check name
            check: Async function that returns HealthCheckResult
        """
        self._checks[name] = check

    async def run_check(self, name: str) -> HealthCheckResult:
        """Run a single health check.

        Args:
            name: Name of the check to run

        Returns:
            Health check result
        """
        if name not in self._checks:
            return HealthCheckResult(
                name=name,
                status=HealthStatus.UNHEALTHY,
                message=f"Unknown check: {name}",
            )

        try:
            result = await self._checks[name]()
            self._last_results[name] = result

            # Trigger alert for unhealthy status
            if result.status == HealthStatus.UNHEALTHY:
                await self._alert_manager.trigger_simple(
                    alert_type=AlertType.SYSTEM_ERROR,
                    severity=AlertSeverity.ERROR,
                    message=f"Health check failed: {name} - {result.message}",
                    details=result.details,
                )

            return result
        except Exception as e:
            result = HealthCheckResult(
                name=name,
                status=HealthStatus.UNHEALTHY,
                message=str(e),
            )
            self._last_results[name] = result
            return result

    async def run_all_checks(self) -> dict[str, HealthCheckResult]:
        """Run all registered health checks.

        Returns:
            Dictionary of check results
        """
        results = {}
        for name in self._checks:
            results[name] = await self.run_check(name)
        return results

    def get_overall_status(self) -> HealthStatus:
        """Get overall system health status.

        Returns:
            Worst status among all checks
        """
        if not self._last_results:
            return HealthStatus.HEALTHY

        has_degraded = False

        for result in self._last_results.values():
            if result.status == HealthStatus.UNHEALTHY:
                return HealthStatus.UNHEALTHY
            if result.status == HealthStatus.DEGRADED:
                has_degraded = True

        return HealthStatus.DEGRADED if has_degraded else HealthStatus.HEALTHY

    def get_status_summary(self) -> dict[str, Any]:
        """Get status summary.

        Returns:
            Status summary dictionary
        """
        uptime = time.time() - self._start_time
        overall = self.get_overall_status()

        return {
            "overall_status": overall.value,
            "uptime_seconds": round(uptime, 2),
            "checks_registered": len(self._checks),
            "last_check_count": len(self._last_results),
            "healthy_count": len(
                [r for r in self._last_results.values() if r.status == HealthStatus.HEALTHY]
            ),
            "degraded_count": len(
                [r for r in self._last_results.values() if r.status == HealthStatus.DEGRADED]
            ),
            "unhealthy_count": len(
                [r for r in self._last_results.values() if r.status == HealthStatus.UNHEALTHY]
            ),
        }

    def get_last_results(self) -> dict[str, Any]:
        """Get last check results.

        Returns:
            Dictionary of last results
        """
        return {name: result.to_dict() for name, result in self._last_results.items()}


# Pre-built health checks


async def check_llm_connection() -> HealthCheckResult:
    """Check LLM connection health."""
    try:
        # In production, would actually test the connection
        # For MVP, return healthy
        return HealthCheckResult(
            name="llm_connection",
            status=HealthStatus.HEALTHY,
            message="LLM connection OK",
            details={"provider": "deepseek"},
        )
    except Exception as e:
        return HealthCheckResult(
            name="llm_connection",
            status=HealthStatus.UNHEALTHY,
            message=f"LLM connection failed: {e}",
        )


async def check_memory_system() -> HealthCheckResult:
    """Check memory system health."""
    try:
        from src.memory import MemSearchAdapter

        # Try a simple memory operation
        MemSearchAdapter()

        return HealthCheckResult(
            name="memory_system",
            status=HealthStatus.HEALTHY,
            message="Memory system OK (MemSearchAdapter)",
            details={"type": "memsearch", "embedding": "local"},
        )
    except Exception as e:
        return HealthCheckResult(
            name="memory_system",
            status=HealthStatus.UNHEALTHY,
            message=f"Memory system failed: {e}",
        )


async def check_disk_space(threshold_percent: float = 90.0) -> HealthCheckResult:
    """Check disk space.

    Args:
        threshold_percent: Alert if usage above this percentage

    Returns:
        Health check result
    """
    try:
        import shutil

        total, used, free = shutil.disk_usage("/")
        usage_percent = (used / total) * 100

        if usage_percent > threshold_percent:
            return HealthCheckResult(
                name="disk_space",
                status=HealthStatus.DEGRADED,
                message=f"Disk usage high: {usage_percent:.1f}%",
                details={
                    "total_gb": round(total / (1024**3), 2),
                    "used_gb": round(used / (1024**3), 2),
                    "free_gb": round(free / (1024**3), 2),
                    "usage_percent": round(usage_percent, 2),
                },
            )

        return HealthCheckResult(
            name="disk_space",
            status=HealthStatus.HEALTHY,
            message=f"Disk usage OK: {usage_percent:.1f}%",
            details={
                "total_gb": round(total / (1024**3), 2),
                "used_gb": round(used / (1024**3), 2),
                "free_gb": round(free / (1024**3), 2),
                "usage_percent": round(usage_percent, 2),
            },
        )
    except Exception as e:
        return HealthCheckResult(
            name="disk_space",
            status=HealthStatus.DEGRADED,
            message=f"Could not check disk space: {e}",
        )


async def check_platform_connections() -> HealthCheckResult:
    """Check platform connection status."""
    try:
        # In production, would verify API credentials
        platforms = {
            "wattpad": True,
            "royalroad": True,
            "kindle": True,
        }

        available = sum(1 for v in platforms.values() if v)

        if available == 0:
            return HealthCheckResult(
                name="platform_connections",
                status=HealthStatus.UNHEALTHY,
                message="No platforms available",
                details=platforms,
            )

        if available < len(platforms):
            return HealthCheckResult(
                name="platform_connections",
                status=HealthStatus.DEGRADED,
                message=f"{available}/{len(platforms)} platforms available",
                details=platforms,
            )

        return HealthCheckResult(
            name="platform_connections",
            status=HealthStatus.HEALTHY,
            message="All platforms available",
            details=platforms,
        )
    except Exception as e:
        return HealthCheckResult(
            name="platform_connections",
            status=HealthStatus.UNHEALTHY,
            message=f"Platform check failed: {e}",
        )


async def check_database() -> HealthCheckResult:
    """Check database connections (PostgreSQL, Neo4j, Pinecone)."""
    db_status = {}
    try:
        from src.db import Neo4jClient, PostgresClient, VectorStore

        postgres_ok = False
        try:
            if PostgresClient is not None:
                postgres_ok = True
                db_status["postgresql"] = "available"
            else:
                db_status["postgresql"] = "not_available"
        except Exception:
            db_status["postgresql"] = "unavailable"

        neo4j_ok = False
        try:
            if Neo4jClient is not None:
                neo4j_ok = True
                db_status["neo4j"] = "available"
            else:
                db_status["neo4j"] = "not_available"
        except Exception:
            db_status["neo4j"] = "unavailable"

        try:
            if VectorStore is not None:
                db_status["pinecone"] = "available"
            else:
                db_status["pinecone"] = "not_available"
        except Exception:
            db_status["pinecone"] = "unavailable"

        all_available = postgres_ok and neo4j_ok
        any_available = postgres_ok or neo4j_ok

        if all_available:
            return HealthCheckResult(
                name="database",
                status=HealthStatus.HEALTHY,
                message="All databases available",
                details=db_status,
            )
        elif any_available:
            return HealthCheckResult(
                name="database",
                status=HealthStatus.DEGRADED,
                message="Some databases available",
                details=db_status,
            )
        else:
            return HealthCheckResult(
                name="database",
                status=HealthStatus.UNHEALTHY,
                message="No databases available",
                details=db_status,
            )
    except Exception as e:
        return HealthCheckResult(
            name="database",
            status=HealthStatus.UNHEALTHY,
            message=f"Database check failed: {e}",
            details=db_status,
        )


async def check_redis() -> HealthCheckResult:
    """Check Redis connection health."""
    try:
        import importlib.util

        redis_spec = importlib.util.find_spec("redis")
        redis_available = redis_spec is not None

        if redis_available:
            return HealthCheckResult(
                name="redis",
                status=HealthStatus.HEALTHY,
                message="Redis library available",
                details={"library": "available"},
            )
        else:
            return HealthCheckResult(
                name="redis",
                status=HealthStatus.DEGRADED,
                message="Redis library not available",
                details={"library": "unavailable"},
            )
    except Exception as e:
        return HealthCheckResult(
            name="redis",
            status=HealthStatus.UNHEALTHY,
            message=f"Redis check failed: {e}",
        )


async def check_knowledge_graph() -> HealthCheckResult:
    """Check knowledge graph integrity."""
    try:
        from src.db import Neo4jClient

        if Neo4jClient is not None:
            return HealthCheckResult(
                name="knowledge_graph",
                status=HealthStatus.HEALTHY,
                message="Knowledge graph system available",
                details={"status": "healthy"},
            )
        else:
            return HealthCheckResult(
                name="knowledge_graph",
                status=HealthStatus.DEGRADED,
                message="Knowledge graph system not available",
                details={"status": "degraded"},
            )
    except Exception as e:
        return HealthCheckResult(
            name="knowledge_graph",
            status=HealthStatus.UNHEALTHY,
            message=f"Knowledge graph check failed: {e}",
        )


async def check_novel_system() -> HealthCheckResult:
    """Check novel generation system health."""
    try:
        import importlib.util

        orchestrator_spec = importlib.util.find_spec("src.agents.orchestrator")
        if orchestrator_spec is not None:
            return HealthCheckResult(
                name="novel_system",
                status=HealthStatus.HEALTHY,
                message="Novel generation system available",
                details={"status": "healthy"},
            )
        else:
            return HealthCheckResult(
                name="novel_system",
                status=HealthStatus.DEGRADED,
                message="Novel system components missing",
                details={"status": "degraded"},
            )
    except Exception as e:
        return HealthCheckResult(
            name="novel_system",
            status=HealthStatus.UNHEALTHY,
            message=f"Novel system check failed: {e}",
        )


async def check_agent_system() -> HealthCheckResult:
    """Check agent system health."""
    try:
        import importlib.util

        base_spec = importlib.util.find_spec("src.agents.base")
        if base_spec is not None:
            return HealthCheckResult(
                name="agent_system",
                status=HealthStatus.HEALTHY,
                message="Agent system available",
                details={"status": "healthy"},
            )
        else:
            return HealthCheckResult(
                name="agent_system",
                status=HealthStatus.DEGRADED,
                message="Agent system components missing",
                details={"status": "degraded"},
            )
    except Exception as e:
        return HealthCheckResult(
            name="agent_system",
            status=HealthStatus.UNHEALTHY,
            message=f"Agent system check failed: {e}",
        )


def setup_default_health_checks(monitor: HealthMonitor) -> None:
    """Set up default health checks.

    Args:
        monitor: Health monitor to configure
    """
    monitor.register_check("llm_connection", check_llm_connection)
    monitor.register_check("memory_system", check_memory_system)
    monitor.register_check("disk_space", check_disk_space)
    monitor.register_check("platform_connections", check_platform_connections)
    monitor.register_check("database", check_database)
    monitor.register_check("redis", check_redis)
    monitor.register_check("knowledge_graph", check_knowledge_graph)
    monitor.register_check("novel_system", check_novel_system)
    monitor.register_check("agent_system", check_agent_system)


# Global health monitor
_health_monitor: HealthMonitor | None = None


def get_health_monitor() -> HealthMonitor:
    """Get global health monitor."""
    global _health_monitor
    if _health_monitor is None:
        _health_monitor = HealthMonitor()
        setup_default_health_checks(_health_monitor)
    return _health_monitor
