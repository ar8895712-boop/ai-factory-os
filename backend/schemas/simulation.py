# ==============================================================
# backend/schemas/simulation.py — Simulation Control Schemas
# ==============================================================
from __future__ import annotations

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class SimulationStatusSchema(BaseModel):
    is_running: bool
    speed_factor: float
    total_machines: int
    active_machines: int
    machines_summary: List[Dict[str, object]] = Field(default_factory=list)


class SimulationSpeedRequest(BaseModel):
    speed_factor: float = Field(ge=0.1, le=10.0, default=1.0)


class SimulationJumpRequest(BaseModel):
    machine_id: int
    target_cycle: int = Field(ge=1, description="Jump to specific degradation cycle")


class SimulationStepRequest(BaseModel):
    steps: int = Field(default=1, ge=1, le=50)


class SimulationControlResponse(BaseModel):
    status: str
    message: str
    is_running: bool
    speed_factor: float

