# ==============================================================
# backend/routers/simulation.py — Simulation Controls
# ==============================================================
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from backend.schemas.simulation import (
    SimulationControlResponse,
    SimulationJumpRequest,
    SimulationSpeedRequest,
    SimulationStatusSchema,
    SimulationStepRequest,
)
from backend.simulation.engine import get_simulation_engine

router = APIRouter(prefix="/api/simulation", tags=["simulation"])


@router.get("/status", response_model=SimulationStatusSchema)
def get_simulation_status():
    """Returns current live simulation execution status across all 6 machines."""
    engine = get_simulation_engine()
    return engine.get_status()


@router.post("/start", response_model=SimulationControlResponse)
def start_simulation():
    """Starts or resumes the real-time simulation background loop."""
    engine = get_simulation_engine()
    engine.start()
    return SimulationControlResponse(
        status="running",
        message="Simulation live replay started.",
        is_running=True,
        speed_factor=engine.speed_factor,
    )


@router.post("/pause", response_model=SimulationControlResponse)
def pause_simulation():
    """Pauses the simulation live replay."""
    engine = get_simulation_engine()
    engine.pause()
    return SimulationControlResponse(
        status="paused",
        message="Simulation live replay paused.",
        is_running=False,
        speed_factor=engine.speed_factor,
    )


@router.post("/reset", response_model=SimulationControlResponse)
def reset_simulation():
    """Resets all machines back to initial healthy baseline (cycle 1)."""
    engine = get_simulation_engine()
    engine.reset()
    return SimulationControlResponse(
        status="reset",
        message="All machines reset to cycle 1.",
        is_running=False,
        speed_factor=engine.speed_factor,
    )


@router.post("/speed", response_model=SimulationControlResponse)
def set_simulation_speed(req: SimulationSpeedRequest):
    """Adjusts replay speed factor (0.1x to 10.0x)."""
    engine = get_simulation_engine()
    engine.set_speed(req.speed_factor)
    return SimulationControlResponse(
        status="speed_updated",
        message=f"Speed set to {req.speed_factor:.1f}x.",
        is_running=engine.is_running,
        speed_factor=engine.speed_factor,
    )


@router.post("/jump", response_model=SimulationControlResponse)
def jump_degradation_cycle(req: SimulationJumpRequest):
    """
    'Start degradation at cycle X' feature:
    Directly seeks a machine to a specific degradation cycle to test late-life
    alerts, critical thresholds, and self-healing.
    """
    engine = get_simulation_engine()
    if req.machine_id not in engine.machines_state:
        raise HTTPException(status_code=404, detail=f"Machine {req.machine_id} not found")

    res = engine.jump_to_cycle(req.machine_id, req.target_cycle)
    return SimulationControlResponse(
        status="jumped",
        message=(
            f"Machine {req.machine_id} ({res['name']}) set to cycle {res['current_cycle']}. "
            f"Health: {res['health_score']}%, Status: {res['status']}."
        ),
        is_running=engine.is_running,
        speed_factor=engine.speed_factor,
    )


@router.post("/step")
async def step_simulation(req: SimulationStepRequest = SimulationStepRequest()):
    """Manually advances the simulation by N steps."""
    engine = get_simulation_engine()
    results = []
    for _ in range(req.steps):
        res = await engine.step_all()
        results = res
    return {
        "status": "stepped",
        "steps_advanced": req.steps,
        "machines": results,
    }

