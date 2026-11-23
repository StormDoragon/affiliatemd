from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from redis import Redis, RedisError
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from .config import settings
from .db import engine
from .routers import billing, content, earnings, generator, scans, sites, users

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    docs_url=None if settings.production else "/docs",
    openapi_url=None if settings.production else "/openapi.json",
    redoc_url=None if settings.production else "/redoc",
    redirect_slashes=False,
)

for api_router in (users, sites, generator, content, scans, earnings, billing):
    app.include_router(api_router.router)


@app.exception_handler(RequestValidationError)
async def validation_error(_: Request, error: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        {"detail": [{"loc": item["loc"], "msg": item["msg"]} for item in error.errors()]},
        status_code=422,
    )


@app.get("/healthz", tags=["health"])
@app.get("/health", tags=["health"])
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/readyz", tags=["health"])
def readiness() -> dict[str, str]:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT id, published_url FROM content_items WHERE 1=0"))
        if settings.production:
            Redis.from_url(settings.redis_url, socket_timeout=2, socket_connect_timeout=2).ping()
    except (SQLAlchemyError, RedisError) as exc:
        raise HTTPException(503, "Required services are unavailable") from exc
    return {"status": "ready"}
