from typing import Any


def classify_request(
    title: str,
    description: str,
    maintenance_mode: str,
) -> dict[str, Any]:
    text = f"{title} {description}".lower()

    if "vibration" in text or "bearing" in text:
        return {
            "issue_type": "MECHANICAL",
            "failure_mode": "ABNORMAL_VIBRATION",
            "severity": "HIGH",
            "required_skills": ["MECHANICAL"],
            "required_tools": ["VIBRATION_METER"],
            "required_parts": ["BRG-6205"],
            "similar_failures": [],
            "confidence": 0.92,
            "model_name": "dqbh-deterministic-fallback",
            "analysis_result": {
                "source": "deterministic_fallback",
                "maintenance_mode": maintenance_mode,
                "reason": "Vibration-related mechanical failure detected from request text.",
            },
        }

    if "electrical" in text or "fuse" in text or "voltage" in text:
        return {
            "issue_type": "ELECTRICAL",
            "failure_mode": "ELECTRICAL_FAULT",
            "severity": "MEDIUM",
            "required_skills": ["ELECTRICAL"],
            "required_tools": ["MULTIMETER"],
            "required_parts": ["FUSE-IND-10A"],
            "similar_failures": [],
            "confidence": 0.85,
            "model_name": "dqbh-deterministic-fallback",
            "analysis_result": {
                "source": "deterministic_fallback",
                "maintenance_mode": maintenance_mode,
                "reason": "Electrical fault indicators detected from request text.",
            },
        }

    return {
        "issue_type": "GENERAL",
        "failure_mode": "UNCLASSIFIED",
        "severity": "MEDIUM",
        "required_skills": [],
        "required_tools": [],
        "required_parts": [],
        "similar_failures": [],
        "confidence": 0.50,
        "model_name": "dqbh-deterministic-fallback",
        "analysis_result": {
            "source": "deterministic_fallback",
            "maintenance_mode": maintenance_mode,
            "reason": "No high-confidence failure pattern detected.",
        },
    }