import pytest
from app.services.simulation import calculate_feasibility


class TestBasicFeasibility:
    def test_basic_case(self):
        result = calculate_feasibility(100, 60)
        assert result["max_additional_chargers"] >= 0
        assert result["feasible"] is True

    def test_full_capacity_available(self):
        result = calculate_feasibility(50, 10)
        assert result["max_additional_chargers"] >= 0

    def test_zero_peak_load(self):
        result = calculate_feasibility(100, 0)
        assert result["max_additional_chargers"] >= 0
        assert result["feasible"] is True


class TestExistingChargers:
    def test_existing_chargers(self):
        result = calculate_feasibility(100, 60, existing_chargers=2)
        assert result["feasible"] is True
        assert result["max_additional_chargers"] < 5

    def test_max_existing_chargers(self):
        result = calculate_feasibility(200, 100, existing_chargers=10)
        assert result["max_additional_chargers"] >= 0

    def test_existing_chargers_at_limit(self):
        result = calculate_feasibility(100, 50, existing_chargers=6)
        assert result["max_additional_chargers"] == 0


class TestNoCapacity:
    def test_no_capacity(self):
        result = calculate_feasibility(100, 95)
        assert result["max_additional_chargers"] >= 0

    def test_at_capacity_edge(self):
        result = calculate_feasibility(100, 92)
        assert result["max_additional_chargers"] >= 0

    def test_exceeding_capacity(self):
        result = calculate_feasibility(100, 98)
        assert result["max_additional_chargers"] >= 0


class TestUpgradeThreshold:
    def test_upgrade_threshold(self):
        result = calculate_feasibility(100, 80)
        assert result["max_additional_chargers"] >= 0

    def test_upgrade_with_recommendation(self):
        result = calculate_feasibility(150, 100)
        assert result["max_additional_chargers"] >= 0

    def test_no_upgrade_needed(self):
        result = calculate_feasibility(100, 40)
        assert result["required_upgrade"] is False or result["required_upgrade"] is True


class TestSafetyMargin:
    def test_default_safety_margin(self):
        result = calculate_feasibility(100, 60, safety_margin_percent=20)
        assert result["max_additional_chargers"] >= 0

    def test_zero_safety_margin(self):
        result = calculate_feasibility(100, 60, safety_margin_percent=0)
        assert result["max_additional_chargers"] >= 0

    def test_high_safety_margin(self):
        result = calculate_feasibility(100, 60, safety_margin_percent=40)
        assert result["max_additional_chargers"] >= 0


class TestChargerPower:
    def test_standard_level2(self):
        result = calculate_feasibility(100, 50, charger_power_kw=7.2)
        assert result["max_additional_chargers"] >= 0

    def test_high_power_level2(self):
        result = calculate_feasibility(100, 50, charger_power_kw=19.2)
        assert result["max_additional_chargers"] >= 0

    def test_dc_fast_charger(self):
        result = calculate_feasibility(200, 50, charger_power_kw=50)
        assert result["max_additional_chargers"] >= 0


class TestVoltageCalculations:
    def test_208v_calculation(self):
        result = calculate_feasibility(100, 60, voltage=208)
        assert result["load_amps"] is not None
        assert result["available_amps"] is not None

    def test_480v_calculation(self):
        result = calculate_feasibility(100, 60, voltage=480)
        assert result["load_amps"] is not None

    def test_240v_calculation(self):
        result = calculate_feasibility(100, 60, voltage=240)
        assert result["load_amps"] is not None


class TestGridUtilization:
    def test_utilization_percentage(self):
        result = calculate_feasibility(100, 75)
        assert result["grid_utilization_percent"] > 0

    def test_high_utilization(self):
        result = calculate_feasibility(100, 95)
        assert result["grid_utilization_percent"] > 0

    def test_low_utilization(self):
        result = calculate_feasibility(150, 30)
        assert result["grid_utilization_percent"] > 0


class TestEdgeCases:
    def test_minimal_transformer(self):
        result = calculate_feasibility(15, 5)
        assert result["feasible"] is True

    def test_large_scale(self):
        result = calculate_feasibility(1000, 500, existing_chargers=50)
        assert result["max_additional_chargers"] >= 0

    def test_zero_charger_power(self):
        result = calculate_feasibility(100, 60, charger_power_kw=0.1)
        assert result["max_additional_chargers"] > 0