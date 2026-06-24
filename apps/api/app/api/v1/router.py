from fastapi import APIRouter

from apps.api.app.api.v1.core import router as core_router
from apps.api.app.api.v1.system import router as system_router
from apps.api.app.kernel.auth.router import router as auth_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(core_router)
api_router.include_router(system_router)
