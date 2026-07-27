from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine
from sqlalchemy.orm import Session

import apps.api.app.kernel.models  # noqa: F401
import plugins.crm.backend.models  # noqa: F401
import plugins.logistics.backend.models  # noqa: F401
import plugins.productos.backend.models  # noqa: F401
import plugins.stock.backend.models  # noqa: F401
import plugins.ventas.cotizacion.backend.models  # noqa: F401
from apps.api.app.commands.seed_demo import seed_demo_data
from apps.api.app.core.config import Settings
from apps.api.app.core.database import Base, build_engine, build_session_factory
from apps.api.app.main import create_app

PROJECT_ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture()
def test_settings(tmp_path: Path) -> Settings:
    database_path = tmp_path / "systutor_test.db"
    return Settings(
        app_name="SYSTUTOR OSS API Test",
        env="test",
        debug=True,
        version="0.2.0-test",
        api_prefix="/api/v1",
        log_level="WARNING",
        database_url=f"sqlite+pysqlite:///{database_path}",
        redis_url="redis://localhost:6379/15",
        outbox_dispatch_batch_size=25,
        outbox_max_retries=2,
        jwt_secret_key="test-secret-key",
        jwt_access_token_ttl_minutes=30,
        plugins_dir=PROJECT_ROOT / "plugins",
        seed_demo_tenant_name="Demo Tenant",
        seed_demo_tenant_slug="demo",
        seed_demo_branch_name="Main Branch",
        seed_demo_branch_code="MAIN",
        seed_admin_email="admin@example.com",
        seed_admin_password="ChangeMe123!",
        seed_admin_full_name="System Admin",
    )


@pytest.fixture()
def engine(test_settings: Settings) -> Generator[Engine, None, None]:
    engine = build_engine(test_settings)
    Base.metadata.create_all(bind=engine)
    try:
        yield engine
    finally:
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture()
def app(test_settings: Settings, engine: Engine):
    app = create_app(test_settings)
    app.state.session_factory = build_session_factory(test_settings)
    return app


@pytest.fixture()
def client(app):
    with TestClient(app) as client:
        yield client


@pytest.fixture()
def db_session(app) -> Generator[Session, None, None]:
    session_factory = app.state.session_factory
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def seeded_demo(app, db_session: Session) -> dict[str, str]:
    return seed_demo_data(db_session, app.state.settings, app.state.plugin_runtime.list_results())
