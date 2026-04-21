from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime
from app.models.schemas import BuildingCreate, BuildingUpdate, BuildingResponse

router = APIRouter()

buildings_db = {}
building_id_counter = 1


@router.post("/buildings", response_model=BuildingResponse, status_code=201)
def create_building(building: BuildingCreate):
    global building_id_counter
    
    now = datetime.utcnow()
    building_data = building.model_dump()
    building_data["id"] = building_id_counter
    building_data["created_at"] = now
    building_data["updated_at"] = now
    
    buildings_db[building_id_counter] = building_data
    building_id_counter += 1
    
    return building_data


@router.get("/buildings", response_model=List[BuildingResponse])
def list_buildings(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    building_type: Optional[str] = None
):
    buildings = list(buildings_db.values())
    
    if building_type:
        buildings = [b for b in buildings if b["building_type"] == building_type]
    
    return buildings[skip:skip + limit]


@router.get("/buildings/{building_id}", response_model=BuildingResponse)
def get_building(building_id: int):
    if building_id not in buildings_db:
        raise HTTPException(status_code=404, detail="Building not found")
    return buildings_db[building_id]


@router.put("/buildings/{building_id}", response_model=BuildingResponse)
def update_building(building_id: int, building: BuildingUpdate):
    if building_id not in buildings_db:
        raise HTTPException(status_code=404, detail="Building not found")
    
    existing = buildings_db[building_id]
    update_data = building.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        existing[field] = value
    
    existing["updated_at"] = datetime.utcnow()
    buildings_db[building_id] = existing
    
    return existing


@router.delete("/buildings/{building_id}", status_code=204)
def delete_building(building_id: int):
    if building_id not in buildings_db:
        raise HTTPException(status_code=404, detail="Building not found")
    
    del buildings_db[building_id]
    return None