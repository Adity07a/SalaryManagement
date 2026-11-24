"""Version 1 API router."""

from fastapi import APIRouter

from app.api.v1.analytics import router as analytics_router
from app.api.v1.employees import router as employees_router
from app.api.v1.meta import router as meta_router

api_router = APIRouter()

api_router.include_router(employees_router)
api_router.include_router(meta_router)
api_router.include_router(analytics_router)
