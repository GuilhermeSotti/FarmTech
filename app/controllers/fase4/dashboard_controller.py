from fastapi import APIRouter
from app.views.dashboard.dashboard import DashboardView

router = APIRouter(prefix="/dashboard", tags=["dashboard"])
dashboard = DashboardView()

@router.get("/metrics")
async def get_metrics():
    return await dashboard.get_metrics()

@router.get("/charts")
async def get_charts():
    return await dashboard.get_chart_data()
