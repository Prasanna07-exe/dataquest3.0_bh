from dataclasses import dataclass
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.technician import Technician

@dataclass
class MatchingFactors:
    skill_match: float
    availability: float
    sla_feasibility: float
    distance: float
    familiarity: float
    workload: float
    performance: float


WEIGHTS = {
    "skill_match": 0.25,
    "availability": 0.15,
    "sla_feasibility": 0.15,
    "distance": 0.15,
    "familiarity": 0.10,
    "workload": 0.10,
    "performance": 0.10,
}


def calculate_match_score(factors: MatchingFactors) -> float:
    score = (
        factors.skill_match * WEIGHTS["skill_match"]
        + factors.availability * WEIGHTS["availability"]
        + factors.sla_feasibility * WEIGHTS["sla_feasibility"]
        + factors.distance * WEIGHTS["distance"]
        + factors.familiarity * WEIGHTS["familiarity"]
        + factors.workload * WEIGHTS["workload"]
        + factors.performance * WEIGHTS["performance"]
    )

    return round(max(0.0, min(100.0, score)), 2)

def rank_technicians(
    db: Session,
    candidates: list[tuple[Technician, MatchingFactors]],
) -> list[tuple[Technician, float]]:
    ranked = []

    for technician, factors in candidates:
        score = calculate_match_score(factors)
        ranked.append((technician, score))

    ranked.sort(key=lambda item: item[1], reverse=True)

    return ranked

def filter_active_technicians(
    technicians: list[Technician],
) -> list[Technician]:
    return [
        technician
        for technician in technicians
        if technician.is_active
    ]