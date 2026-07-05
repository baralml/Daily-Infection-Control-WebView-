import uuid
from typing import List, Optional, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Response
from app.services.reporting import generate_daily_rounds_excel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, PermissionChecker
from app.models.auth import User
from app.models.capa import Capa, CapaStatusEnum
from app.schemas.daily_round import (
    DailyRoundCreate, DailyRoundResponse, DailyRoundDetailResponse,
    DailyRoundObservationCreate, DailyRoundObservationResponse, MasterObservationResponse,
    DailyRoundObservationMediaResponse, DailyRoundObservationMediaBase,
    BuildingCreate, BuildingResponse, BuildingLayoutResponse, BuildingFloorCreate
)
from app.crud.crud_daily_round import (
    create_daily_round, get_daily_round_details, get_daily_rounds,
    add_observation_to_round, finish_daily_round, search_master_observations,
    add_observation_media, create_building, get_buildings, get_building_layout,
    save_building_layout, update_floor_state
)
from app.services.storage import process_and_store_media

router = APIRouter()

@router.get("/layouts", response_model=List[BuildingResponse])
def list_buildings(
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user)
) -> Any:
    """Lists all active building layout configuration nodes."""
    return get_buildings(db)

@router.post("/layouts", response_model=BuildingResponse, status_code=status.HTTP_201_CREATED)
def add_building(
    obj_in: BuildingCreate,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user)
) -> Any:
    """Creates a new building node."""
    return create_building(db, obj_in.name)

@router.get("/layouts/{building_id}", response_model=BuildingLayoutResponse)
def fetch_building_layout(
    building_id: uuid.UUID,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user)
) -> Any:
    """Retrieves full nested floor, department, and room mapping for a building."""
    layout = get_building_layout(db, building_id)
    if not layout:
        raise HTTPException(status_code=404, detail="Building layout not found")
    return layout

@router.post("/layouts/{building_id}", response_model=BuildingLayoutResponse)
def save_layout(
    building_id: uuid.UUID,
    floors_in: List[BuildingFloorCreate],
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user)
) -> Any:
    """Saves/replaces full layout schema floors, departments, and rooms mapping for a building."""
    try:
        return save_building_layout(db, building_id, floors_in)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.patch("/{round_id}/floors/{floor_id}/status", response_model=DailyRoundDetailResponse)
def patch_floor_status(
    round_id: uuid.UUID,
    floor_id: uuid.UUID,
    status_update: dict,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user)
) -> Any:
    """Updates the state status of a floor walk session log."""
    new_status = status_update.get("status")
    if not new_status or new_status not in ["BLUE", "ORANGE", "GREEN", "RED"]:
        raise HTTPException(status_code=400, detail="Invalid status color. Use BLUE, ORANGE, GREEN, or RED")
    
    updated_state = update_floor_state(db, round_id, floor_id, new_status)
    if not updated_state:
        raise HTTPException(status_code=404, detail="Floor state not found for this round")
        
    return get_daily_round_details(db, round_id)

@router.post("", response_model=DailyRoundResponse, status_code=status.HTTP_201_CREATED)
def start_round(
    obj_in: DailyRoundCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Starts a new Daily Round walk tracking session."""
    return create_daily_round(db, obj_in, current_user.id)

@router.get("", response_model=List[DailyRoundResponse])
def list_rounds(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user)
) -> Any:
    """Retrieve list of historical and active daily rounds."""
    return get_daily_rounds(db, skip=skip, limit=limit)

@router.get("/observations/search", response_model=List[MasterObservationResponse])
def search_observations(
    query: str = Query("", description="Query text to filter master observations"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user)
) -> Any:
    """Fuzzy/substring search of observations from the pre-defined master library."""
    return search_master_observations(db, query=query, limit=limit)

@router.get("/export/excel")
def export_daily_rounds_excel(
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user)
):
    """Compiles daily rounds summaries into a structured Excel download."""
    rounds = get_daily_rounds(db, skip=0, limit=1000)
    excel_bytes = generate_daily_rounds_excel(rounds)
    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=Daily_Rounds_Report.xlsx"}
    )

@router.get("/{round_id}", response_model=DailyRoundDetailResponse)
def get_round_details(
    round_id: uuid.UUID,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user)
) -> Any:
    """Retrieves full details of a specific round including all its observations."""
    round_obj = get_daily_round_details(db, round_id)
    if not round_obj:
        raise HTTPException(status_code=404, detail="Daily round not found")
    return round_obj

@router.post("/{round_id}/observations", response_model=DailyRoundObservationResponse, status_code=status.HTTP_201_CREATED)
def add_observation(
    round_id: uuid.UUID,
    obj_in: DailyRoundObservationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Appends an observation to an active round, with optional CAPA generation."""
    # Verify round exists
    round_obj = get_daily_round_details(db, round_id)
    if not round_obj:
        raise HTTPException(status_code=404, detail="Daily round not found")
        
    if round_obj.status == "COMPLETED":
        raise HTTPException(status_code=400, detail="Cannot add observations to a completed round")

    # If CAPA details are included, mark has_capa as True initially
    if obj_in.capa_details:
        obj_in.has_capa = True

    # 1. Create observation
    db_obs = add_observation_to_round(db, round_id, obj_in)

    # 2. Handle integrated CAPA generation
    if obj_in.capa_details:
        try:
            deadline_date = datetime.strptime(obj_in.capa_details.deadline, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid deadline date format. Use YYYY-MM-DD")
            
        db_capa = Capa(
            id=uuid.uuid4(),
            daily_round_observation_id=db_obs.id,
            department_id=db_obs.department_id,
            assigned_to=obj_in.capa_details.assigned_to,
            created_by=current_user.id,
            title=f"CAPA: {obj_in.observation_text}",
            description=f"Auto-generated CAPA from Daily Rounds. Observation: {obj_in.observation_text}. Remarks: {obj_in.remarks or 'None'}",
            deadline=deadline_date,
            priority=obj_in.capa_details.priority,
            status=CapaStatusEnum.PENDING
        )
        db.add(db_capa)
        db.commit()
        db.refresh(db_obs)

    return db_obs

@router.post("/{round_id}/finish", response_model=DailyRoundResponse)
def finish_round(
    round_id: uuid.UUID,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user)
) -> Any:
    """Finalizes an active walk session and seals its observations."""
    round_obj = get_daily_round_details(db, round_id)
    if not round_obj:
        raise HTTPException(status_code=404, detail="Daily round not found")
        
    if round_obj.status == "COMPLETED":
        raise HTTPException(status_code=400, detail="Round is already completed")
        
    updated = finish_daily_round(db, round_id)
    return updated

@router.post("/{round_id}/observations/{observation_id}/media", response_model=DailyRoundObservationMediaResponse)
def upload_observation_photo(
    round_id: uuid.UUID,
    observation_id: uuid.UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user)
) -> Any:
    """Uploads and associates a photo/media attachment to a daily round observation."""
    round_obj = get_daily_round_details(db, round_id)
    if not round_obj:
        raise HTTPException(status_code=404, detail="Daily round not found")

    file_bytes = file.file.read()
    original_url, compressed_url, thumbnail_url = process_and_store_media(
        file_bytes, file.filename, file.content_type
    )

    media_in = DailyRoundObservationMediaBase(
        media_type="IMAGE" if file.content_type.startswith("image/") else "VIDEO",
        original_url=original_url,
        thumbnail_url=thumbnail_url,
        compressed_url=compressed_url,
        file_size=len(file_bytes),
        mime_type=file.content_type
    )

    return add_observation_media(db, observation_id, media_in)
