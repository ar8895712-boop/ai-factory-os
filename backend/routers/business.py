# ==============================================================
# backend/routers/business.py — Business Impact & Self-Healing API
# ==============================================================
"""
REST endpoints for Phase 4:

GET  /api/business/impact/{machine_id}   — Single machine ₹ impact report
GET  /api/business/fleet-summary         — All 6 machines aggregated
POST /api/business/self-heal/{machine_id}— Trigger self-healing rule engine
GET  /api/business/heal-history          — Audit log of past healing decisions

All numbers come from ML predictions (via simulation engine) + config.yaml.
The LLM (Phase 6) calls these endpoints via tools — it never computes numbers.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException

from backend.schemas.business import (
    BusinessImpactSchema,
    FleetSummarySchema,
    HealingDecisionSchema,
    HealingTriggerRequest,
)
from backend.services.business_impact import (
    BusinessImpactReport,
    generate_fleet_summary,
    get_business_calculator,
)
from backend.services.self_healing import (
    SelfHealingDecision,
    _decision_to_dict,
    get_healing_engine,
)
from backend.simulation.engine import get_simulation_engine

router = APIRouter(prefix="/api/business", tags=["Business Impact"])


# ── Helper: extract ML snapshot from live engine ─────────────────────

def _get_machine_snapshot(machine_id: int) -> Dict[str, Any]:
    """
    Pulls the latest ML prediction snapshot for a machine from the
    in-memory Digital Twin engine. Raises 404 if machine not found.
    """
    engine = get_simulation_engine()
    if machine_id not in engine.machines_state:
        raise HTTPException(
            status_code=404,
            detail=f"Machine {machine_id} not found. Valid IDs: {list(engine.machines_state.keys())}",
        )
    return engine._build_machine_summary(machine_id)


def _report_to_schema(report: BusinessImpactReport) -> BusinessImpactSchema:
    """Converts a BusinessImpactReport dataclass to a Pydantic schema."""
    from backend.schemas.business import (
        DowntimeRiskSchema,
        EnergyWasteSchema,
        DelayPenaltySchema,
        MaintenanceSavingsSchema,
    )
    return BusinessImpactSchema(
        machine_id=report.machine_id,
        machine_name=report.machine_name,
        health_score=report.health_score,
        rul_predicted=report.rul_predicted,
        failure_probability=report.failure_probability,
        anomaly_score=report.anomaly_score,
        downtime_risk=DowntimeRiskSchema(**report.downtime_risk.__dict__),
        energy_waste=EnergyWasteSchema(**report.energy_waste.__dict__),
        delay_penalty=DelayPenaltySchema(**report.delay_penalty.__dict__),
        maintenance_savings=MaintenanceSavingsSchema(**report.maintenance_savings.__dict__),
        total_daily_exposure_inr=report.total_daily_exposure_inr,
        recommendation=report.recommendation,
        alert_level=report.alert_level,
    )


# ── Endpoints ─────────────────────────────────────────────────────────

@router.get(
    "/impact/{machine_id}",
    response_model=BusinessImpactSchema,
    summary="Business impact report for one machine",
    description=(
        "Returns a full financial breakdown (downtime risk, energy waste, "
        "delay penalty, maintenance savings comparison) for a single machine "
        "based on its current ML prediction state. All values in ₹."
    ),
)
def get_machine_impact(machine_id: int) -> BusinessImpactSchema:
    """
    Generates a Business Impact Report for one machine.

    Flow:
    1. Fetch live ML prediction from Digital Twin engine
    2. Run all 4 cost formulas (pure arithmetic, no ML call)
    3. Return structured ₹ breakdown
    """
    snapshot = _get_machine_snapshot(machine_id)
    calc = get_business_calculator()

    report = calc.generate_report(
        machine_id=machine_id,
        machine_name=snapshot["name"],
        health_score=snapshot["health_score"],
        rul_predicted=snapshot["rul_predicted"],
        failure_probability=snapshot["failure_probability"],
        anomaly_score=snapshot["anomaly_score"],
        alert_level=snapshot["alert_level"],
    )
    return _report_to_schema(report)


@router.get(
    "/fleet-summary",
    response_model=FleetSummarySchema,
    summary="Aggregated fleet-wide financial impact",
    description=(
        "Aggregates business impact across all 6 machines. "
        "Useful for the CFO-level dashboard view: total daily ₹ exposure, "
        "which machines are critical, and worst performer."
    ),
)
def get_fleet_summary() -> FleetSummarySchema:
    """
    Fleet-wide financial roll-up.

    Runs the impact calculator for all 6 machines in a single call,
    then aggregates into a fleet summary with totals and rankings.
    """
    engine = get_simulation_engine()
    calc = get_business_calculator()

    reports: List[BusinessImpactReport] = []
    for mid in engine.machines_state:
        snapshot = engine._build_machine_summary(mid)
        report = calc.generate_report(
            machine_id=mid,
            machine_name=snapshot["name"],
            health_score=snapshot["health_score"],
            rul_predicted=snapshot["rul_predicted"],
            failure_probability=snapshot["failure_probability"],
            anomaly_score=snapshot["anomaly_score"],
            alert_level=snapshot["alert_level"],
        )
        reports.append(report)

    fleet = generate_fleet_summary(reports)
    per_machine_schemas = [_report_to_schema(r) for r in reports]

    return FleetSummarySchema(
        **fleet,
        per_machine=per_machine_schemas,
    )


@router.post(
    "/self-heal/{machine_id}",
    response_model=HealingDecisionSchema,
    summary="Trigger self-healing rule engine for a machine",
    description=(
        "Evaluates all 4 corrective actions (reduce_speed, shift_load, "
        "alert_operator, schedule_maintenance) with their ₹ cost estimates, "
        "selects the cheapest feasible action, and returns the full reasoning. "
        "Pass override_health to test hypothetical scenarios."
    ),
)
def trigger_self_healing(
    machine_id: int,
    request: HealingTriggerRequest = None,
) -> HealingDecisionSchema:
    """
    Self-Healing Rule Engine trigger.

    For each action:
    - Estimates the expected ₹ cost given current machine state
    - Marks infeasible actions (e.g., shift_load with no healthy peers)
    - Selects minimum-cost feasible action
    - Logs decision to heal_history

    The override_health parameter allows what-if testing:
    POST /api/business/self-heal/3 {"machine_id": 3, "override_health": 25}
    simulates what happens if Machine 3 drops to health=25.
    """
    engine = get_simulation_engine()
    if machine_id not in engine.machines_state:
        raise HTTPException(status_code=404, detail=f"Machine {machine_id} not found")

    snapshot = engine._build_machine_summary(machine_id)

    # Allow override for demo/what-if testing
    health_score = snapshot["health_score"]
    if request and request.override_health is not None:
        health_score = request.override_health

    # Build all_machine_states for shift_load feasibility check
    all_states: Dict[int, Dict] = {}
    for mid in engine.machines_state:
        s = engine._build_machine_summary(mid)
        all_states[mid] = {
            "health_score": s["health_score"],
            "name": s["name"],
        }

    healing = get_healing_engine()
    decision = healing.evaluate(
        machine_id=machine_id,
        machine_name=snapshot["name"],
        health_score=health_score,
        rul_predicted=snapshot["rul_predicted"],
        failure_probability=snapshot["failure_probability"],
        anomaly_score=snapshot["anomaly_score"],
        alert_level=snapshot["alert_level"],
        all_machine_states=all_states,
    )

    return HealingDecisionSchema(**_decision_to_dict(decision))


@router.get(
    "/heal-history",
    summary="Audit log of past self-healing decisions",
    description=(
        "Returns the most recent self-healing decisions across all machines. "
        "Each record includes the trigger state, all evaluated options with ₹ "
        "costs, and the chosen action with reasoning."
    ),
)
def get_heal_history(limit: int = 20) -> List[Dict]:
    """Returns recent self-healing decision log (newest first)."""
    healing = get_healing_engine()
    return healing.get_history(limit=min(limit, 100))


@router.get(
    "/config-preview",
    summary="Preview current business config values used in calculations",
    description="Returns the exact config.yaml business section being used right now.",
)
def get_config_preview() -> Dict:
    """Shows which ₹ assumptions are active — useful for debugging & demo."""
    import yaml
    from pathlib import Path
    cfg_path = Path(__file__).resolve().parent.parent.parent / "config.yaml"
    with open(cfg_path, "r") as f:
        raw = yaml.safe_load(f)
    return raw.get("business", {})

