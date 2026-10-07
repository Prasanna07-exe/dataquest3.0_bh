from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from app.core.database import SessionLocal
from app.models.customer import Customer, Machine, MachineModel, Site
from app.models.identity import Role, User
from app.models.inventory import InventoryBalance, Part, Warehouse
from app.models.technician import (
    Skill,
    Technician,
    TechnicianAvailability,
    TechnicianSkill,
)
from app.models.checklist import ChecklistTemplate, ChecklistItem

def seed():
    db = SessionLocal()

    try:
        role = db.scalar(
            select(Role).where(Role.name == "OPERATIONS_MANAGER")
        )

        if role is None:
            role = Role(
                name="OPERATIONS_MANAGER",
                description="Demo operations manager role",
            )
            db.add(role)
            db.flush()

        user = db.scalar(
            select(User).where(User.email == "manager@dqbh.local")
        )

        if user is None:
            user = User(
                email="manager@dqbh.local",
                password_hash="demo-password-hash",
                full_name="Demo Manager",
                role_id=role.id,
                is_active=True,
            )
            db.add(user)
            db.flush()

        customer = db.scalar(
            select(Customer).where(Customer.code == "DEMO-CUST")
        )

        if customer is None:
            customer = Customer(
                name="Demo Industries",
                code="DEMO-CUST",
                contact_email="customer@dqbh.local",
                contact_phone="+91-9000000000",
                is_active=True,
                created_at=datetime.now(timezone.utc),
            )
            db.add(customer)
            db.flush()

        site = db.scalar(
            select(Site).where(Site.code == "CHN-PLANT-01")
        )

        if site is None:
            site = Site(
                customer_id=customer.id,
                name="Chennai Plant",
                code="CHN-PLANT-01",
                address_line="Industrial Estate",
                city="Chennai",
                state="Tamil Nadu",
                country="India",
                latitude=13.0827,
                longitude=80.2707,
                is_active=True,
                created_at=datetime.now(timezone.utc),
            )
            db.add(site)
            db.flush()

        machine_model = db.scalar(
            select(MachineModel).where(
                MachineModel.model_code == "DM-X100"
            )
        )

        if machine_model is None:
            machine_model = MachineModel(
                manufacturer="Demo Motors",
                model_name="Industrial Motor X100",
                model_code="DM-X100",
                description="Demo industrial motor for DQBH workflow",
            )
            db.add(machine_model)
            db.flush()

        machine = db.scalar(
            select(Machine).where(
                Machine.asset_code == "M-104"
            )
        )

        if machine is None:
            machine = Machine(
                site_id=site.id,
                machine_model_id=machine_model.id,
                asset_code="M-104",
                serial_number="SN-M104-001",
                name="Production Motor M-104",
                status="OPERATIONAL",
                is_active=True,
            )
            db.add(machine)
            db.flush()

        mechanical_skill = db.scalar(
            select(Skill).where(Skill.name == "MECHANICAL")
        )

        if mechanical_skill is None:
            mechanical_skill = Skill(
                name="MECHANICAL",
                description="Industrial mechanical maintenance",
            )
            db.add(mechanical_skill)
            db.flush()

        electrical_skill = db.scalar(
            select(Skill).where(Skill.name == "ELECTRICAL")
        )

        if electrical_skill is None:
            electrical_skill = Skill(
                name="ELECTRICAL",
                description="Industrial electrical maintenance",
            )
            db.add(electrical_skill)
            db.flush()

        technician_user_1 = db.scalar(
            select(User).where(User.email == "tech1@dqbh.local")
        )

        if technician_user_1 is None:
            technician_user_1 = User(
                email="tech1@dqbh.local",
                password_hash="demo-password-hash",
                full_name="Arun Technician",
                role_id=role.id,
                is_active=True,
            )
            db.add(technician_user_1)
            db.flush()

        technician_user_2 = db.scalar(
            select(User).where(User.email == "tech2@dqbh.local")
        )

        if technician_user_2 is None:
            technician_user_2 = User(
                email="tech2@dqbh.local",
                password_hash="demo-password-hash",
                full_name="Vikram Technician",
                role_id=role.id,
                is_active=True,
            )
            db.add(technician_user_2)
            db.flush()

        technician_1 = db.scalar(
            select(Technician).where(
                Technician.employee_code == "TECH-001"
            )
        )

        if technician_1 is None:
            technician_1 = Technician(
                user_id=technician_user_1.id,
                employee_code="TECH-001",
                home_latitude=13.0827,
                home_longitude=80.2707,
                workload_score=25,
                performance_score=90,
                is_active=True,
            )
            db.add(technician_1)
            db.flush()

        technician_2 = db.scalar(
            select(Technician).where(
                Technician.employee_code == "TECH-002"
            )
        )

        if technician_2 is None:
            technician_2 = Technician(
                user_id=technician_user_2.id,
                employee_code="TECH-002",
                home_latitude=13.0500,
                home_longitude=80.2200,
                workload_score=60,
                performance_score=75,
                is_active=True,
            )
            db.add(technician_2)
            db.flush()

        if db.get(
            TechnicianSkill,
            {
                "technician_id": technician_1.id,
                "skill_id": mechanical_skill.id,
            },
        ) is None:
            db.add(
                TechnicianSkill(
                    technician_id=technician_1.id,
                    skill_id=mechanical_skill.id,
                    proficiency_level="EXPERT",
                )
            )

        if db.get(
            TechnicianSkill,
            {
                "technician_id": technician_2.id,
                "skill_id": mechanical_skill.id,
            },
        ) is None:
            db.add(
                TechnicianSkill(
                    technician_id=technician_2.id,
                    skill_id=mechanical_skill.id,
                    proficiency_level="INTERMEDIATE",
                )
            )

        availability_start = datetime.now(timezone.utc)
        availability_end = availability_start + timedelta(hours=8)

        existing_availability = db.scalar(
            select(TechnicianAvailability).where(
                TechnicianAvailability.technician_id == technician_1.id
            )
        )

        if existing_availability is None:
            db.add(
                TechnicianAvailability(
                    technician_id=technician_1.id,
                    start_at=availability_start,
                    end_at=availability_end,
                    status="AVAILABLE",
                )
            )

        existing_availability = db.scalar(
            select(TechnicianAvailability).where(
                TechnicianAvailability.technician_id == technician_2.id
            )
        )

        if existing_availability is None:
            db.add(
                TechnicianAvailability(
                    technician_id=technician_2.id,
                    start_at=availability_start,
                    end_at=availability_end,
                    status="AVAILABLE",
                )
            )

        local_warehouse = db.scalar(
            select(Warehouse).where(Warehouse.code == "WH-CHN-01")
        )

        if local_warehouse is None:
            local_warehouse = Warehouse(
                name="Chennai Plant Warehouse",
                code="WH-CHN-01",
                address_line="Industrial Estate",
                city="Chennai",
                state="Tamil Nadu",
                country="India",
                latitude=13.0827,
                longitude=80.2707,
                description="Primary warehouse near Chennai Plant",
                is_active=True,
            )
            db.add(local_warehouse)
            db.flush()

        alternate_warehouse = db.scalar(
            select(Warehouse).where(Warehouse.code == "WH-CHN-02")
        )

        if alternate_warehouse is None:
            alternate_warehouse = Warehouse(
                name="Chennai Regional Warehouse",
                code="WH-CHN-02",
                address_line="Ambattur Industrial Area",
                city="Chennai",
                state="Tamil Nadu",
                country="India",
                latitude=13.1143,
                longitude=80.1548,
                description="Alternate warehouse for shortage resolution",
                is_active=True,
            )
            db.add(alternate_warehouse)
            db.flush()

        bearing = db.scalar(
            select(Part).where(Part.part_code == "BRG-6205")
        )

        if bearing is None:
            bearing = Part(
                name="Industrial Bearing 6205",
                part_code="BRG-6205",
                description="Replacement bearing for industrial motor",
                unit_cost=850,
                is_active=True,
            )
            db.add(bearing)
            db.flush()

        fuse = db.scalar(
            select(Part).where(Part.part_code == "FUSE-IND-10A")
        )

        if fuse is None:
            fuse = Part(
                name="Industrial Fuse 10A",
                part_code="FUSE-IND-10A",
                description="Industrial protection fuse",
                unit_cost=120,
                is_active=True,
            )
            db.add(fuse)
            db.flush()

        bearing_balance = db.scalar(
            select(InventoryBalance).where(
                InventoryBalance.warehouse_id == local_warehouse.id,
                InventoryBalance.part_id == bearing.id,
            )
        )

        if bearing_balance is None:
            db.add(
                InventoryBalance(
                    warehouse_id=local_warehouse.id,
                    part_id=bearing.id,
                    quantity_on_hand=10,
                    quantity_reserved=0,
                    reorder_level=3,
                )
            )

        fuse_local_balance = db.scalar(
            select(InventoryBalance).where(
                InventoryBalance.warehouse_id == local_warehouse.id,
                InventoryBalance.part_id == fuse.id,
            )
        )

        if fuse_local_balance is None:
            db.add(
                InventoryBalance(
                    warehouse_id=local_warehouse.id,
                    part_id=fuse.id,
                    quantity_on_hand=0,
                    quantity_reserved=0,
                    reorder_level=5,
                )
            )

        fuse_alternate_balance = db.scalar(
            select(InventoryBalance).where(
                InventoryBalance.warehouse_id == alternate_warehouse.id,
                InventoryBalance.part_id == fuse.id,
            )
        )

        if fuse_alternate_balance is None:
            db.add(
                InventoryBalance(
                    warehouse_id=alternate_warehouse.id,
                    part_id=fuse.id,
                    quantity_on_hand=20,
                    quantity_reserved=0,
                    reorder_level=5,
                )
            )
        db.commit()
        checklist_template = (
            db.query(ChecklistTemplate)
            .filter(ChecklistTemplate.name == "M-104 Reactive Maintenance Checklist")
            .first()
        )

        if checklist_template is None:
            checklist_template = ChecklistTemplate(
                name="M-104 Reactive Maintenance Checklist",
                maintenance_mode="REACTIVE",
                machine_type="DM-X100",
                is_active=True,
            )
            db.add(checklist_template)
            db.flush()

            checklist_items = [
                "Safety isolation confirmed",
                "Bearing assembly inspected",
                "Abnormal vibration source identified",
                "Replacement bearing installed",
                "Machine test run completed",
                "Final vibration measurement recorded",
            ]

            for index, item_text in enumerate(checklist_items, start=1):
                db.add(
                    ChecklistItem(
                        template_id=checklist_template.id,
                        item_text=item_text,
                        is_mandatory=True,
                        sequence=index,
                    )
                )
            db.commit()
        print("Seed completed successfully.")
        print(f"User ID: {user.id}")
        print(f"Customer ID: {customer.id}")
        print(f"Site ID: {site.id}")
        print(f"Machine ID: {machine.id}")
        print(f"Machine asset: {machine.asset_code}")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed()