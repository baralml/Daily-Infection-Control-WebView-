import sys
import os
import uuid
from datetime import datetime, timezone

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.auth import User
from app.models.audit import AuditTemplate, QuestionGroup, Question, ResponseTypeEnum

CHECKLISTS_DATA = [
    {
        "title": "Hand Hygiene Compliance Audit",
        "description": "Standard NABH audit checklist monitoring Hand Hygiene protocols.",
        "groups": [
            {
                "title": "1. Hand Hygiene Infrastructure",
                "questions": [
                    {"text": "Are handwash sinks clean, dry, and free of blockages?", "weight": 2},
                    {"text": "Is running tap water continuously available?", "weight": 3},
                    {"text": "Is liquid handwash soap available in a functional dispenser?", "weight": 2},
                    {"text": "Are clean, single-use paper towels or air dryers operational?", "weight": 2}
                ]
            },
            {
                "title": "2. Five Moments Compliance",
                "questions": [
                    {"text": "Do staff perform hand hygiene before touching a patient?", "weight": 3},
                    {"text": "Do staff perform hand hygiene before clean/aseptic procedures?", "weight": 3},
                    {"text": "Do staff perform hand hygiene after body fluid exposure risk?", "weight": 3},
                    {"text": "Do staff perform hand hygiene after touching a patient?", "weight": 3},
                    {"text": "Do staff perform hand hygiene after touching patient surroundings?", "weight": 2}
                ]
            }
        ]
    },
    {
        "title": "Biomedical Waste (BMW) Audit",
        "description": "Standard audit evaluating segregation, puncture-proof boxing, and safe transit.",
        "groups": [
            {
                "title": "1. Waste Segregation & Coding",
                "questions": [
                    {"text": "Are yellow bags used strictly for human anatomical waste and soiled linen?", "weight": 3},
                    {"text": "Are sharp containers/puncture-proof boxes used for needles and syringes?", "weight": 3},
                    {"text": "Are red bags utilized for recyclable contaminated plastic wastes?", "weight": 2},
                    {"text": "Is general municipal waste segregated into black bins?", "weight": 2}
                ]
            },
            {
                "title": "2. Labeling & Safe Transit",
                "questions": [
                    {"text": "Are all waste bags sealed and labeled with date and ward code before transport?", "weight": 2},
                    {"text": "Is waste transported in covered, dedicated trolleys to storage area?", "weight": 2}
                ]
            }
        ]
    },
    {
        "title": "PPE Compliance Audit",
        "description": "Monitors donning, doffing, stocking, and proper usage of PPE.",
        "groups": [
            {
                "title": "1. PPE Infrastructure & Availability",
                "questions": [
                    {"text": "Are PPE storage stations fully stocked with gloves, masks, and gowns?", "weight": 2},
                    {"text": "Are all PPE items available in appropriate sizes?", "weight": 2}
                ]
            },
            {
                "title": "2. Donning, Doffing & Disposal Protocol",
                "questions": [
                    {"text": "Do staff perform hand hygiene before donning and after doffing PPE?", "weight": 3},
                    {"text": "Are used PPE discarded immediately in designated color-coded bins?", "weight": 3},
                    {"text": "Are fit tests performed for N95 respirators where required?", "weight": 2}
                ]
            }
        ]
    },
    {
        "title": "Operation Theater Sterility Audit",
        "description": "Critical NABH compliance audit for OT HVAC air particulates, autoclaves and sterilizations.",
        "groups": [
            {
                "title": "1. Air Quality & Cleanliness",
                "questions": [
                    {"text": "Are OT humidity, temperature, and positive pressure levels monitored daily?", "weight": 3},
                    {"text": "Is clean zone disinfection protocol fully completed between surgeries?", "weight": 3},
                    {"text": "Are HEPA filters inspected and certified on schedule?", "weight": 3}
                ]
            },
            {
                "title": "2. Autoclave and Pack Sterilization",
                "questions": [
                    {"text": "Are biological/chemical validation indicators verified before opening instrument packs?", "weight": 3},
                    {"text": "Are autoclave maintenance logs updated and certified monthly?", "weight": 2}
                ]
            }
        ]
    },
    {
        "title": "Patient Room Audit",
        "description": "Checks wards, beds, and standard patient environments.",
        "groups": [
            {
                "title": "1. Bed & Surface Disinfection",
                "questions": [
                    {"text": "Are patient beds and mattresses sanitized with appropriate bleach dilutions upon discharge?", "weight": 3},
                    {"text": "Are high-touch surfaces (bedrails, tables, call buttons) wiped twice daily?", "weight": 2},
                    {"text": "Are bed curtains changed according to the department schedule?", "weight": 2}
                ]
            }
        ]
    },
    {
        "title": "Isolation Room Audit",
        "description": "Audits negative pressure, anterooms, and airborne protection units.",
        "groups": [
            {
                "title": "1. Pressure & Ventilation Parameters",
                "questions": [
                    {"text": "Is the negative pressure monitoring gauge operational and in the green zone?", "weight": 3},
                    {"text": "Is the anteroom door kept closed at all times?", "weight": 3}
                ]
            },
            {
                "title": "2. Isolation PPE & Waste",
                "questions": [
                    {"text": "Is there a dedicated PPE station and hand hygiene dispenser in the anteroom?", "weight": 3},
                    {"text": "Are biohazard double-bagging protocols practiced for waste transit?", "weight": 2}
                ]
            }
        ]
    },
    {
        "title": "Nurses Station & Medication Room Audit",
        "description": "Audits injection safety, drug preparation, and workstation hygiene.",
        "groups": [
            {
                "title": "1. Medication Preparation Hygiene",
                "questions": [
                    {"text": "Are hands sanitized immediately before drawing medications?", "weight": 3},
                    {"text": "Are multi-dose vials labeled with discard dates within 28 days of opening?", "weight": 3},
                    {"text": "Is the drug preparation counter cleaned and kept clutter-free?", "weight": 2}
                ]
            }
        ]
    },
    {
        "title": "Clean Utility & Central Sterile Audit",
        "description": "Reviews sterile supply store (CSSD) and storage conditions.",
        "groups": [
            {
                "title": "1. Sterile Storage Integrity",
                "questions": [
                    {"text": "Are sterile packs stored at least 8 inches off the floor and 18 inches from the ceiling?", "weight": 2},
                    {"text": "Are sterile pack wrappers inspected for tears, moisture, or expiry dates?", "weight": 3},
                    {"text": "Is temperature and humidity in the sterile store room within limits?", "weight": 2}
                ]
            }
        ]
    },
    {
        "title": "Dirty Utility & Soiled Linen Audit",
        "description": "Reviews dirty holding areas and waste sluice units.",
        "groups": [
            {
                "title": "1. Sluice Room & Linen Sorting",
                "questions": [
                    {"text": "Are soiled linens stored in leak-proof, color-coded bags?", "weight": 2},
                    {"text": "Are sluice machines and disposal drains clean and functioning?", "weight": 2},
                    {"text": "Is appropriate protective wear (aprons, heavy gloves) available for staff?", "weight": 3}
                ]
            }
        ]
    },
    {
        "title": "Environmental Cleaning Audit",
        "description": "General housekeeping routines and chemical dilutions.",
        "groups": [
            {
                "title": "1. Microfiber & Mop Protocols",
                "questions": [
                    {"text": "Are color-coded microfiber cloths used correctly (e.g. red for toilets)?", "weight": 2},
                    {"text": "Are cleaning chemicals prepared daily with exact dilution ratios?", "weight": 3},
                    {"text": "Are high-touch cleaning logs signed by supervisors on schedule?", "weight": 2}
                ]
            }
        ]
    },
    {
        "title": "Housekeeping Quality Audit",
        "description": "Housekeeping worker training, techniques, and storage.",
        "groups": [
            {
                "title": "1. Cleaner Knowledge & Protocols",
                "questions": [
                    {"text": "Can housekeeping staff demonstrate correct mop cleaning and drying steps?", "weight": 2},
                    {"text": "Are housekeeping carts clean and kept organized?", "weight": 2},
                    {"text": "Is spill management kit available and fully stocked?", "weight": 3}
                ]
            }
        ]
    },
    {
        "title": "Medical Equipment Cleaning Audit",
        "description": "Disinfection of monitors, ventilators, and clinical machinery.",
        "groups": [
            {
                "title": "1. Clinical Machine Sanitization",
                "questions": [
                    {"text": "Are ventilators and patient monitors disinfected between patient shifts?", "weight": 3},
                    {"text": "Are blood pressure cuffs and pulse oximeter probes wiped with disinfectant?", "weight": 2},
                    {"text": "Are IV poles and syringe pumps clean and free of visible dust or stains?", "weight": 2}
                ]
            }
        ]
    },
    {
        "title": "Kitchen & Pantry Audit",
        "description": "Food safety, hygiene, and dietary control parameters.",
        "groups": [
            {
                "title": "1. Dietary Hygiene",
                "questions": [
                    {"text": "Do food handlers wear hair nets, aprons, and gloves?", "weight": 3},
                    {"text": "Are raw ingredients and cooked meals stored in separate refrigerators?", "weight": 3},
                    {"text": "Are kitchen water quality reports certified and updated?", "weight": 2}
                ]
            }
        ]
    },
    {
        "title": "Staff Break Room Audit",
        "description": "Break room cleanliness, pantry hygiene, and locker storage.",
        "groups": [
            {
                "title": "1. Break Area Hygiene",
                "questions": [
                    {"text": "Is the break room sink clean and stocked with hand hygiene items?", "weight": 2},
                    {"text": "Are employee lockers clean and free of decaying food items?", "weight": 2}
                ]
            }
        ]
    },
    {
        "title": "Refrigerator & Temperature Log Audit",
        "description": "Reviews pharmacies, labs, and ward cold-chain storages.",
        "groups": [
            {
                "title": "1. Cold-Chain Control",
                "questions": [
                    {"text": "Are refrigerator temperature logs filled out twice daily (target 2-8°C)?", "weight": 3},
                    {"text": "Are medications stored separately from laboratory specimens?", "weight": 3},
                    {"text": "Is there a functional backup power supply or generator trigger?", "weight": 2}
                ]
            }
        ]
    },
    {
        "title": "Infection Control Logbook Audit",
        "description": "Checks documentation, isolation ward records, and cleaning logs.",
        "groups": [
            {
                "title": "1. Documentation Accuracy",
                "questions": [
                    {"text": "Are all daily cleaning logs signed off and filed correctly?", "weight": 2},
                    {"text": "Are isolation ward visitor and staff logs completed without gaps?", "weight": 3},
                    {"text": "Are needle-stick and splash incidents logged in the register?", "weight": 3}
                ]
            }
        ]
    },
    {
        "title": "Staff Infection Control Knowledge Audit",
        "description": "Audits employee training on isolation and safety protocols.",
        "groups": [
            {
                "title": "1. Core Staff Knowledge",
                "questions": [
                    {"text": "Can randomly selected staff demonstrate the 6 steps of handwashing?", "weight": 3},
                    {"text": "Do staff know the immediate actions for a needle-stick injury?", "weight": 3},
                    {"text": "Can staff identify color coding for biomedical waste bags?", "weight": 2}
                ]
            }
        ]
    },
    {
        "title": "Linen Management Audit",
        "description": "Linen storage, transportation carts, and laundry parameters.",
        "groups": [
            {
                "title": "1. Clean & Dirty Linen Separation",
                "questions": [
                    {"text": "Are clean and dirty linen transport carts kept completely segregated?", "weight": 3},
                    {"text": "Is the clean linen storage area dry, elevated, and dust-free?", "weight": 2},
                    {"text": "Is linen laundry water temperature verified to kill pathogens?", "weight": 2}
                ]
            }
        ]
    },
    {
        "title": "Pest Control Audit",
        "description": "Pest logs, screens, and bait station checks.",
        "groups": [
            {
                "title": "1. Facility Pest Barriers",
                "questions": [
                    {"text": "Are mesh screens on windows and door seal strips intact?", "weight": 2},
                    {"text": "Are bait stations and pest traps checked and signed off by vendors?", "weight": 2},
                    {"text": "Are chemical approval certifications for pesticides on file?", "weight": 2}
                ]
            }
        ]
    },
    {
        "title": "Air Quality & Ventilation Audit",
        "description": "Reviews ACH logs, pressure balances, and duct cleanups.",
        "groups": [
            {
                "title": "1. Ventilation Standards",
                "questions": [
                    {"text": "Are Air Changes per Hour (ACH) certified annually in OT and ICU?", "weight": 3},
                    {"text": "Are positive and negative pressure rooms calibrated and working?", "weight": 3},
                    {"text": "Is there a documented schedule for air duct cleaning and maintenance?", "weight": 2}
                ]
            }
        ]
    },
    {
        "title": "Water & Sanitation Audit",
        "description": "Checks water purity logs, chlorine levels, and drain flows.",
        "groups": [
            {
                "title": "1. Water Purity Parameters",
                "questions": [
                    {"text": "Are water tank microbiological reports updated monthly?", "weight": 3},
                    {"text": "Is the residual chlorine level in tap water checked and logged daily?", "weight": 3},
                    {"text": "Are drinking water dispensers and filters serviced on schedule?", "weight": 2}
                ]
            }
        ]
    },
    {
        "title": "Sharps Safety Audit",
        "description": "Checks sharps bins, hub cutters, and safety needles.",
        "groups": [
            {
                "title": "1. Sharps Disposal Controls",
                "questions": [
                    {"text": "Are sharps container boxes discarded before they fill beyond the 3/4 line?", "weight": 3},
                    {"text": "Are hub cutters or needle destroyers functional at the point of use?", "weight": 3},
                    {"text": "Are safety-engineered syringes and cannulas utilized where available?", "weight": 2}
                ]
            }
        ]
    },
    {
        "title": "Medication Safety Audit",
        "description": "Reviews labeling, LASA drug setups, and prep areas.",
        "groups": [
            {
                "title": "1. Drug Prep and Safety",
                "questions": [
                    {"text": "Are prepared syringes labeled immediately with drug name, concentration, and date?", "weight": 3},
                    {"text": "Are LASA (Look-Alike Sound-Alike) drugs stored in separated, color-coded trays?", "weight": 3},
                    {"text": "Are double-checks performed by two nurses before high-alert drug infusion?", "weight": 3}
                ]
            }
        ]
    },
    {
        "title": "Laboratory Infection Control Audit",
        "description": "Checks biosafety cabinets, waste handling, and lab vaccinations.",
        "groups": [
            {
                "title": "1. Lab Safety Parameters",
                "questions": [
                    {"text": "Are biohazard disposal bins available at all laboratory workstations?", "weight": 3},
                    {"text": "Are biosafety cabinet airflows certified within the last 12 months?", "weight": 3},
                    {"text": "Is staff vaccination documentation (Hepatitis B, etc.) complete?", "weight": 3}
                ]
            }
        ]
    },
    {
        "title": "ICU Infection Control Audit",
        "description": "ICU bundle compliance, VAP, CLABSI, and visitor logs.",
        "groups": [
            {
                "title": "1. Bundle Compliance",
                "questions": [
                    {"text": "Is VAP (Ventilator-Associated Pneumonia) bundle checklist completed daily?", "weight": 3},
                    {"text": "Are central line site care and dressing changes logged according to protocol?", "weight": 3},
                    {"text": "Is the catheter-associated urinary tract infection (CAUTI) bundle followed?", "weight": 3}
                ]
            }
        ]
    },
    {
        "title": "Emergency Department Audit",
        "description": "Triage isolation, stretchers cleaning, and splash gear.",
        "groups": [
            {
                "title": "1. Emergency Care Control",
                "questions": [
                    {"text": "Are triage protocols in place to immediately isolate suspected respiratory patients?", "weight": 3},
                    {"text": "Are stretcher mattresses disinfected between emergency cases?", "weight": 2},
                    {"text": "Is emergency eye-wash station functional and checked weekly?", "weight": 2}
                ]
            }
        ]
    },
    {
        "title": "Dialysis Unit Audit",
        "description": "Reviews dialysis machines routing, cleaning, and site cares.",
        "groups": [
            {
                "title": "1. Dialysis Sterility Protocol",
                "questions": [
                    {"text": "Are dedicated machines routed and labeled for HBV/HCV positive patients?", "weight": 3},
                    {"text": "Are dialysate fluid microbiological testing logs up to date?", "weight": 3},
                    {"text": "Do staff perform catheter access site disinfection before hookup?", "weight": 3}
                ]
            }
        ]
    },
    {
        "title": "NICU/PICU Infection Control Audit",
        "description": "Incubator logs, breast milk storage, and hand hygiene coaching.",
        "groups": [
            {
                "title": "1. Pediatric Sterility",
                "questions": [
                    {"text": "Are incubators and warmers disinfected according to pediatric schedule?", "weight": 3},
                    {"text": "Are breast milk storage containers labeled with name and date inside freezer?", "weight": 2},
                    {"text": "Do visitors perform handwashing and wear isolation gowns before entry?", "weight": 3}
                ]
            }
        ]
    },
    {
        "title": "Fire & Safety Observation Audit",
        "description": "Exit signs, fire extinguishers tags, and electrical panel clearings.",
        "groups": [
            {
                "title": "1. Fire Safety Checks",
                "questions": [
                    {"text": "Are exit paths and fire doors kept completely clear of equipment and boxes?", "weight": 2},
                    {"text": "Are fire extinguishers inspected and tags signed within the last 12 months?", "weight": 2},
                    {"text": "Are electrical panel doors closed and kept clear of obstructions?", "weight": 2}
                ]
            }
        ]
    },
    {
        "title": "General Facility Audit",
        "description": "Corridors, signage, and visitor hygiene stations.",
        "groups": [
            {
                "title": "1. Facility Layout Safety",
                "questions": [
                    {"text": "Are hand hygiene stations visible at all main corridors and elevator lobbies?", "weight": 2},
                    {"text": "Is infection control signage clearly visible in patient waiting areas?", "weight": 2}
                ]
            }
        ]
    }
]

def seed_checklists():
    session = SessionLocal()
    try:
        # Get admin user ID
        admin = session.query(User).filter_by(email="admin@hospital.com").first()
        if not admin:
            print("Error: admin user not found in database.")
            return
        
        admin_id = admin.id
        print(f"Found admin user: {admin.email} (ID: {admin_id})")

        # Iterate over checklist data
        for cdata in CHECKLISTS_DATA:
            title = cdata["title"]
            desc = cdata["description"]

            # Remove existing template with same title to prevent duplication
            existing = session.query(AuditTemplate).filter_by(title=title).first()
            if existing:
                print(f"Removing existing checklist: '{title}'")
                session.delete(existing)
                session.commit()

            # Create new template
            template = AuditTemplate(
                id=uuid.uuid4(),
                title=title,
                description=desc,
                version=1,
                is_active=True,
                created_by=admin_id
            )
            session.add(template)
            session.commit()
            print(f"Created template: '{title}' (ID: {template.id})")

            # Create groups and questions
            for g_idx, gdata in enumerate(cdata["groups"]):
                group = QuestionGroup(
                    id=uuid.uuid4(),
                    template_id=template.id,
                    title=gdata["title"],
                    order_num=g_idx + 1
                )
                session.add(group)
                session.commit()

                # Add questions
                for q_idx, qdata in enumerate(gdata["questions"]):
                    question = Question(
                        id=uuid.uuid4(),
                        group_id=group.id,
                        text=qdata["text"],
                        response_type=ResponseTypeEnum.RADIO,
                        options=["Yes", "No", "N/A"],
                        compliance_weight=qdata["weight"],
                        is_required=True,
                        is_active=True,
                        order_num=q_idx + 1
                    )
                    session.add(question)
                
                session.commit()
                print(f"  Added Group: '{group.title}' with {len(gdata['questions'])} questions.")

        print("Seeding completed successfully!")
    except Exception as e:
        session.rollback()
        print(f"Transaction failed: {e}")
        raise e
    finally:
        session.close()

if __name__ == "__main__":
    seed_checklists()
