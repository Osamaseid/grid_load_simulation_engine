# VoltStream Grid Feasibility API

A professional-grade FastAPI backend for **EV charging infrastructure feasibility analysis** - calculates transformer capacity and recommends how many chargers a building can support.

## Quick Start

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
pytest -v
```

Server runs at `http://localhost:8000`. API docs at `http://localhost:8000/docs`.

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/api/simulate` | **Run feasibility analysis** |
| GET | `/api/buildings` | List buildings |
| POST | `/api/buildings` | Create building |
| GET | `/api/buildings/{id}` | Get building |
| PUT | `/api/buildings/{id}` | Update building |
| DELETE | `/api/buildings/{id}` | Delete building |
| GET | `/api/grid/stress` | Current grid pricing |
| GET | `/api/grid/forecast` | Grid pricing forecast (1-72 hours) |

---

## `/api/simulate` - Feasibility Analysis

Calculates how many additional EV chargers can be supported.

### Request
```json
{
  "transformer_kw": 150,
  "peak_kw": 80,
  "existing_chargers": 4,
  "charger_power_kw": 19.2,
  "voltage": 480,
  "is_three_phase": true,
  "power_factor": 0.95,
  "safety_margin_percent": 20
}
```

### Response
```json
{
  "feasible": true,
  "available_capacity_kw": 42.8,
  "max_additional_chargers": 2,
  "grid_utilization_percent": 72.4,
  "required_upgrade": false,
  "peak_load_after_addition_kw": 126.8,
  "load_amps": 152.33,
  "available_amps": 51.66,
  "details": {
    "base_load_kw": 64.0,
    "charger_load_kw": 61.44,
    "is_three_phase": true
  }
}
```

---

## Building CRUD

Store building electrical profiles.

### Request (POST/PUT)
```json
{
  "name": "Downtown Plaza",
  "address": "123 Main St",
  "building_type": "commercial",
  "transformer_kw": 150,
  "peak_kw": 80,
  "existing_chargers": 4,
  "voltage": 208,
  "power_factor": 0.95
}
```

Building types: `commercial`, `residential`, `industrial`, `mixed_use`

---

## Grid Stress API

Real-time and forecast grid pricing for demand response decisions.

- `GET /api/grid/stress?building_demand_kw=50` - Current pricing
- `GET /api/grid/forecast?hours=24` - 24-hour forecast

Returns: `price_per_kwh`, `grid_load_percent`, `demand_kw`, `status`, `recommendation`

---

## Project Structure

```
voltstream_api/
├── app/
│   ├── main.py              # FastAPI app entry point
│   ├── config.py            # Settings (pydantic-settings)
│   ├── api/
│   │   ├── routes_simulation.py  # /simulate endpoint
│   │   ├── routes_buildings.py   # Building CRUD
│   │   └── routes_grid.py        # Grid stress API
│   ├── models/
│   │   └── schemas.py       # Pydantic request/response models
│   ├── services/
│   │   ├── simulation.py    # Core feasibility calculation
│   │   └── grid_stress.py   # Grid pricing logic
│   └── utils/
│       └── validators.py   # Input validation
├── tests/                  # 90+ test cases
├── requirements.txt
└── pytest.ini
```

---

## Configuration

Settings in `.env` or `app/config.py`:

| Setting | Default | Description |
|---------|---------|-------------|
| `app_port` | 8000 | Server port |
| `app_host` | 0.0.0.0 | Server host |
| `default_voltage` | 208 | System voltage (V) |
| `default_power_factor` | 0.95 | Power factor |
| `default_safety_margin_percent` | 20 | Safety buffer (%) |
| `max_transformer_kw` | 5000 | Max transformer size |

Valid voltages: 120, 208, 240, 480, 600

---

## Core Calculation Logic

1. **Transformer Capacity** = `transformer_kw × (1 - safety_margin%)`
2. **Existing Load** = `(peak_kw × demand_factor) + (chargers × power × diversity_factor)`
   - demand_factor = 0.8
   - diversity_factor = 1.25
3. **Available Capacity** = `transformer_capacity - existing_load`
4. **Max Additional Chargers** = `floor(available_capacity / charger_power_kw)`
5. **Amps (3-phase)** = `(kW × 1000) / (V × 1.732)`

---

## Features

- **Transformer Capacity Analysis**: Calculate how many Level 2/DC fast chargers a building electrical service can support
- **Upgrade Recommendations**: Smart recommendations for utility-side transformer upgrades
- **Engineering Unit Validation**: Strict validation for kW, Amps, Volts, and power factor
- **Grid Stress Simulation**: Real-time utility pricing and demand forecasting
- **Building Management**: Full CRUD for building electrical profiles
