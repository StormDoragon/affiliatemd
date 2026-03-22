from fastapi import FastAPI

from . import models
from .config import settings
from .db import Base, engine
from .routers import content, earnings, scans, users

app = FastAPI(
	title=settings.app_name,
	version=settings.app_version,
	docs_url="/docs",
	redoc_url="/redoc",
)

app.include_router(users.router)
app.include_router(content.router)
app.include_router(scans.router)
app.include_router(earnings.router)


@app.on_event("startup")
def on_startup() -> None:
	# Development convenience: create tables if migrations were not run yet.
	Base.metadata.create_all(bind=engine)


@app.get("/healthz", tags=["health"])
def healthcheck() -> dict[str, str]:
	return {"status": "ok"}
