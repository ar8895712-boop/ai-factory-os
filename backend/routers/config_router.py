# ==============================================================
# backend/routers/config_router.py — Live Business Settings API
# ==============================================================
"""
Exposes endpoints to view and dynamically update business assumptions
(downtime cost in ₹, tariffs, penalties) and health score weights in config.yaml.
Allows live editing directly from the UI dashboard.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict
import yaml
from fastapi import APIRouter
from pydantic import BaseModel

from backend.config import PROJECT_ROOT, CONFIG_PATH, get_settings

router = APIRouter(prefix="/api/config", tags=["config"])


class BusinessConfigUpdate(BaseModel):
    loss_per_hour: float
    planned_maintenance_cost_per_hour: float
    energy_tariff_per_kwh: float
    machine_power_kw: float
    delay_penalty_per_hour: float
    daily_production_target: int
    avg_spare_part_cost: float


class HealthWeightsUpdate(BaseModel):
    rul_weight: float
    anomaly_weight: float
    failure_weight: float


@router.get("/business")
def get_business_config() -> Dict[str, Any]:
    """Returns all current business assumptions and financial constants in ₹."""
    cfg = get_settings()
    return cfg.business.model_dump()


@router.put("/business")
def update_business_config(update_data: BusinessConfigUpdate) -> Dict[str, Any]:
    """
    Updates business constants in config.yaml and applies them to live settings.
    Editable from the UI dashboard.
    """
    cfg = get_settings()
    # Update in-memory
    for key, val in update_data.model_dump().items():
        setattr(cfg.business, key, val)

    # Persist back to config.yaml
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        raw_yaml = yaml.safe_load(f)

    for key, val in update_data.model_dump().items():
        raw_yaml["business"][key] = val

    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        yaml.safe_dump(raw_yaml, f, sort_keys=False)

    return {
        "status": "success",
        "message": "Business assumptions updated successfully.",
        "business": cfg.business.model_dump(),
    }


@router.get("/health-weights")
def get_health_weights() -> Dict[str, Any]:
    """Returns current composite health score weights."""
    cfg = get_settings()
    return cfg.health_score.model_dump()


@router.put("/health-weights")
def update_health_weights(weights: HealthWeightsUpdate) -> Dict[str, Any]:
    """Updates composite health score weights."""
    cfg = get_settings()
    total = weights.rul_weight + weights.anomaly_weight + weights.failure_weight
    if abs(total - 1.0) > 0.01:
        return {"status": "error", "message": f"Weights must sum to 1.0 (got {total:.2f})"}

    cfg.health_score.rul_weight = weights.rul_weight
    cfg.health_score.anomaly_weight = weights.anomaly_weight
    cfg.health_score.failure_weight = weights.failure_weight

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        raw_yaml = yaml.safe_load(f)

    raw_yaml["health_score"]["rul_weight"] = weights.rul_weight
    raw_yaml["health_score"]["anomaly_weight"] = weights.anomaly_weight
    raw_yaml["health_score"]["failure_weight"] = weights.failure_weight

    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        yaml.safe_dump(raw_yaml, f, sort_keys=False)

    return {
        "status": "success",
        "message": "Health score weights updated.",
        "health_score": cfg.health_score.model_dump(),
    }

