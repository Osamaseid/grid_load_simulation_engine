from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "VoltStream Grid Feasibility API"
    app_version: str = "1.0.0"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    debug: bool = False

    grid_stress_min_price: float = 0.08
    grid_stress_max_price: float = 0.45
    grid_stress_critical_threshold: int = 90

    default_safety_margin_percent: float = 20.0
    default_charger_power_kw: float = 7.2
    default_voltage: int = 208
    default_power_factor: float = 0.95

    min_transformer_kw: float = 15
    max_transformer_kw: float = 5000
    max_existing_chargers: int = 1000
    max_charger_power_kw: float = 350

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()
