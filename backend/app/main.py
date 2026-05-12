import uuid
import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, JSONResponse

from app.api.router import api_router
from app.core.audit_batch_processor import get_audit_batch_processor
from app.core.config import get_settings
from app.core.performance import get_performance_monitor
from app.core.prometheus_metrics import observe_request
from app.core.resilience import get_resilience_controller
from app.database.bootstrap import initialize_database
from app.database.session import engine
from app.core.logging import setup_logging, get_logger, set_correlation_id, reset_correlation_id

settings = get_settings()
setup_logging(settings.environment == "development" and "DEBUG" or "INFO")
logger = get_logger("gifip.main")
performance_monitor = get_performance_monitor()
audit_batch_processor = get_audit_batch_processor()
resilience_controller = get_resilience_controller()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Global Infrastructure Failure Intelligence Platform (GIFIP) backend for "
        "corrosion prediction and infrastructure risk intelligence."
    ),
)

# Correlation ID Middleware
@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    request.state.correlation_id = correlation_id
    correlation_token = set_correlation_id(correlation_id)

    start_time = time.perf_counter()
    response: Response | None = None
    status_code = 500
    admitted = False
    shed_reason: str | None = None
    try:
        admitted, shed_reason = resilience_controller.admit(path=request.url.path)
        if not admitted:
            status_code = 503
            response = JSONResponse(
                status_code=status_code,
                content={
                    "detail": {
                        "code": "request_shed",
                        "reason": shed_reason or "overload",
                        "message": "Request was shed by resilience controls; retry shortly.",
                    }
                },
            )
            response.headers["Retry-After"] = str(settings.resilience_retry_after_seconds)
            return response

        response = await call_next(request)
        status_code = response.status_code
        return response
    finally:
        process_time = (time.perf_counter() - start_time) * 1000

        if admitted:
            resilience_controller.release(
                path=request.url.path,
                status_code=status_code,
                latency_ms=process_time,
            )

        performance_monitor.record_request(
            method=request.method,
            path=request.url.path,
            status_code=status_code,
            latency_ms=process_time,
        )
        if settings.prometheus_metrics_enabled:
            route = request.scope.get("route")
            route_path = getattr(route, "path", request.url.path)
            observe_request(
                method=request.method,
                path=route_path,
                status_code=status_code,
                latency_ms=process_time,
            )

        if response is not None:
            response.headers["X-Correlation-ID"] = correlation_id
            response.headers["X-Process-Time-Ms"] = f"{process_time:.2f}"

        logger.info(
            "Handled request",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": status_code,
                "duration_ms": process_time,
                "request_shed": not admitted,
                "shed_reason": shed_reason,
            },
        )
        reset_correlation_id(correlation_token)

# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True, extra={
        "correlation_id": correlation_id,
        "path": request.url.path
    })
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal Server Error",
            "correlation_id": correlation_id,
            "message": "An unexpected error occurred. Please contact support with the correlation ID."
        }
    )

# Allow local frontend origins to call the API in browser-based development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://localhost:3000",
        "https://127.0.0.1:3000",
    ],
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1|\[::1\])(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.middleware("http")
async def security_headers_middleware(request, call_next):
    response: Response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    response.headers.setdefault("Permissions-Policy", "geolocation=(), camera=(), microphone=()")
    response.headers.setdefault("Content-Security-Policy", "default-src 'none'; frame-ancestors 'none'; base-uri 'none'")
    return response


@app.on_event("startup")
async def startup_event() -> None:
    await audit_batch_processor.start()
    # Ensure baseline schema and seed records are available on first run.
    if settings.auto_initialize_db:
        await initialize_database(engine)


@app.on_event("shutdown")
async def shutdown_event() -> None:
    await audit_batch_processor.stop()


@app.get("/", tags=["root"])
def read_root() -> dict[str, str]:
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "status": "running",
    }
