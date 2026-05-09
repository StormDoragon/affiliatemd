from fastapi import FastAPI

from . import models
from .config import settings
from .db import Base, engine
from .routers import billing, content, earnings, generator, scans, sites, users

app = FastAPI(
	title=settings.app_name,
	version=settings.app_version,
	docs_url="/docs",
	redoc_url="/redoc",
)

app.include_router(users.router)
app.include_router(sites.router)
app.include_router(generator.router)
app.include_router(content.router)
app.include_router(scans.router)
app.include_router(earnings.router)
app.include_router(billing.router)


@app.on_event("startup")
def on_startup() -> None:
	# Development convenience: create tables if migrations were not run yet.
	Base.metadata.create_all(bind=engine)


def _health_payload() -> dict[str, str]:
	return {"status": "ok"}


@app.get("/healthz", tags=["health"])
def healthcheck() -> dict[str, str]:
	return _health_payload()


@app.get("/health", tags=["health"])
def healthcheck_legacy() -> dict[str, str]:
	return _health_payload()
