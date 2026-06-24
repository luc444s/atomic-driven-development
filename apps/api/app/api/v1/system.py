from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from apps.api.app.api.deps import get_db_session, get_plugin_registry, get_settings_dep
from apps.api.app.core.config import Settings
from apps.api.app.core.database import check_database_connection
from apps.api.app.core.lifecycle import ensure_session_factory
from apps.api.app.kernel.auth.dependencies import require_permission
from apps.api.app.kernel.auth.models import User
from apps.api.app.kernel.plugins.manifest import PluginManifest
from apps.api.app.kernel.plugins.persistent import list_plugin_registry_records
from apps.api.app.kernel.plugins.runtime import PluginManifestRegistry

router = APIRouter(prefix="/system", tags=["system"])


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    env: str


class ReadyResponse(HealthResponse):
    plugins_loaded: int
    database_configured: bool
    database_connected: bool
    redis_configured: bool


class PluginRuntimeRecordResponse(BaseModel):
    id: str
    plugin_id: str
    name: str
    version: str
    api_version: str
    state: str
    is_enabled: bool
    backend_entrypoint: str | None
    frontend_entrypoint: str | None
    requires_json: list[str]
    permissions_json: list[str]
    events_json: list[str]
    description: str | None
    migration_version: str | None
    installed_at: datetime | None
    enabled_at: datetime | None
    disabled_at: datetime | None
    last_error: str | None
    created_at: datetime
    updated_at: datetime


def _health_payload(settings: Settings) -> HealthResponse:
    return HealthResponse(
        status="ok",
        service="api",
        version=settings.version,
        env=settings.env,
    )


@router.get("/health", response_model=HealthResponse)
def health(settings: Settings = Depends(get_settings_dep)) -> HealthResponse:
    return _health_payload(settings)


@router.get("/health/live", response_model=HealthResponse)
def live_alias(settings: Settings = Depends(get_settings_dep)) -> HealthResponse:
    return _health_payload(settings)


@router.get("/ready", response_model=ReadyResponse)
def ready(
    request: Request,
    settings: Settings = Depends(get_settings_dep),
    plugin_registry: PluginManifestRegistry = Depends(get_plugin_registry),
) -> ReadyResponse:
    database_connected = False

    try:
        database_connected = check_database_connection(ensure_session_factory(request.app))
    except Exception as exc:  # pragma: no cover - defensive path for runtime envs
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "error",
                "message": "database not ready",
                "reason": str(exc),
            },
        ) from exc

    return ReadyResponse(
        status="ok",
        service="api",
        version=settings.version,
        env=settings.env,
        plugins_loaded=len(plugin_registry.list()),
        database_configured=bool(settings.database_url),
        database_connected=database_connected,
        redis_configured=bool(settings.redis_url),
    )


@router.get("/health/ready", response_model=ReadyResponse)
def ready_alias(
    request: Request,
    settings: Settings = Depends(get_settings_dep),
    plugin_registry: PluginManifestRegistry = Depends(get_plugin_registry),
) -> ReadyResponse:
    return ready(request=request, settings=settings, plugin_registry=plugin_registry)


@router.get("/plugins", response_model=list[PluginManifest])
def list_plugins(
    _: User = Depends(require_permission("core.plugin.read")),
    plugin_registry: PluginManifestRegistry = Depends(get_plugin_registry),
) -> list[PluginManifest]:
    return plugin_registry.list()


@router.get("/plugin-runtime", response_model=list[PluginRuntimeRecordResponse])
def list_plugin_runtime(
    db: Session = Depends(get_db_session),
    _: User = Depends(require_permission("core.plugin.read")),
) -> list[PluginRuntimeRecordResponse]:
    return [
        PluginRuntimeRecordResponse.model_validate(record, from_attributes=True)
        for record in list_plugin_registry_records(db)
    ]
