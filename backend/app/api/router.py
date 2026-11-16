from fastapi import APIRouter

from backend.app.modules.academic.router import router as academic_router
from backend.app.modules.academic.router import unidades_router
from backend.app.modules.health.router import router as health_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(academic_router, tags=["academic"])
api_router.include_router(unidades_router, tags=["academic"])
