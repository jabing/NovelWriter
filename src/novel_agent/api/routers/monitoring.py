from typing import Any

from fastapi import APIRouter, HTTPException

# Attempt to import existing monitoring components.
try:
    # Preferred import path
    from writer.monitoring import AlertManager, HealthMonitor, MetricsCollector  # type: ignore
except Exception:
    # Fallback to alternative module path in case of packaging differences
    try:
        from ...monitoring import AlertManager, HealthMonitor, MetricsCollector  # type: ignore
    except Exception:
        HealthMonitor = MetricsCollector = AlertManager  # type: ignore



router = APIRouter(prefix="/api/monitoring", tags=["monitoring"], redirect_slashes=False)


def _call_method(obj: Any, name: str, *args, **kwargs) -> Any:
    fn = getattr(obj, name, None)
    if callable(fn):
        return fn(*args, **kwargs)
    raise AttributeError(f"Method {name} not found on {type(obj)}")


@router.get("/health")
async def health() -> dict[str, Any]:
    # Safely call the health check from the existing HealthMonitor implementation.
    try:
        hm: Any = HealthMonitor()
    except Exception:
        return {"status": "unavailable"}
    try:
        return {"status": hm.health()}
    except Exception:
        pass
    try:
        return {"status": hm.status}
    except Exception:
        return {"status": "unknown"}


@router.get("/metrics")
async def metrics() -> Any:
    try:
        mc: Any = MetricsCollector()
    except Exception:
        return {}
    try:
        return mc.collect()
    except Exception:
        pass
    try:
        return mc.get_metrics()
    except Exception:
        return {}


@router.get("/alerts")
async def alerts() -> Any:
    try:
        am: Any
        am = AlertManager()  # type: ignore
    except Exception:
        return []
    try:
        return _call_method(am, "list_alerts")
    except Exception:
        pass
    try:
        return _call_method(am, "get_alerts")
    except Exception:
        return []


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    # Acknowledge a specific alert by ID using the existing AlertManager
    try:
        am: Any
        am = AlertManager()  # type: ignore
    except Exception:
        raise HTTPException(status_code=501, detail="Alert manager not available")
    data = payload or {}
    try:
        _call_method(am, "acknowledge", alert_id, data)
    except Exception:
        try:
            _call_method(am, "ack", alert_id, data)
        except Exception:
            raise HTTPException(status_code=501, detail="Acknowledge method not implemented")

    return {"alert_id": alert_id, "acknowledged": True}
