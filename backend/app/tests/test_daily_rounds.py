import uuid
from datetime import datetime, timezone
import pytest
from app.models.auth import Role, User
from app.models.audit import Department, RiskLevelEnum
from app.models.daily_round import DailyRound, DailyRoundObservation, RoundStatusEnum, MasterObservation
from app.crud.crud_daily_round import (
    create_daily_round, get_daily_round_details, get_daily_rounds,
    add_observation_to_round, finish_daily_round, search_master_observations,
    create_building, get_buildings, get_building_layout, save_building_layout, update_floor_state
)
from app.schemas.daily_round import (
    DailyRoundCreate, DailyRoundObservationCreate, BuildingFloorCreate, BuildingDepartmentCreate
)

def test_daily_rounds_lifecycle(db):
    """Verifies daily round creation, observation logging, fuzzy search, and sealing."""
    # 1. Setup Role, User, Department
    role = Role(name="ICO", permissions={})
    db.add(role)
    db.commit()

    user = User(email="ico_round@hosp.com", hashed_password="pw", full_name="Rounder", role_id=role.id)
    db.add(user)

    dept = Department(name="Emergency Unit", code="ER")
    db.add(dept)
    db.commit()

    # 2. Setup Master Observations
    obs1 = MasterObservation(text="Dust on Hand Rail", category="Dust", default_severity=RiskLevelEnum.LOW)
    obs2 = MasterObservation(text="Yellow Bin Overflowing", category="BMW", default_severity=RiskLevelEnum.HIGH)
    db.add_all([obs1, obs2])
    db.commit()

    # 3. Test Search Master Observations
    results = search_master_observations(db, "dust")
    assert len(results) == 1
    assert results[0].text == "Dust on Hand Rail"

    # 4. Test Create Daily Round
    round_in = DailyRoundCreate(
        hospital="ABC Hospital",
        building="Main Block",
        floor="3rd Floor",
        department_id=dept.id,
        round_type="Morning"
    )
    db_round = create_daily_round(db, round_in, user.id)
    assert db_round.hospital == "ABC Hospital"
    assert db_round.status == RoundStatusEnum.DRAFT

    # 5. Add Observation
    obs_in = DailyRoundObservationCreate(
        observation_text="Dust on Hand Rail",
        category="Dust",
        floor_name="3rd Floor",
        department_id=dept.id,
        room_number="ER-1",
        severity=RiskLevelEnum.LOW,
        remarks="Needs immediate dusting",
        has_capa=False
    )
    db_obs = add_observation_to_round(db, db_round.id, obs_in)
    assert db_obs.observation_text == "Dust on Hand Rail"
    assert db_obs.room_number == "ER-1"

    # 6. Fetch Round Details
    details = get_daily_round_details(db, db_round.id)
    assert details is not None
    assert len(details.observations) == 1
    assert details.observations[0].id == db_obs.id

    # 7. Finish Round
    finished = finish_daily_round(db, db_round.id)
    assert finished.status == RoundStatusEnum.COMPLETED
    assert finished.ended_at is not None

def test_layouts_lifecycle(db):
    """Verifies building layouts configuration, sorting, and nested room saves."""
    # 1. Setup Department
    dept = Department(name="Cardiac Care", code="CCU")
    db.add(dept)
    db.commit()

    # 2. Create Building
    b = create_building(db, "Main Wing")
    assert b.name == "Main Wing"

    # 3. List Buildings
    buildings = get_buildings(db)
    assert len(buildings) == 1
    assert buildings[0].name == "Main Wing"

    # 4. Save Layout
    floor_data = [
        BuildingFloorCreate(
            floor_name="Floor 3",
            order_index=3,
            departments=[
                BuildingDepartmentCreate(
                    department_id=dept.id,
                    rooms=["CCU-10", "CCU-11"]
                )
            ]
        )
    ]
    save_building_layout(db, b.id, floor_data)

    # 5. Fetch Layout
    layout = get_building_layout(db, b.id)
    assert layout is not None
    assert len(layout.floors) == 1
    assert layout.floors[0].floor_name == "Floor 3"
    assert len(layout.floors[0].departments) == 1
    assert layout.floors[0].departments[0].department_id == dept.id
    assert len(layout.floors[0].departments[0].rooms) == 2
    assert layout.floors[0].departments[0].rooms[0].room_number == "CCU-10"
