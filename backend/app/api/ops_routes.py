from __future__ import annotations

import time
from typing import Dict
from fastapi import APIRouter, Depends, Query, Response, Request, HTTPException, status
import psutil

from app.api.security import require_roles
from app.core.performance import get_performance_monitor
from app.database.session import get_db_pool_metrics
from app.models.auth import AuthPrincipal, UserRole
from app.core.audit_batch_processor import get_audit_batch_processor
from app.core.resilience import get_resilience_controller
from app.models.ops import OpsPerformanceResponse
from app.core.prometheus_metrics import export_prometheus_payload
from app.services.report_builder_service import ReportBuilderService

router = APIRouter(prefix="/ops", tags=["ops"])

_RATE_LIMITS: Dict[str, float] = {}

def apply_rate_limit(request: Request, limit_per_minute: int = 60):
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()
    
    if client_ip in _RATE_LIMITS:
        # Simple token bucket or last-access cooldown
        last_request = _RATE_LIMITS[client_ip]
        min_interval = 60.0 / limit_per_minute
        if now - last_request < min_interval:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please wait.",
            )
    _RATE_LIMITS[client_ip] = now

@router.get("/metrics/live")
async def get_live_system_metrics(
    request: Request,
    api_key: str | None = Query(None, description="Static API Key for metrics auth"),
) -> dict:
    if api_key != "SIMULATED_KEY_123":
        # Simulate auth logic or require the env variable
        raise HTTPException(status_code=401, detail="Unauthorized metrics access.")
        
    apply_rate_limit(request, limit_per_minute=120)  # Need 2-3s intervals -> 30-120 reqs/min

    try:
        cpu_percent = psutil.cpu_percent(interval=None) # Non-blocking read
        mem = psutil.virtual_memory()
        
        # Sockets
        try:
            connections = len(psutil.net_connections(kind='inet'))
        except (psutil.AccessDenied, PermissionError):
            connections = 0

        return {
            "cpu": {
                "usage_percent": cpu_percent,
                "cores": psutil.cpu_count(logical=True)
            },
            "memory": {
                "total_gb": round(mem.total / (1024 ** 3), 2),
                "available_gb": round(mem.available / (1024 ** 3), 2),
                "used_gb": round(mem.used / (1024 ** 3), 2),
                "usage_percent": mem.percent
            },
            "network": {
                "active_connections": connections
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics/prometheus", include_in_schema=False)
async def get_prometheus_metrics() -> Response:
    payload, content_type = export_prometheus_payload()
    return Response(content=payload, media_type=content_type)


@router.get("/performance", response_model=OpsPerformanceResponse)
async def get_performance_dashboard(
    path: str | None = Query(default=None, description="Optional exact path filter, e.g. /api/v1/simulation/simulate"),
    include_paths: bool = Query(default=False, description="Include top slow endpoint breakdown"),
    top: int = Query(default=5, ge=1, le=20, description="Max number of slow endpoints to include"),
    _principal: AuthPrincipal = Depends(require_roles(UserRole.admin, UserRole.engineer)),
) -> OpsPerformanceResponse:
    monitor = get_performance_monitor()
    audit_batch = get_audit_batch_processor()
    resilience = get_resilience_controller()
    payload = monitor.snapshot(
        path_filter=path,
        include_path_breakdown=include_paths,
        top_paths=top,
    )
    payload["db_pool"] = get_db_pool_metrics()
    payload["caches"] = [ReportBuilderService.cache_snapshot()]
    payload["audit_batch"] = audit_batch.snapshot()
    payload["resilience"] = resilience.snapshot()
    return OpsPerformanceResponse.model_validate(payload)
