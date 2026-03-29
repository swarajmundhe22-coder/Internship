from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import get_settings
from app.database.bootstrap import initialize_database
from app.database.session import engine

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Global Infrastructure Failure Intelligence Platform (GIFIP) backend for "
        "corrosion prediction and infrastructure risk intelligence."
    ),
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


@app.on_event("startup")
async def startup_event() -> None:
    # Ensure baseline schema and seed records are available on first run.
    if settings.auto_initialize_db:
        await initialize_database(engine)


@app.get("/", tags=["root"])
def read_root() -> dict[str, str]:
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "status": "running",
    }
