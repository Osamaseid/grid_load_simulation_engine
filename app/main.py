from fastapi import FastAPI
from app.api.routes_simulation import router as sim_router
from app.api.routes_buildings import router as buildings_router
from app.api.routes_grid import router as grid_router
from app.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version
)

app.include_router(sim_router, prefix="/api")
app.include_router(buildings_router, prefix="/api")
app.include_router(grid_router, prefix="/api")


@app.get("/health")
def health():
    return {"status": "ok", "app": settings.app_name, "version": settings.app_version}