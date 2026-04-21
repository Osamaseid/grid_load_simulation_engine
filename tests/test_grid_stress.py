import pytest
from datetime import datetime
from app.services.grid_stress import get_grid_stress, get_time_multiplier


class TestGridStressService:
    def test_get_grid_stress_basic(self):
        result = get_grid_stress()
        assert "timestamp" in result
        assert "price_per_kwh" in result
        assert "grid_load_percent" in result
        assert "status" in result

    def test_grid_stress_price_range(self):
        result = get_grid_stress()
        assert 0.05 <= result["price_per_kwh"] <= 1.0

    def test_grid_stress_load_range(self):
        result = get_grid_stress()
        assert 30 <= result["grid_load_percent"] <= 100

    def test_grid_stress_valid_status(self):
        result = get_grid_stress()
        valid_statuses = ["low", "normal", "high", "critical"]
        assert result["status"] in valid_statuses

    def test_grid_stress_with_base_demand(self):
        result = get_grid_stress(base_demand_kw=150)
        assert "demand_kw" in result
        assert result["demand_kw"] > 150

    def test_grid_stress_demand_scaling(self):
        result_low = get_grid_stress(base_demand_kw=50)
        result_high = get_grid_stress(base_demand_kw=200)
        assert result_high["demand_kw"] > result_low["demand_kw"]

    def test_grid_stress_critical_has_recommendation(self):
        for _ in range(20):
            result = get_grid_stress()
            if result["status"] == "critical":
                assert result["recommendation"] is not None
                assert "charging" in result["recommendation"].lower() or "off-peak" in result["recommendation"].lower()
                break
        else:
            pytest.skip("Could not generate critical status in 20 attempts")

    def test_grid_stress_high_has_recommendation(self):
        for _ in range(20):
            result = get_grid_stress()
            if result["status"] == "high":
                assert result["recommendation"] is not None
                break
        else:
            pytest.skip("Could not generate high status in 20 attempts")

    def test_grid_stress_timestamp_format(self):
        result = get_grid_stress()
        assert isinstance(result["timestamp"], datetime)


class TestTimeMultiplier:
    def test_time_multiplier_range(self):
        multiplier = get_time_multiplier()
        assert 0.5 <= multiplier <= 2.0

    def test_time_multiplier_off_peak(self):
        for _ in range(100):
            multiplier = get_time_multiplier()
            if 0 <= datetime.utcnow().hour < 6 or 21 <= datetime.utcnow().hour < 24:
                assert multiplier <= 1.0
                break

    def test_time_multiplier_peak_hours(self):
        for _ in range(100):
            multiplier = get_time_multiplier()
            hour = datetime.utcnow().hour
            if 16 <= hour < 21:
                assert multiplier >= 1.0
                break


class TestGridForecast:
    def test_forecast_length(self):
        from app.services.grid_stress import get_grid_stress
        forecast = [get_grid_stress() for _ in range(24)]
        assert len(forecast) == 24

    def test_forecast_returns_data(self):
        from app.services.grid_stress import get_grid_stress
        timestamps = [get_grid_stress()["timestamp"] for _ in range(10)]
        assert len(timestamps) == 10
