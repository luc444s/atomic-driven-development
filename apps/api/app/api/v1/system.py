from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from apps.api.app.api.deps import get_plugin_registry, get_settings_dep
from apps.api.app.core.config import Settings
from apps.api.app.core.database import check_database_connection
from apps.api.app.core.lifecycle import ensure_session_factory
from apps.api.app.kernel.auth.dependencies import require_permission
from apps.api.app.kernel.auth.models import User
from apps.api.app.kernel.plugins.manifest import PluginManifest
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
