from pydantic import validator, Field, field_validator
from pydantic import BaseModel as PydanticBaseModel
from typing import Optional, ClassVar
from enum import Enum


class VoltageLevel(str, Enum):
    VOLTAGE_120 = "120V"
    VOLTAGE_208 = "208V"
    VOLTAGE_240 = "240V"
    VOLTAGE_480 = "480V"


class UnitType(str, Enum):
    KILOWATTS = "kW"
    KILOWATT_HOURS = "kWh"
    AMPS = "A"
    VOLTS = "V"
    PERCENT = "%"


class EngineeringUnitsMixin:
    @field_validator("*", mode="before")
    @classmethod
    def strip_whitespace(cls, v):
        if isinstance(v, str):
            return v.strip()
        return v


class PowerValidator:
    MIN_KW: ClassVar[float] = 0.1
    MAX_KW: ClassVar[float] = 10000.0
    
    @classmethod
    def validate_kw(cls, value: float, field_name: str = "power") -> float:
        if value <= 0:
            raise ValueError(f"{field_name} must be positive (got {value} kW)")
        if value > cls.MAX_KW:
            raise ValueError(f"{field_name} exceeds maximum ({value} kW > {cls.MAX_KW} kW)")
        return round(value, 2)


class CurrentValidator:
    MIN_AMPS: ClassVar[float] = 0.1
    MAX_AMPS: ClassVar[float] = 4000.0
    
    @classmethod
    def validate_amps(cls, value: float, field_name: str = "current") -> float:
        if value <= 0:
            raise ValueError(f"{field_name} must be positive (got {value} A)")
        if value > cls.MAX_AMPS:
            raise ValueError(f"{field_name} exceeds maximum ({value} A > {cls.MAX_AMPS} A)")
        return round(value, 2)


class VoltageValidator:
    VALID_VOLTAGES: ClassVar[list] = [120, 208, 240, 480, 600]
    
    @classmethod
    def validate_volts(cls, value: float, field_name: str = "voltage") -> float:
        if value <= 0:
            raise ValueError(f"{field_name} must be positive (got {value} V)")
        if value not in cls.VALID_VOLTAGES:
            raise ValueError(
                f"{field_name} must be one of standard voltages: {cls.VALID_VOLTAGES} (got {value} V)"
            )
        return int(value)


def validate_power_factor(pf: float) -> float:
    if not 0.5 <= pf <= 1.0:
        raise ValueError(f"Power factor must be between 0.5 and 1.0 (got {pf})")
    return round(pf, 3)


def validate_transformer_capacity(kw: float) -> float:
    standard_sizes = [15, 25, 37.5, 50, 75, 100, 150, 225, 300, 500, 750, 1000, 1500, 2000]
    
    if kw < 15:
        raise ValueError(f"Transformer capacity too small (minimum 15kW, got {kw}kW)")
    if kw > 5000:
        raise ValueError(f"Transformer capacity exceeds practical limit (maximum 5000kW, got {kw}kW)")
    
    return round(kw, 1)


def validate_charger_power(kw: float) -> float:
    standard_levels = {
        "Level 1": 1.4,
        "Level 2": [7.2, 9.6, 11.5, 19.2],
        "DC Fast": [50, 100, 150, 200, 350]
    }
    
    if kw > 350:
        raise ValueError(f"Charger power exceeds DC fast charging max (got {kw}kW)")
    
    return round(kw, 1)


def calculate_amps_from_kw(kw: float, volts: int) -> float:
    if volts == 0:
        raise ValueError("Voltage cannot be zero")
    return round((kw * 1000) / volts, 2)


def calculate_kw_from_amps(amps: float, volts: int) -> float:
    if volts == 0:
        raise ValueError("Voltage cannot be zero")
    return round((amps * volts) / 1000, 2)


def validate_load_calculation(
    transformer_kw: float,
    peak_kw: float,
    charger_kw: float,
    num_chargers: int
) -> dict:
    total_charger_load = charger_kw * num_chargers
    proposed_total = peak_kw + total_charger_load
    
    if proposed_total > transformer_kw * 1.25:
        return {
            "valid": False,
            "error": f"Overload: proposed load ({proposed_total}kW) exceeds 125% of transformer capacity ({transformer_kw}kW)",
            "headroom_kw": round(transformer_kw - peak_kw, 2)
        }
    
    return {
        "valid": True,
        "proposed_load_kw": round(proposed_total, 2),
        "headroom_kw": round(transformer_kw - proposed_total, 2),
        "utilization_percent": round((proposed_total / transformer_kw) * 100, 1)
    }
