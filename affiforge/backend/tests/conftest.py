import os
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy.engine import make_url

scratch = TemporaryDirectory(prefix="affiforge-tests-")
test_database = os.environ.get("TEST_DATABASE_URL")
if test_database:
    url = make_url(test_database)
    if url.get_backend_name() != "postgresql" or not (url.database or "").endswith("_test"):
        raise ValueError(
            "TEST_DATABASE_URL must point to a disposable PostgreSQL database ending in _test"
        )
os.environ["DATABASE_URL"] = test_database or f"sqlite:///{scratch.name}/test.db"
os.environ["ENVIRONMENT"] = "test"
os.environ["DEMO_MODE"] = "true"
os.environ["ALLOW_REGISTRATION"] = "true"
os.environ["ENABLE_API_GUARDRAILS"] = "false"

from src.db import Base, engine
from src.main import app


@pytest.fixture(scope="session", autouse=True)
def migrate_schema():
    config = Config(str(Path(__file__).parents[1] / "alembic.ini"))
    config.set_main_option("script_location", str(Path(__file__).parents[1] / "alembic"))
    command.upgrade(config, "head")
    yield
    engine.dispose()
    scratch.cleanup()


@pytest.fixture(autouse=True)
def reset_db() -> None:
    with engine.begin() as connection:
        for table in reversed(Base.metadata.sorted_tables):
            connection.execute(table.delete())


@pytest.fixture
def client() -> TestClient:
    with TestClient(app) as instance:
        yield instance
