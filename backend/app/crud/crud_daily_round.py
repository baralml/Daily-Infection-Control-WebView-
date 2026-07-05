import uuid
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, desc

from app.models.daily_round import (
    DailyRound, DailyRoundObservation, DailyRoundObservationMedia, MasterObservation, 
    RoundStatusEnum, Building, BuildingFloor, BuildingDepartment, BuildingRoom, DailyRoundFloorState
)
from app.schemas.daily_round import DailyRoundCreate, DailyRoundObservationCreate, DailyRoundObservationMediaBase
from app.models.audit import RiskLevelEnum

def create_daily_round(db: Session, obj_in: DailyRoundCreate, auditor_id: uuid.UUID) -> DailyRound:
    """Initializes a new daily round walking session in Draft mode."""
    db_round = DailyRound(
        id=uuid.uuid4(),
        hospital=obj_in.hospital,
        building=obj_in.building,
        building_id=obj_in.building_id,
        floor=obj_in.floor,
        department_id=obj_in.department_id,
        round_type=obj_in.round_type,
        auditor_id=auditor_id,
        status=RoundStatusEnum.DRAFT,
        started_at=datetime.now(timezone.utc)
    )
    db.add(db_round)
    db.commit()
    db.refresh(db_round)

    # Seed initial floor states as 'BLUE' (Not Visited) if building layout is selected
    if obj_in.building_id:
        floors = db.query(BuildingFloor).filter(BuildingFloor.building_id == obj_in.building_id).all()
        for fl in floors:
            state = DailyRoundFloorState(
                id=uuid.uuid4(),
                round_id=db_round.id,
                floor_id=fl.id,
                status="BLUE"
            )
            db.add(state)
        db.commit()
        db.refresh(db_round)

    return db_round

def get_daily_round_details(db: Session, round_id: uuid.UUID) -> Optional[DailyRound]:
    """Retrieves full nested daily round details, observations, and floor states logs."""
    return db.query(DailyRound).options(
        joinedload(DailyRound.department),
        joinedload(DailyRound.auditor),
        joinedload(DailyRound.building_obj),
        joinedload(DailyRound.floor_states).joinedload(DailyRoundFloorState.floor),
        joinedload(DailyRound.observations).joinedload(DailyRoundObservation.media),
        joinedload(DailyRound.observations).joinedload(DailyRoundObservation.capas),
        joinedload(DailyRound.observations).joinedload(DailyRoundObservation.department)
    ).filter(DailyRound.id == round_id).first()

def get_daily_rounds(db: Session, skip: int = 0, limit: int = 100) -> List[DailyRound]:
    """Retrieve list of historical and active daily rounds."""
    return db.query(DailyRound).options(
        joinedload(DailyRound.department),
        joinedload(DailyRound.auditor),
        joinedload(DailyRound.building_obj)
    ).order_by(desc(DailyRound.started_at)).offset(skip).limit(limit).all()

def add_observation_to_round(db: Session, round_id: uuid.UUID, obj_in: DailyRoundObservationCreate) -> DailyRoundObservation:
    """Adds a recorded clinical observation during a walking round."""
    # Find matching layout nodes if building layout exists
    floor_id = None
    building_dept_id = None
    
    round_obj = db.query(DailyRound).filter(DailyRound.id == round_id).first()
    if round_obj and round_obj.building_id:
        fl_node = db.query(BuildingFloor).filter(
            BuildingFloor.building_id == round_obj.building_id,
            BuildingFloor.floor_name == obj_in.floor_name
        ).first()
        if fl_node:
            floor_id = fl_node.id
            dept_node = db.query(BuildingDepartment).filter(
                BuildingDepartment.floor_id == fl_node.id,
                BuildingDepartment.department_id == obj_in.department_id
            ).first()
            if dept_node:
                building_dept_id = dept_node.id

    db_obs = DailyRoundObservation(
        id=uuid.uuid4(),
        round_id=round_id,
        floor_name=obj_in.floor_name,
        department_id=obj_in.department_id,
        floor_id=floor_id,
        building_department_id=building_dept_id,
        observation_text=obj_in.observation_text,
        category=obj_in.category,
        room_number=obj_in.room_number,
        severity=obj_in.severity,
        remarks=obj_in.remarks,
        voice_note_url=obj_in.voice_note_url,
        voice_text_transcript=obj_in.voice_text_transcript,
        has_capa=obj_in.has_capa
    )
    db.add(db_obs)
    db.commit()
    db.refresh(db_obs)

    # Automatically set floor status to 'RED' if severity is HIGH or CRITICAL, otherwise 'ORANGE'
    if round_obj and floor_id:
        f_state = db.query(DailyRoundFloorState).filter(
            DailyRoundFloorState.round_id == round_id,
            DailyRoundFloorState.floor_id == floor_id
        ).first()
        if f_state:
            if obj_in.severity in [RiskLevelEnum.HIGH, RiskLevelEnum.CRITICAL]:
                f_state.status = "RED"
            elif f_state.status == "BLUE":
                f_state.status = "ORANGE"
            db.commit()

    return db_obs

def add_observation_media(db: Session, observation_id: uuid.UUID, media_in: DailyRoundObservationMediaBase) -> DailyRoundObservationMedia:
    """Links an uploaded photo or attachment to an observation."""
    db_media = DailyRoundObservationMedia(
        id=uuid.uuid4(),
        observation_id=observation_id,
        media_type=media_in.media_type,
        original_url=media_in.original_url,
        thumbnail_url=media_in.thumbnail_url,
        compressed_url=media_in.compressed_url,
        file_size=media_in.file_size,
        mime_type=media_in.mime_type
    )
    db.add(db_media)
    db.commit()
    db.refresh(db_media)
    return db_media

def finish_daily_round(db: Session, round_id: uuid.UUID) -> Optional[DailyRound]:
    """Completes an active daily round, setting ended_at timestamp."""
    db_round = db.query(DailyRound).filter(DailyRound.id == round_id).first()
    if db_round:
        db_round.status = RoundStatusEnum.COMPLETED
        db_round.ended_at = datetime.now(timezone.utc)
        db_round.updated_at = datetime.now(timezone.utc)
        
        # Any remaining ORANGE or BLUE floors turn to GREEN
        floor_states = db.query(DailyRoundFloorState).filter(DailyRoundFloorState.round_id == round_id).all()
        for fs in floor_states:
            if fs.status in ["BLUE", "ORANGE"]:
                fs.status = "GREEN"
                
        db.commit()
        db.refresh(db_round)
    return db_round

def search_master_observations(db: Session, query: str, limit: int = 20) -> List[MasterObservation]:
    """Perform fuzzy search on predefined clinical observations library using SQL contains."""
    if not query:
        return db.query(MasterObservation).filter(MasterObservation.is_active == True).limit(limit).all()
        
    pattern = f"%{query}%"
    return db.query(MasterObservation).filter(
        MasterObservation.is_active == True,
        or_(
            MasterObservation.text.ilike(pattern),
            MasterObservation.category.ilike(pattern)
        )
    ).limit(limit).all()

# ---------------- Layout Operations ----------------
def create_building(db: Session, name: str) -> Building:
    """Creates a new building node."""
    db_b = Building(id=uuid.uuid4(), name=name, is_active=True)
    db.add(db_b)
    db.commit()
    db.refresh(db_b)
    return db_b

def get_buildings(db: Session) -> List[Building]:
    """Lists all configured buildings."""
    return db.query(Building).filter(Building.is_active == True).order_by(Building.name).all()

def get_building_layout(db: Session, building_id: uuid.UUID) -> Optional[Building]:
    """Retrieves full nested building floor, department, and room hierarchy layout."""
    return db.query(Building).options(
        joinedload(Building.floors)
        .joinedload(BuildingFloor.departments)
        .joinedload(BuildingDepartment.department),
        joinedload(Building.floors)
        .joinedload(BuildingFloor.departments)
        .joinedload(BuildingDepartment.rooms)
    ).filter(Building.id == building_id).first()

def update_floor_state(db: Session, round_id: uuid.UUID, floor_id: uuid.UUID, status: str) -> Optional[DailyRoundFloorState]:
    """Updates status color of a floor walk progress state."""
    db_state = db.query(DailyRoundFloorState).filter(
        DailyRoundFloorState.round_id == round_id,
        DailyRoundFloorState.floor_id == floor_id
    ).first()
    if db_state:
        db_state.status = status
        db_state.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(db_state)
    return db_state

def save_building_layout(db: Session, building_id: uuid.UUID, floors_in: List[any]) -> Building:
    """Synchronizes full building floors, departments, and rooms layout structure by recreating nodes."""
    building = db.query(Building).filter(Building.id == building_id).first()
    if not building:
        raise ValueError("Building not found")
        
    # Delete existing layout nodes
    db.query(BuildingFloor).filter(BuildingFloor.building_id == building_id).delete()
    db.commit()
    
    # Save new layout structures
    for fl_idx, fl in enumerate(floors_in):
        db_floor = BuildingFloor(
            id=uuid.uuid4(),
            building_id=building_id,
            floor_name=fl.floor_name,
            order_index=fl.order_index
        )
        db.add(db_floor)
        db.flush()
        
        for dept in fl.departments:
            db_dept = BuildingDepartment(
                id=uuid.uuid4(),
                floor_id=db_floor.id,
                department_id=dept.department_id
            )
            db.add(db_dept)
            db.flush()
            
            for rm in dept.rooms:
                db_room = BuildingRoom(
                    id=uuid.uuid4(),
                    building_department_id=db_dept.id,
                    room_number=rm
                )
                db.add(db_room)
                
    db.commit()
    db.refresh(building)
    return building
