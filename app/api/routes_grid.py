from fastapi import APIRouter, Query
from typing import Optional
from app.services.grid_stress import get_grid_stress
from app.models.schemas import GridStressResponse

router = APIRouter()


@router.get("/grid/stress", response_model=GridStressResponse)
def get_current_grid_stress(
    building_demand_kw: Optional[float] = Query(None, description="Optional building demand to calculate grid impact")
):
    return get_grid_stress(base_demand_kw=building_demand_kw)


@router.get("/grid/forecast", response_model=list[GridStressResponse])
def get_grid_forecast(hours: int = Query(24, ge=1, le=72)):
    forecast = []
    for _ in range(hours):
        forecast.append(get_grid_stress())
    return forecast