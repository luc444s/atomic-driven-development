from __future__ import annotations

from collections.abc import AsyncGenerator, Generator
from typing import Any

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from apps.api.app.core.config import Settings


class Base(DeclarativeBase):
    """Base declarativa compartida del backend."""


def register_model_metadata() -> None:
    # Carga todos los modelos del kernel para que las FKs se resuelvan
    # tambien fuera de Alembic o pytest.
    import apps.api.app.kernel.models  # noqa: F401


def _to_async_url(url: str) -> str:
    """Convierte URL sync a async (psycopg → asyncpg)."""
    return url.replace("postgresql+psycopg://", "postgresql+asyncpg://").replace(
        "postgresql://", "postgresql+asyncpg://"
    )


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


def build_async_engine(settings: Settings) -> AsyncEngine | None:
    """Crea engine async solo para PostgreSQL. SQLite no soporta async."""
    if not settings.database_url.startswith("postgresql"):
        return None
    register_model_metadata()
    async_url = _to_async_url(settings.database_url)
    return create_async_engine(
        async_url,
        pool_pre_ping=True,
        future=True,
    )


def build_async_session_factory(
    settings: Settings,
) -> async_sessionmaker[AsyncSession] | None:
    engine = build_async_engine(settings)
    if engine is None:
        return None
    return async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
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


async def async_db_session_scope(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncSession, None]:
    async with session_factory() as session:
        yield session


def check_database_connection(session_factory: sessionmaker[Session]) -> bool:
    with session_factory() as session:
        session.execute(text("SELECT 1"))
    return True
