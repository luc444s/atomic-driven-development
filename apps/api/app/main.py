from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from systutor.core.errors import register_exception_handlers
from systutor.core.lifecycle import bootstrap_app_state, lifespan
from systutor.core.logging import configure_logging
from systutor.core.request_context import RequestContextMiddleware

from apps.api.app.api.v1.router import api_router
from apps.api.app.config import get_settings
from systutor.core.config import Settings


def create_app(settings: Settings | None = None) -> FastAPI:
    effective_settings = settings or get_settings()
    configure_logging(effective_settings.log_level)

    app = FastAPI(
        title=effective_settings.app_name,
        version=effective_settings.version,
        debug=effective_settings.debug,
        lifespan=lifespan,
    )
    bootstrap_app_state(app, effective_settings)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=effective_settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestContextMiddleware)
    app.include_router(api_router, prefix=effective_settings.api_prefix)
    register_exception_handlers(app)
    return app


app = create_app()
