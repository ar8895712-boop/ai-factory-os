# ==============================================================
# backend/routers/whatif.py — What-If Simulator REST Endpoints
# ==============================================================
"""
Exposes SimPy discrete-event simulation endpoints:
- POST /api/whatif/run        — Execute Baseline vs Scenario comparison
- GET  /api/whatif/templates  — Pre-built scenario templates
- GET  /api/whatif/history    — Historical simulation runs from DB
- GET  /api/whatif/{sim_id}   — Detailed result of a specific run
"""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException

from backend.database import SessionLocal
from backend.models.simulation_result import SimulationResult
from backend.schemas.whatif import (
    WhatIfComparisonResponse,
    WhatIfHistoryItemSchema,
    WhatIfRunRequest,
    WhatIfTemplateSchema,
)
from backend.simulation.whatif import (
    MachineScenarioParam,
    WhatIfComparisonResult,
    WhatIfRequestConfig,
    get_scenario_templates,
    get_whatif_service,
)

router = APIRouter(prefix="/api/whatif", tags=["What-If Simulator"])


def _result_to_response(res: WhatIfComparisonResult) -> WhatIfComparisonResponse:
    """Helper to convert dataclass into Pydantic response."""
    return WhatIfComparisonResponse(**asdict(res))


@router.post(
    "/run",
    response_model=WhatIfComparisonResponse,
    summary="Run Baseline vs Scenario What-If Simulation",
    description=(
        "Executes a SimPy discrete-event simulation over `sim_hours` (e.g. 168h = 1 week). "
        "Compares a Baseline (unmanaged degradation resulting in catastrophic failure) "
        "against the requested Scenario (proactive shutdown, load shifting, or speed throttling). "
        "Persists results into `simulation_results` table."
    ),
)
def run_whatif_simulation(req: WhatIfRunRequest) -> WhatIfComparisonResponse:
    service = get_whatif_service()

    # Convert request schemas into dataclass parameters
    machine_params: Dict[int, MachineScenarioParam] = {}
    for mid, p in req.machines.items():
        machine_params[int(mid)] = MachineScenarioParam(
            machine_id=int(mid),
            speed_factor=p.speed_factor,
            is_shutdown=p.is_shutdown,
            shutdown_duration_hours=p.shutdown_duration_hours,
            shutdown_start_hour=p.shutdown_start_hour,
            shifted_to_machine_id=p.shifted_to_machine_id,
        )

    config = WhatIfRequestConfig(
        scenario_name=req.scenario_name,
        description=req.description,
        sim_hours=req.sim_hours,
        machines=machine_params,
    )

    comparison = service.run_comparison(config)
    return _result_to_response(comparison)


@router.get(
    "/templates",
    response_model=List[WhatIfTemplateSchema],
    summary="List pre-configured scenario templates",
    description="Returns curated what-if scenarios (e.g., proactive maintenance, load shifting, speed throttle).",
)
def list_scenario_templates() -> List[WhatIfTemplateSchema]:
    templates = get_scenario_templates()
    return [WhatIfTemplateSchema(**t) for t in templates]


@router.get(
    "/history",
    response_model=List[WhatIfHistoryItemSchema],
    summary="List past what-if simulation runs",
    description="Fetches recent simulation records from SQLite `simulation_results` table.",
)
def list_simulation_history(limit: int = 20) -> List[WhatIfHistoryItemSchema]:
    db = SessionLocal()
    try:
        records = (
            db.query(SimulationResult)
            .order_by(SimulationResult.id.desc())
            .limit(min(limit, 100))
            .all()
        )
        history = []
        for r in records:
            params = {}
            if r.parameters:
                try:
                    params = json.loads(r.parameters)
                except Exception:
                    pass

            net_savings = None
            if r.results and r.baseline_results:
                try:
                    scen = json.loads(r.results)
                    base = json.loads(r.baseline_results)
                    net_savings = base.get("total_financial_cost_inr", 0) - scen.get("total_financial_cost_inr", 0)
                except Exception:
                    pass

            history.append(WhatIfHistoryItemSchema(
                id=r.id,
                scenario_name=r.scenario_name,
                description=r.description,
                timestamp=r.timestamp.isoformat() if r.timestamp else "",
                duration_seconds=r.duration_seconds,
                sim_hours=float(params.get("sim_hours", 168.0)),
                net_savings_inr=net_savings,
            ))
        return history
    finally:
        db.close()


@router.get(
    "/{sim_id}",
    summary="Get full details of a past simulation run",
    description="Returns the full JSON parameters and outputs for a specific run ID.",
)
def get_simulation_detail(sim_id: int) -> Dict[str, Any]:
    db = SessionLocal()
    try:
        record = db.query(SimulationResult).filter(SimulationResult.id == sim_id).first()
        if not record:
            raise HTTPException(status_code=404, detail=f"Simulation run {sim_id} not found")

        params = json.loads(record.parameters) if record.parameters else {}
        scenario_res = json.loads(record.results) if record.results else {}
        baseline_res = json.loads(record.baseline_results) if record.baseline_results else {}

        return {
            "id": record.id,
            "scenario_name": record.scenario_name,
            "description": record.description,
            "timestamp": record.timestamp.isoformat() if record.timestamp else "",
            "duration_seconds": record.duration_seconds,
            "parameters": params,
            "scenario": scenario_res,
            "baseline": baseline_res,
        }
    finally:
        db.close()

