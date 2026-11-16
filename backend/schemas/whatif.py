# ==============================================================
# backend/schemas/whatif.py — What-If Simulator Pydantic Schemas
# ==============================================================
"""
Typed schemas for What-If scenario execution, comparisons,
and historical run queries.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class MachineScenarioParamSchema(BaseModel):
    machine_id: int
    speed_factor: float = Field(default=1.0, ge=0.2, le=2.0)
    is_shutdown: bool = False
    shutdown_duration_hours: float = Field(default=4.0, ge=0.5, le=48.0)
    shutdown_start_hour: float = Field(default=0.0, ge=0.0)
    shifted_to_machine_id: Optional[int] = None


class WhatIfRunRequest(BaseModel):
    scenario_name: str = Field(default="Custom What-If Scenario")
    description: str = Field(default="What-if simulation run")
    sim_hours: float = Field(default=168.0, ge=6.0, le=720.0, description="Horizon in hours (default 168h = 1 week)")
    machines: Dict[int, MachineScenarioParamSchema] = Field(
        default_factory=dict,
        description="Map of machine_id -> scenario overrides"
    )


class MachineSimMetricsSchema(BaseModel):
    machine_id: int
    machine_name: str
    units_produced: float
    operating_hours: float
    idle_hours: float
    unplanned_downtime_hours: float
    planned_downtime_hours: float
    failure_count: int
    energy_kwh: float
    energy_cost_inr: float
    downtime_loss_inr: float
    maintenance_cost_inr: float
    total_cost_inr: float


class SimulationRunSummarySchema(BaseModel):
    total_units_produced: float
    target_units: float
    production_deficit_units: float
    total_operating_hours: float
    total_unplanned_downtime_hours: float
    total_planned_downtime_hours: float
    total_failures: int
    total_energy_kwh: float
    total_energy_cost_inr: float
    total_downtime_loss_inr: float
    total_maintenance_cost_inr: float
    total_delay_penalty_inr: float
    total_financial_cost_inr: float
    machines: List[MachineSimMetricsSchema]
    hourly_trajectory: List[Dict[str, float]] = Field(default_factory=list)


class WhatIfComparisonResponse(BaseModel):
    scenario_name: str
    description: str
    sim_hours: float
    timestamp: str
    baseline: SimulationRunSummarySchema
    scenario: SimulationRunSummarySchema
    net_savings_inr: float
    production_delta_units: float
    downtime_avoided_hours: float
    energy_saved_kwh: float
    roi_summary: str


class WhatIfTemplateSchema(BaseModel):
    id: str
    name: str
    description: str
    sim_hours: float
    machines: Dict[int, MachineScenarioParamSchema]


class WhatIfHistoryItemSchema(BaseModel):
    id: int
    scenario_name: str
    description: Optional[str]
    timestamp: str
    duration_seconds: Optional[float]
    sim_hours: float
    net_savings_inr: Optional[float]

