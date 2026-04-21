import random
from datetime import datetime
from typing import Optional


def get_grid_stress(base_demand_kw: Optional[float] = None) -> dict:
    grid_load = random.randint(30, 100)
    
    if grid_load < 50:
        status = "low"
        base_price = 0.08
    elif grid_load < 75:
        status = "normal"
        base_price = 0.12
    elif grid_load < 90:
        status = "high"
        base_price = 0.25
    else:
        status = "critical"
        base_price = 0.45
    
    time_multiplier = get_time_multiplier()
    price_per_kwh = round(base_price * time_multiplier, 3)
    
    if base_demand_kw:
        demand_kw = base_demand_kw * (1 + grid_load / 100)
    else:
        demand_kw = round(grid_load * random.uniform(8, 12), 2)
    
    recommendation = None
    if status == "critical":
        recommendation = "Avoid peak charging. Consider scheduling EV charging during off-peak hours (10pm-6am)."
    elif status == "high":
        recommendation = "Consider delaying non-essential charging to off-peak hours."
    
    return {
        "timestamp": datetime.utcnow(),
        "price_per_kwh": price_per_kwh,
        "grid_load_percent": grid_load,
        "demand_kw": round(demand_kw, 2),
        "status": status,
        "recommendation": recommendation
    }


def get_time_multiplier() -> float:
    hour = datetime.utcnow().hour
    
    if 6 <= hour < 10:
        return 1.5
    elif 10 <= hour < 16:
        return 1.1
    elif 16 <= hour < 21:
        return 1.8
    elif 21 <= hour < 24:
        return 1.3
    else:
        return 0.7