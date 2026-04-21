import logging
from math import floor, ceil
from typing import Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ElectricalParams:
    transformer_kw: float
    peak_kw: float
    existing_chargers: int
    charger_power_kw: float
    safety_margin_percent: float
    voltage: int
    demand_factor: float = 0.8
    diversity_factor: float = 1.25


def calculate_three_phase_amps(kw: float, volts: int) -> float:
    if volts == 0:
        raise ValueError("Voltage cannot be zero")
    return round((kw * 1000) / (volts * 1.732), 2)


def calculate_single_phase_amps(kw: float, volts: int) -> float:
    if volts == 0:
        raise ValueError("Voltage cannot be zero")
    return round((kw * 1000) / volts, 2)


def calculate_apparent_power(kw: float, power_factor: float = 0.95) -> float:
    return round(kw / power_factor, 2)


def apply_demand_factor(load_kw: float, demand_factor: float = 0.8) -> float:
    return round(load_kw * demand_factor, 2)


def calculate_feasibility(
    transformer_kw: float,
    peak_kw: float,
    existing_chargers: int = 0,
    charger_power_kw: float = 7.2,
    safety_margin_percent: float = 20.0,
    voltage: int = 208,
    power_factor: float = 0.95,
    is_three_phase: bool = True
) -> dict:
    logger.info(
        f"Calculating feasibility: transformer={transformer_kw}kW, peak={peak_kw}kW, "
        f"chargers={existing_chargers}x{charger_power_kw}kW, voltage={voltage}V"
    )

    if voltage not in [120, 208, 240, 480, 600]:
        logger.warning(f"Non-standard voltage {voltage}V, using single-phase calculation")
        is_three_phase = False

    calc_amps = calculate_three_phase_amps if is_three_phase else calculate_single_phase_amps

    try:
        params = ElectricalParams(
            transformer_kw=transformer_kw,
            peak_kw=peak_kw,
            existing_chargers=existing_chargers,
            charger_power_kw=charger_power_kw,
            safety_margin_percent=safety_margin_percent,
            voltage=voltage
        )

        base_load_kw = peak_kw
        charger_load_kw = existing_chargers * charger_power_kw

        adjusted_base_load = apply_demand_factor(base_load_kw, params.demand_factor)
        adjusted_charger_load = apply_demand_factor(charger_load_kw, params.diversity_factor)

        existing_load_kw = adjusted_base_load + adjusted_charger_load

        usable_capacity_kw = transformer_kw * (1 - safety_margin_percent / 100)
        available_kw = usable_capacity_kw - existing_load_kw

        load_amps = calc_amps(existing_load_kw, voltage)
        available_amps = calc_amps(max(0, available_kw), voltage) if available_kw > 0 else 0

        if available_kw <= 0:
            logger.warning("No capacity available - transformer upgrade required")
            return _build_upgrade_response(
                params, existing_load_kw, load_amps, usable_capacity_kw
            )

        max_additional = floor(available_kw / charger_power_kw)

        if max_additional == 0:
            logger.info("Available capacity too small for another charger")
            return _build_partial_response(
                params, existing_load_kw, load_amps, available_kw, available_amps
            )

        proposed_load_kw = existing_load_kw + (max_additional * charger_power_kw)

        if proposed_load_kw > transformer_kw:
            max_safe = floor((usable_capacity_kw - adjusted_base_load) / charger_power_kw)
            max_safe = max(0, min(max_safe, floor((transformer_kw - adjusted_base_load) / charger_power_kw)))

            if max_safe > 0:
                logger.info(f"Limited by transformer capacity: {max_safe} chargers")
                return _build_limited_response(
                    params, existing_load_kw, load_amps, available_kw, available_amps,
                    max_safe, charger_power_kw, transformer_kw
                )
            else:
                logger.warning("Even 1 charger would exceed transformer")
                return _build_upgrade_response(
                    params, existing_load_kw, load_amps, usable_capacity_kw
                )

        final_utilization = (proposed_load_kw / transformer_kw) * 100

        logger.info(
            f"Feasibility calculated: {max_additional} chargers possible, "
            f"final utilization {final_utilization:.1f}%"
        )

        return {
            "feasible": True,
            "available_capacity_kw": round(available_kw, 2),
            "max_additional_chargers": max_additional,
            "grid_utilization_percent": round(final_utilization, 2),
            "required_upgrade": False,
            "upgrade_recommendation": None,
            "peak_load_after_addition_kw": round(proposed_load_kw, 2),
            "load_amps": load_amps,
            "available_amps": round(available_amps, 2),
            "details": {
                "base_load_kw": round(adjusted_base_load, 2),
                "charger_load_kw": round(adjusted_charger_load, 2),
                "total_existing_load_kw": round(existing_load_kw, 2),
                "power_factor": power_factor,
                "is_three_phase": is_three_phase,
                "demand_factor_applied": params.demand_factor,
                "diversity_factor_applied": params.diversity_factor
            }
        }

    except Exception as e:
        logger.error(f"Feasibility calculation error: {str(e)}")
        raise


def _build_upgrade_response(
    params: ElectricalParams,
    existing_load_kw: float,
    load_amps: float,
    usable_capacity: float
) -> dict:
    upgrade_size = ceil(existing_load_kw * 1.5 / 25) * 25
    upgrade_size = max(upgrade_size, params.transformer_kw * 1.5)

    return {
        "feasible": True,
        "available_capacity_kw": 0,
        "max_additional_chargers": 0,
        "grid_utilization_percent": round((existing_load_kw / params.transformer_kw) * 100, 2),
        "required_upgrade": True,
        "upgrade_recommendation": f"Upgrade to {int(upgrade_size)}kW transformer recommended",
        "peak_load_after_addition_kw": round(existing_load_kw, 2),
        "load_amps": load_amps,
        "available_amps": 0,
        "details": {
            "current_utilization": round((existing_load_kw / params.transformer_kw) * 100, 1),
            "headroom_kw": round(usable_capacity - existing_load_kw, 2)
        }
    }


def _build_partial_response(
    params: ElectricalParams,
    existing_load_kw: float,
    load_amps: float,
    available_kw: float,
    available_amps: float
) -> dict:
    return {
        "feasible": True,
        "available_capacity_kw": round(available_kw, 2),
        "max_additional_chargers": 0,
        "grid_utilization_percent": round((existing_load_kw / params.transformer_kw) * 100, 2),
        "required_upgrade": False,
        "upgrade_recommendation": "Available capacity insufficient for additional charger",
        "peak_load_after_addition_kw": round(existing_load_kw, 2),
        "load_amps": load_amps,
        "available_amps": round(available_amps, 2),
        "details": {
            "min_charger_power_kw": params.charger_power_kw,
            "available_headroom_kw": round(available_kw, 2)
        }
    }


def _build_limited_response(
    params: ElectricalParams,
    existing_load_kw: float,
    load_amps: float,
    available_kw: float,
    available_amps: float,
    max_safe: int,
    charger_power: float,
    transformer_kw: float
) -> dict:
    return {
        "feasible": True,
        "available_capacity_kw": round(available_kw, 2),
        "max_additional_chargers": max_safe,
        "grid_utilization_percent": round((existing_load_kw / transformer_kw) * 100, 2),
        "required_upgrade": True,
        "upgrade_recommendation": f"Add {max_safe} chargers now, then upgrade to {int(ceil((existing_load_kw + (max_safe + 1) * charger_power) * 1.25 / 25) * 25)}kW",
        "peak_load_after_addition_kw": round(existing_load_kw + (max_safe * charger_power), 2),
        "load_amps": load_amps,
        "available_amps": round(available_amps, 2),
        "details": {
            "limited_by": "transformer_capacity"
        }
    }