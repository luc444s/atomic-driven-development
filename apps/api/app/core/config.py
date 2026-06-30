from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Literal, cast

from pydantic import BaseModel, Field

PROJECT_ROOT = Path(__file__).resolve().parents[4]


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


class Settings(BaseModel):
    app_name: str = "SYSTUTOR OSS API"
    env: Literal["local", "development", "test", "production"] = "local"
    debug: bool = False
    version: str = "0.1.0"
    api_prefix: str = "/api/v1"
    log_level: str = "INFO"
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/systutor"
    redis_url: str = "redis://localhost:6379/0"
    outbox_dispatch_batch_size: int = 100
    outbox_max_retries: int = 3
    jwt_secret_key: str = "change-me"
    jwt_access_token_ttl_minutes: int = 60
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:5173", "http://127.0.0.1:5173", "http://192.168.18.9:5173"]
    )
    plugins_dir: Path = Field(default_factory=lambda: PROJECT_ROOT / "plugins")
    seed_demo_tenant_name: str = "Demo Tenant"
    seed_demo_tenant_slug: str = "demo"
    seed_demo_branch_name: str = "Main Branch"
    seed_demo_branch_code: str = "MAIN"
    seed_admin_email: str = "admin@example.com"
    seed_admin_password: str = "ChangeMe123!"
    seed_admin_full_name: str = "System Admin"


@lru_cache
def get_settings() -> Settings:
    cors_origins = _split_csv(
        os.getenv(
            "SYSTUTOR_CORS_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173,http://192.168.18.9:5173",
        )
    )
    return Settings(
        app_name=os.getenv("SYSTUTOR_APP_NAME", "SYSTUTOR OSS API"),
        env=cast(
            Literal["local", "development", "test", "production"],
            os.getenv("SYSTUTOR_ENV", "local"),
        ),
        debug=os.getenv("SYSTUTOR_DEBUG", "false").lower() in {"1", "true", "yes", "on"},
        version=os.getenv("SYSTUTOR_VERSION", "0.1.0"),
        api_prefix=os.getenv("SYSTUTOR_API_PREFIX", "/api/v1"),
        log_level=os.getenv("SYSTUTOR_LOG_LEVEL", "INFO"),
        database_url=os.getenv(
            "SYSTUTOR_DATABASE_URL",
            "postgresql+psycopg://postgres:postgres@localhost:5432/systutor",
        ),
        redis_url=os.getenv("SYSTUTOR_REDIS_URL", "redis://localhost:6379/0"),
        outbox_dispatch_batch_size=int(os.getenv("SYSTUTOR_OUTBOX_DISPATCH_BATCH_SIZE", "100")),
        outbox_max_retries=int(os.getenv("SYSTUTOR_OUTBOX_MAX_RETRIES", "3")),
        jwt_secret_key=os.getenv("SYSTUTOR_JWT_SECRET_KEY", "change-me"),
        jwt_access_token_ttl_minutes=int(os.getenv("SYSTUTOR_JWT_ACCESS_TOKEN_TTL_MINUTES", "60")),
        cors_origins=cors_origins,
        plugins_dir=Path(os.getenv("SYSTUTOR_PLUGINS_DIR", str(PROJECT_ROOT / "plugins"))),
        seed_demo_tenant_name=os.getenv("SYSTUTOR_SEED_TENANT_NAME", "Demo Tenant"),
        seed_demo_tenant_slug=os.getenv("SYSTUTOR_SEED_TENANT_SLUG", "demo"),
        seed_demo_branch_name=os.getenv("SYSTUTOR_SEED_BRANCH_NAME", "Main Branch"),
        seed_demo_branch_code=os.getenv("SYSTUTOR_SEED_BRANCH_CODE", "MAIN"),
        seed_admin_email=os.getenv("SYSTUTOR_SEED_ADMIN_EMAIL", "admin@example.com"),
        seed_admin_password=os.getenv("SYSTUTOR_SEED_ADMIN_PASSWORD", "ChangeMe123!"),
        seed_admin_full_name=os.getenv("SYSTUTOR_SEED_ADMIN_FULL_NAME", "System Admin"),
    )
