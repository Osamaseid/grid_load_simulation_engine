import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestHealthEndpoint:
    def test_health_check(self):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data


class TestSimulationEndpoint:
    def test_simulation_endpoint(self):
        response = client.post("/api/simulate", json={
            "transformer_kw": 100,
            "peak_kw": 60
        })
        assert response.status_code == 200
        assert "max_additional_chargers" in response.json()

    def test_simulation_with_existing_chargers(self):
        response = client.post("/api/simulate", json={
            "transformer_kw": 100,
            "peak_kw": 60,
            "existing_chargers": 2,
            "charger_power_kw": 7.2
        })
        assert response.status_code == 200
        data = response.json()
        assert data["max_additional_chargers"] < 5

    def test_simulation_invalid_voltage(self):
        response = client.post("/api/simulate", json={
            "transformer_kw": 100,
            "peak_kw": 60,
            "voltage": 220
        })
        assert response.status_code == 422

    def test_simulation_transformer_exceeds_max(self):
        response = client.post("/api/simulate", json={
            "transformer_kw": 6000,
            "peak_kw": 100
        })
        assert response.status_code == 422

    def test_simulation_negative_peak_load(self):
        response = client.post("/api/simulate", json={
            "transformer_kw": 100,
            "peak_kw": -10
        })
        assert response.status_code == 422

    def test_simulation_overload_validation(self):
        response = client.post("/api/simulate", json={
            "transformer_kw": 100,
            "peak_kw": 90,
            "existing_chargers": 10
        })
        assert response.status_code == 422

    def test_simulation_response_fields(self):
        response = client.post("/api/simulate", json={
            "transformer_kw": 100,
            "peak_kw": 60,
            "voltage": 480
        })
        assert response.status_code == 200
        data = response.json()
        required_fields = [
            "feasible",
            "available_capacity_kw",
            "max_additional_chargers",
            "grid_utilization_percent",
            "required_upgrade",
            "peak_load_after_addition_kw",
            "load_amps",
            "available_amps"
        ]
        for field in required_fields:
            assert field in data

    def test_simulation_high_voltage(self):
        response = client.post("/api/simulate", json={
            "transformer_kw": 100,
            "peak_kw": 60,
            "voltage": 480
        })
        assert response.status_code == 200
        data = response.json()
        assert data["load_amps"] is not None


class TestBuildingEndpoints:
    def test_create_building(self):
        response = client.post("/api/buildings", json={
            "name": "Test Building",
            "address": "123 Test St",
            "building_type": "commercial",
            "transformer_kw": 100,
            "peak_kw": 60
        })
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Building"
        assert "id" in data

    def test_create_building_invalid_type(self):
        response = client.post("/api/buildings", json={
            "name": "Test",
            "address": "123 Test St",
            "building_type": "invalid",
            "transformer_kw": 100,
            "peak_kw": 60
        })
        assert response.status_code == 422

    def test_create_building_overload(self):
        response = client.post("/api/buildings", json={
            "name": "Test",
            "address": "123 Test St",
            "building_type": "commercial",
            "transformer_kw": 100,
            "peak_kw": 150
        })
        assert response.status_code == 422

    def test_list_buildings(self):
        response = client.get("/api/buildings")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_list_buildings_with_pagination(self):
        response = client.get("/api/buildings?skip=0&limit=10")
        assert response.status_code == 200

    def test_get_building_by_id(self):
        create_response = client.post("/api/buildings", json={
            "name": "Get Test",
            "address": "456 Test Ave",
            "building_type": "residential",
            "transformer_kw": 75,
            "peak_kw": 40
        })
        building_id = create_response.json()["id"]

        response = client.get(f"/api/buildings/{building_id}")
        assert response.status_code == 200
        assert response.json()["name"] == "Get Test"

    def test_get_building_not_found(self):
        response = client.get("/api/buildings/99999")
        assert response.status_code == 404

    def test_update_building(self):
        create_response = client.post("/api/buildings", json={
            "name": "Update Test",
            "address": "789 Test Blvd",
            "building_type": "commercial",
            "transformer_kw": 150,
            "peak_kw": 80
        })
        building_id = create_response.json()["id"]

        response = client.put(f"/api/buildings/{building_id}", json={
            "existing_chargers": 5
        })
        assert response.status_code == 200
        assert response.json()["existing_chargers"] == 5

    def test_update_building_not_found(self):
        response = client.put("/api/buildings/99999", json={
            "existing_chargers": 5
        })
        assert response.status_code == 404

    def test_delete_building(self):
        create_response = client.post("/api/buildings", json={
            "name": "Delete Test",
            "address": "Delete St",
            "building_type": "industrial",
            "transformer_kw": 200,
            "peak_kw": 100
        })
        building_id = create_response.json()["id"]

        response = client.delete(f"/api/buildings/{building_id}")
        assert response.status_code == 204

        get_response = client.get(f"/api/buildings/{building_id}")
        assert get_response.status_code == 404

    def test_delete_building_not_found(self):
        response = client.delete("/api/buildings/99999")
        assert response.status_code == 404


class TestGridStressEndpoints:
    def test_grid_stress_basic(self):
        response = client.get("/api/grid/stress")
        assert response.status_code == 200
        data = response.json()
        assert "price_per_kwh" in data
        assert "grid_load_percent" in data
        assert "status" in data

    def test_grid_stress_with_building_demand(self):
        response = client.get("/api/grid/stress?building_demand_kw=150")
        assert response.status_code == 200
        data = response.json()
        assert "demand_kw" in data
        assert data["demand_kw"] > 150

    def test_grid_stress_forecast(self):
        response = client.get("/api/grid/forecast?hours=24")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 24

    def test_grid_stress_forecast_default(self):
        response = client.get("/api/grid/forecast")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 24

    def test_grid_stress_forecast_max_hours(self):
        response = client.get("/api/grid/forecast?hours=72")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 72

    def test_grid_stress_forecast_invalid_hours(self):
        response = client.get("/api/grid/forecast?hours=100")
        assert response.status_code == 422

    def test_grid_stress_recommendations(self):
        response = client.get("/api/grid/stress")
        assert response.status_code == 200
        data = response.json()
        if data["status"] in ["high", "critical"]:
            assert data["recommendation"] is not None


class TestValidationErrors:
    def test_missing_required_fields(self):
        response = client.post("/api/simulate", json={})
        assert response.status_code == 422

    def test_invalid_building_type(self):
        response = client.post("/api/buildings", json={
            "name": "Test",
            "address": "Test",
            "building_type": "unknown",
            "transformer_kw": 100,
            "peak_kw": 50
        })
        assert response.status_code == 422

    def test_transformer_too_small(self):
        response = client.post("/api/simulate", json={
            "transformer_kw": 10,
            "peak_kw": 5
        })
        assert response.status_code in [200, 422]
