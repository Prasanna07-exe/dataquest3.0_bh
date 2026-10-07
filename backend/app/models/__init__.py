from app.models.customer import Customer, Machine, MachineModel, Site
from app.models.identity import Permission, Role, RolePermission, User
from app.models.service_request import RequestAIAnalysis, ServiceRequest
from app.models.technician import Skill, Technician, TechnicianAvailability, TechnicianSkill
from app.models.inventory import (
    InventoryBalance,
    InventoryTransfer,
    Part,
    Warehouse,
)
from app.models.assignment import Assignment
from app.models.reservation import ResourceReservation
from app.models.approval import Approval
from app.models.work_log import WorkLog
from app.models.checklist import ChecklistTemplate, ChecklistItem, WorkChecklist
from app.models.exception_event import ExceptionEvent
from app.models.service_history import ServiceHistory
from app.models.attachment import Attachment

__all__ = [
    "Customer",
    "Machine",
    "MachineModel",
    "Site",
    "Permission",
    "Role",
    "RolePermission",
    "User",
    "ServiceRequest",
    "RequestAIAnalysis",
    "Skill",
    "Technician",
    "TechnicianAvailability",
    "TechnicianSkill",
    "InventoryBalance",
    "InventoryTransfer",
    "Part",
    "Warehouse",
    "Assignment",
    "ResourceReservation",
    "Approval",
    "ChecklistTemplate",
    "ChecklistItem",
    "WorkChecklist",
    "Attachment",
    "ServiceHistory",
]