from __future__ import annotations

from collections.abc import Generator
from typing import Any

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from apps.api.app.core.config import Settings


class Base(DeclarativeBase):
    """Base declarativa compartida del backend."""


def register_model_metadata() -> None:
    # Carga todos los modelos del kernel para que las FKs se resuelvan
    # tambien fuera de Alembic o pytest.
    import apps.api.app.kernel.models  # noqa: F401


def build_engine(settings: Settings) -> Engine:
    register_model_metadata()
    connect_args: dict[str, Any] = {}
    if settings.database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False

    return create_engine(
        settings.database_url,
        pool_pre_ping=True,
        future=True,
        connect_args=connect_args,
    )


def build_session_factory(settings: Settings) -> sessionmaker[Session]:
    engine = build_engine(settings)
    return sessionmaker(
        bind=engine,
        class_=Session,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )


def db_session_scope(session_factory: sessionmaker[Session]) -> Generator[Session, None, None]:
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


def check_database_connection(session_factory: sessionmaker[Session]) -> bool:
    with session_factory() as session:
        session.execute(text("SELECT 1"))
    return True
