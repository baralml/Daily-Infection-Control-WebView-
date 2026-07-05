import sys
import os
import uuid
from datetime import datetime, timezone

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.audit import Department
from app.models.daily_round import Building, BuildingFloor, BuildingDepartment, BuildingRoom

def seed_default_building_layout():
    session = SessionLocal()
    try:
        print("Fetching existing departments...")
        # Get mapping of department code to database ID
        depts = {d.name.upper(): d.id for d in session.query(Department).all()}
        print(f"Loaded departments: {list(depts.keys())}")

        # Default mapping keys if name mismatch
        # Helper to find department ID or return first department
        def get_dept_id(keywords):
            for kw in keywords:
                for name, d_id in depts.items():
                    if kw.upper() in name:
                        return d_id
            return list(depts.values())[0] if depts else 1

        icu_id = get_dept_id(["ICU", "INTENSIVE"])
        ot_id = get_dept_id(["OT", "THEATRE", "SURGERY"])
        wards_id = get_dept_id(["WARD", "NURSING", "PATIENT"])
        cssd_id = get_dept_id(["CSSD", "STERILE", "DIRTY", "CLEAN"])
        lab_id = get_dept_id(["LAB", "BIOMEDICAL", "PATHOLOGY"])

        # Check if building exists
        building = session.query(Building).filter(Building.name == "Main Block").first()
        if building:
            print("Layout for 'Main Block' already exists. Re-seeding...")
            session.delete(building)
            session.commit()

        print("Seeding Building: 'Main Block'...")
        building = Building(id=uuid.uuid4(), name="Main Block", is_active=True)
        session.add(building)
        session.commit()

        # Seed Floors 1 to 7
        floors_config = [
            ("7th Floor", 7, [
                (wards_id, ["Premium Cabin A", "Premium Cabin B"]),
                (wards_id, ["VIP Suite 1", "VIP Suite 2"])
            ]),
            ("6th Floor", 6, [
                (icu_id, ["ICU Bed 1", "ICU Bed 2", "ICU Bed 3", "ICU Bed 4"]),
                (wards_id, ["Nursing Desk 6", "Clean Utility 6"])
            ]),
            ("5th Floor", 5, [
                (ot_id, ["OT Room 1", "OT Room 2", "Scrub Area 5"]),
                (cssd_id, ["Autoclave Bay", "Sterile Storage"])
            ]),
            ("4th Floor", 4, [
                (wards_id, ["General Ward Bed 101", "General Ward Bed 102", "General Ward Bed 103"])
            ]),
            ("3rd Floor", 3, [
                (lab_id, ["Radiology Room", "CT Scan Bay"])
            ]),
            ("2nd Floor", 2, [
                (lab_id, ["Pathology Lab", "Hematology Unit"])
            ]),
            ("1st Floor", 1, [
                (wards_id, ["Dialysis Station 1", "Dialysis Station 2"])
            ]),
            ("Ground Floor", 0, [
                (wards_id, ["Emergency Bed 1", "Emergency Bed 2", "Triage Desk"]),
                (wards_id, ["Billing Counter", "Main Reception"])
            ])
        ]

        for floor_name, idx, depts_config in floors_config:
            floor = BuildingFloor(
                id=uuid.uuid4(),
                building_id=building.id,
                floor_name=floor_name,
                order_index=idx
            )
            session.add(floor)
            session.commit()

            for dept_id, rooms in depts_config:
                b_dept = BuildingDepartment(
                    id=uuid.uuid4(),
                    floor_id=floor.id,
                    department_id=dept_id
                )
                session.add(b_dept)
                session.commit()

                for rm in rooms:
                    room = BuildingRoom(
                        id=uuid.uuid4(),
                        building_department_id=b_dept.id,
                        room_number=rm
                    )
                    session.add(room)
            
            print(f"  Seeded {floor_name}...")

        session.commit()
        print("Successfully seeded Main Block building floor and department layout configurations!")
    except Exception as e:
        session.rollback()
        print(f"Failed to seed layouts: {e}")
        raise e
    finally:
        session.close()

if __name__ == "__main__":
    seed_default_building_layout()
