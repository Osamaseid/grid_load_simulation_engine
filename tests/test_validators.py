import pytest
from app.utils.validators import (
    calculate_amps_from_kw,
    calculate_kw_from_amps,
    validate_power_factor,
    validate_transformer_capacity,
    validate_charger_power,
    validate_load_calculation
)


class TestUnitConversions:
    def test_calculate_amps_from_kw_208v(self):
        assert calculate_amps_from_kw(7.2, 208) == 34.62
        assert calculate_amps_from_kw(100, 208) == 480.77

    def test_calculate_amps_from_kw_480v(self):
        assert calculate_amps_from_kw(100, 480) == 208.33

    def test_calculate_amps_from_kw_240v(self):
        assert calculate_amps_from_kw(7.2, 240) == 30.0

    def test_calculate_amps_from_kw_zero_voltage_raises(self):
        with pytest.raises(ValueError, match="Voltage cannot be zero"):
            calculate_amps_from_kw(100, 0)

    def test_calculate_kw_from_amps_208v(self):
        assert calculate_kw_from_amps(32, 208) == 6.66

    def test_calculate_kw_from_amps_480v(self):
        assert calculate_kw_from_amps(200, 480) == 96.0

    def test_calculate_kw_from_amps_zero_voltage_raises(self):
        with pytest.raises(ValueError, match="Voltage cannot be zero"):
            calculate_kw_from_amps(100, 0)


class TestPowerFactorValidation:
    def test_valid_power_factor(self):
        assert validate_power_factor(0.95) == 0.95
        assert validate_power_factor(1.0) == 1.0
        assert validate_power_factor(0.5) == 0.5

    def test_power_factor_below_minimum(self):
        with pytest.raises(ValueError, match="Power factor must be between"):
            validate_power_factor(0.4)

    def test_power_factor_above_maximum(self):
        with pytest.raises(ValueError, match="Power factor must be between"):
            validate_power_factor(1.1)


class TestTransformerCapacity:
    def test_valid_transformer_kw(self):
        assert validate_transformer_capacity(100) == 100.0
        assert validate_transformer_capacity(1500) == 1500.0
        assert validate_transformer_capacity(50) == 50.0

    def test_transformer_below_minimum(self):
        with pytest.raises(ValueError, match="Transformer capacity too small"):
            validate_transformer_capacity(10)

    def test_transformer_above_maximum(self):
        with pytest.raises(ValueError, match="Transformer capacity exceeds practical limit"):
            validate_transformer_capacity(6000)


class TestChargerPower:
    def test_valid_charger_power(self):
        assert validate_charger_power(7.2) == 7.2
        assert validate_charger_power(19.2) == 19.2
        assert validate_charger_power(350) == 350.0

    def test_charger_power_exceeds_max(self):
        with pytest.raises(ValueError, match="Charger power exceeds DC fast charging max"):
            validate_charger_power(400)


class TestLoadCalculation:
    def test_valid_load_calculation(self):
        result = validate_load_calculation(
            transformer_kw=100,
            peak_kw=60,
            charger_kw=7.2,
            num_chargers=4
        )
        assert result["valid"] is True
        assert result["proposed_load_kw"] == 88.8
        assert result["headroom_kw"] == 11.2

    def test_load_exceeds_transformer_125_percent(self):
        result = validate_load_calculation(
            transformer_kw=100,
            peak_kw=80,
            charger_kw=7.2,
            num_chargers=10
        )
        assert result["valid"] is False
        assert "Overload" in result["error"]

    def test_load_at_threshold(self):
        result = validate_load_calculation(
            transformer_kw=100,
            peak_kw=50,
            charger_kw=7.2,
            num_chargers=7
        )
        assert "valid" in result

    def test_load_within_capacity(self):
        result = validate_load_calculation(
            transformer_kw=150,
            peak_kw=80,
            charger_kw=19.2,
            num_chargers=2
        )
        assert result["valid"] is True
        assert result["utilization_percent"] > 0
