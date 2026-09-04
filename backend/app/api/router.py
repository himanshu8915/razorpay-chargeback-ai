"""
Root API router. Includes all route modules.
Additional routes are added in later phases.
"""

from fastapi import APIRouter

from app.api.routes.health import router as health_router
from app.api.routes.portfolio import router as portfolio_router
from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.copilot import router as copilot_router
from app.api.disputes import router as disputes_router
from app.api.v1.endpoints.decision import router as decision_router
from app.core.constants import API_V1_PREFIX

api_router = APIRouter(prefix=API_V1_PREFIX)
api_router.include_router(health_router)
api_router.include_router(portfolio_router)
api_router.include_router(dashboard_router)
api_router.include_router(copilot_router)
api_router.include_router(disputes_router)
api_router.include_router(decision_router, prefix="/decision", tags=["decision"])
