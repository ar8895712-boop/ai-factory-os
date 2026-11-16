# ==============================================================
# backend/schemas/business.py — Business Impact Pydantic Schemas
# ==============================================================
"""
Typed request/response models for the Business Impact and
Self-Healing endpoints. All ₹ values are plain floats — the
LLM formats them in Phase 6.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ── Business Impact Schemas ───────────────────────────────────────────

class DowntimeRiskSchema(BaseModel):
    failure_probability: float
    estimated_hours_to_failure: float
    loss_per_hour_inr: float
    expected_downtime_cost_inr: float
    formula: str


class EnergyWasteSchema(BaseModel):
    nominal_power_kw: float
    degradation_overhead_fraction: float
    daily_operating_hours: float
    extra_kwh_per_day: float
    tariff_per_kwh_inr: float
    daily_energy_waste_inr: float
    formula: str


class DelayPenaltySchema(BaseModel):
    health_score: float
    daily_target_units: int
    actual_production_units: float
    production_deficit_units: float
    penalty_per_hour_inr: float
    daily_delay_penalty_inr: float
    formula: str


class MaintenanceSavingsSchema(BaseModel):
    avg_spare_part_cost_inr: float
    emergency_markup: float
    technician_hours: float
    technician_rate_inr: float
    overtime_multiplier: float
    planned_maintenance_cost_inr: float
    emergency_maintenance_cost_inr: float
    savings_if_planned_inr: float
    formula: str


class BusinessImpactSchema(BaseModel):
    machine_id: int
    machine_name: str
    health_score: float
    rul_predicted: float
    failure_probability: float
    anomaly_score: float
    downtime_risk: DowntimeRiskSchema
    energy_waste: EnergyWasteSchema
    delay_penalty: DelayPenaltySchema
    maintenance_savings: MaintenanceSavingsSchema
    total_daily_exposure_inr: float
    recommendation: str
    alert_level: str


class FleetSummarySchema(BaseModel):
    fleet_total_daily_exposure_inr: float
    fleet_total_daily_exposure_monthly_inr: float
    breakdown: Dict[str, float]
    critical_machines: List[str]
    warning_machines: List[str]
    worst_machine: Optional[str]
    worst_machine_exposure_inr: float
    machines_count: int
    per_machine: List[BusinessImpactSchema]


# ── Self-Healing Schemas ──────────────────────────────────────────────

class ActionOptionSchema(BaseModel):
    action_name: str
    description: str
    feasible: bool
    expected_cost_inr: float
    cost_breakdown: Dict[str, float]
    reasoning: str


class HealingDecisionSchema(BaseModel):
    machine_id: int
    machine_name: str
    trigger_health: float
    trigger_rul: float
    trigger_failure_prob: float
    alert_level: str
    all_options: List[ActionOptionSchema]
    chosen_action: str
    chosen_cost_inr: float
    chosen_reasoning: str
    timestamp: str
    executed: bool
    execution_message: str


class HealingTriggerRequest(BaseModel):
    """
    Manual trigger for self-healing evaluation (for testing / demo).
    If not provided, the engine uses live simulation state.
    """
    machine_id: int
    override_health: Optional[float] = Field(
        default=None,
        description="Override health score (0-100) for what-if testing",
        ge=0.0,
        le=100.0,
    )

