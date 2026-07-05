from fastapi import APIRouter

from app.api.v1.endpoints import auth, users, audits, capas, templates, daily_rounds, staff_reports

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(audits.router, prefix="/audits", tags=["audits"])
api_router.include_router(capas.router, prefix="/capas", tags=["capas"])
api_router.include_router(templates.router, prefix="/templates", tags=["templates"])
api_router.include_router(daily_rounds.router, prefix="/daily-rounds", tags=["daily-rounds"])
api_router.include_router(staff_reports.router, prefix="/staff-reports", tags=["staff-reports"])
