from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from typing import Optional, List
from datetime import datetime
from enum import Enum
from app.utils.validators import (
    validate_transformer_capacity,
    validate_charger_power,
    validate_load_calculation,
    calculate_amps_from_kw,
    validate_power_factor
)
from app.config import get_settings

settings = get_settings()


class BuildingType(str, Enum):
    COMMERCIAL = "commercial"
    RESIDENTIAL = "residential"
    INDUSTRIAL = "industrial"
    MIXED_USE = "mixed_use"


class SimulationRequest(BaseModel):
    model_config = ConfigDict(str_min_length=1)

    transformer_kw: float = Field(
        ..., description="Transformer capacity in kilowatts",
        gt=0, le=settings.max_transformer_kw
    )
    peak_kw: float = Field(..., description="Current peak load in kilowatts", ge=0)
    existing_chargers: int = Field(
        default=0, description="Number of existing Level 2 chargers",
        ge=0, le=settings.max_existing_chargers
    )
    charger_power_kw: float = Field(
        default=settings.default_charger_power_kw,
        description="Power per Level 2 charger in kW",
        gt=0, le=settings.max_charger_power_kw
    )
    safety_margin_percent: float = Field(
        default=settings.default_safety_margin_percent,
        description="Safety margin buffer",
        ge=0, le=50
    )
    voltage: int = Field(
        default=settings.default_voltage,
        description="System voltage (V)"
    )
    power_factor: float = Field(
        default=settings.default_power_factor,
        description="Power factor",
        ge=0.5, le=1.0
    )
    is_three_phase: bool = Field(
        default=True,
        description="Use three-phase power calculation"
    )

    @field_validator("voltage")
    @classmethod
    def validate_voltage(cls, v):
        valid_voltages = [120, 208, 240, 480, 600]
        if v not in valid_voltages:
            raise ValueError(f"Voltage must be one of: {valid_voltages}")
        return v

    @model_validator(mode="after")
    def validate_load_balance(self):
        result = validate_load_calculation(
            self.transformer_kw,
            self.peak_kw,
            self.charger_power_kw,
            self.existing_chargers
        )
        if not result["valid"]:
            raise ValueError(result["error"])
        return self


class FeasibilityResponse(BaseModel):
    feasible: bool
    available_capacity_kw: float
    max_additional_chargers: int
    grid_utilization_percent: float
    required_upgrade: bool
    upgrade_recommendation: Optional[str] = None
    peak_load_after_addition_kw: Optional[float] = None
    load_amps: Optional[float] = Field(None, description="Peak load in Amps")
    available_amps: Optional[float] = Field(None, description="Available capacity in Amps")


class BuildingBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    address: str
    building_type: BuildingType
    transformer_kw: float = Field(..., gt=0, le=5000, description="Transformer capacity in kW")
    peak_kw: float = Field(..., ge=0, le=5000, description="Peak load in kW")
    existing_chargers: int = Field(default=0, ge=0, le=1000)
    voltage: int = Field(default=208, description="System voltage")
    power_factor: float = Field(default=0.95, ge=0.5, le=1.0)

    @field_validator("voltage")
    @classmethod
    def validate_voltage(cls, v):
        valid_voltages = [120, 208, 240, 480, 600]
        if v not in valid_voltages:
            raise ValueError(f"Voltage must be one of: {valid_voltages}")
        return v

    @model_validator(mode="after")
    def validate_building_load(self):
        result = validate_load_calculation(
            self.transformer_kw,
            self.peak_kw,
            7.2,
            self.existing_chargers
        )
        if not result["valid"]:
            raise ValueError(result["error"])
        return self


class BuildingCreate(BuildingBase):
    pass


class BuildingUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    address: Optional[str] = None
    building_type: Optional[BuildingType] = None
    transformer_kw: Optional[float] = Field(None, gt=0, le=5000)
    peak_kw: Optional[float] = Field(None, ge=0, le=5000)
    existing_chargers: Optional[int] = Field(None, ge=0, le=1000)
    voltage: Optional[int] = Field(None, description="System voltage")
    power_factor: Optional[float] = Field(None, ge=0.5, le=1.0)

    @field_validator("voltage")
    @classmethod
    def validate_voltage(cls, v):
        if v is None:
            return v
        valid_voltages = [120, 208, 240, 480, 600]
        if v not in valid_voltages:
            raise ValueError(f"Voltage must be one of: {valid_voltages}")
        return v


class BuildingResponse(BuildingBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class GridStressResponse(BaseModel):
    timestamp: datetime
    price_per_kwh: float
    grid_load_percent: float
    demand_kw: float
    status: str
    recommendation: Optional[str] = None