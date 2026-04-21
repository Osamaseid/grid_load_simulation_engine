from fastapi import APIRouter, HTTPException
from app.models.schemas import SimulationRequest, FeasibilityResponse
from app.services.simulation import calculate_feasibility

router = APIRouter()


@router.post("/simulate", response_model=FeasibilityResponse)
def simulate(data: SimulationRequest):
    result = calculate_feasibility(
        transformer_kw=data.transformer_kw,
        peak_kw=data.peak_kw,
        existing_chargers=data.existing_chargers,
        charger_power_kw=data.charger_power_kw,
        safety_margin_percent=data.safety_margin_percent,
        voltage=data.voltage,
        power_factor=data.power_factor,
        is_three_phase=data.is_three_phase
    )
    return result