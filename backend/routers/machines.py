# ==============================================================
# backend/routers/machines.py — Machine Management & Telemetry
# ==============================================================
from __future__ import annotations

import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.machine import Machine
from backend.models.prediction import Prediction
from backend.schemas.machine import (
    MachineBaseSchema,
    MachineDetailSchema,
    MachineHistoryPoint,
    MachineHistoryResponse,
    PredictionSummarySchema,
    SensorReadingSchema,
)
from backend.simulation.engine import get_simulation_engine

router = APIRouter(prefix="/api/machines", tags=["machines"])


@router.get("", response_model=List[MachineBaseSchema])
def list_machines(db: Session = Depends(get_db)):
    """Returns all 6 factory machines with current operational and health status."""
    engine = get_simulation_engine()
    machines = db.query(Machine).order_by(Machine.id).all()
    results = []
    for m in machines:
        m_state = engine.machines_state.get(m.id, {})
        pred = m_state.get("latest_prediction") or {}
        results.append(
            MachineBaseSchema(
                id=m.id,
                name=m.name,
                type=m.type,
                location=m.location,
                status=m_state.get("status", m.status),
                demo_engine_id=m.demo_engine_id,
                current_cycle=m_state.get("cycle", m.current_cycle),
                speed_factor=engine.speed_factor,
                health_score=pred.get("health_score", m.health_score or 100.0),
                rul_predicted=pred.get("rul_predicted", m.rul_predicted or 125.0),
                anomaly_score=pred.get("anomaly_score", m.anomaly_score or 0.05),
                failure_probability=pred.get("failure_probability", m.failure_probability or 0.02),
            )
        )
    return results


@router.get("/{machine_id}", response_model=MachineDetailSchema)
def get_machine_detail(machine_id: int, db: Session = Depends(get_db)):
    """Returns detailed machine telemetry, latest prediction, and active sensor readings."""
    engine = get_simulation_engine()
    if machine_id not in engine.machines_state:
        raise HTTPException(status_code=404, detail=f"Machine {machine_id} not found")

    m_state = engine.machines_state[machine_id]
    m = db.query(Machine).filter(Machine.id == machine_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Machine not in database")

    pred_data = m_state.get("latest_prediction") or {}
    readings_data = m_state.get("latest_readings") or {}

    readings_list = [
        SensorReadingSchema(sensor_name=k, value=round(v, 4))
        for k, v in readings_data.items()
    ]

    latest_pred = None
    if pred_data:
        latest_pred = PredictionSummarySchema(
            cycle=m_state["cycle"],
            health_score=pred_data.get("health_score", 100.0),
            rul_predicted=pred_data.get("rul_predicted", 125.0),
            anomaly_score=pred_data.get("anomaly_score", 0.05),
            failure_probability=pred_data.get("failure_probability", 0.02),
            alert_level=pred_data.get("alert_level", "normal"),
            model_name="xgboost_rul + isolation_forest",
            shap_explanation=pred_data.get("shap_explanation"),
        )

    return MachineDetailSchema(
        id=m.id,
        name=m.name,
        type=m.type,
        location=m.location,
        status=m_state["status"],
        demo_engine_id=m.demo_engine_id,
        current_cycle=m_state["cycle"],
        max_cycle=m_state["max_cycle"],
        speed_factor=engine.speed_factor,
        health_score=pred_data.get("health_score", m.health_score or 100.0),
        rul_predicted=pred_data.get("rul_predicted", m.rul_predicted or 125.0),
        anomaly_score=pred_data.get("anomaly_score", m.anomaly_score or 0.05),
        failure_probability=pred_data.get("failure_probability", m.failure_probability or 0.02),
        latest_readings=readings_list,
        latest_prediction=latest_pred,
    )


@router.get("/{machine_id}/history", response_model=MachineHistoryResponse)
def get_machine_history(machine_id: int, limit: int = 100, db: Session = Depends(get_db)):
    """Returns time-series history of health, RUL, and anomaly metrics for charts."""
    m = db.query(Machine).filter(Machine.id == machine_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Machine not found")

    predictions = (
        db.query(Prediction)
        .filter(Prediction.machine_id == machine_id)
        .order_by(Prediction.cycle.desc())
        .limit(limit)
        .all()
    )
    predictions.reverse()

    history_points = [
        MachineHistoryPoint(
            cycle=p.cycle,
            timestamp=p.timestamp,
            health_score=p.health_score,
            rul_predicted=p.rul_predicted,
            anomaly_score=p.anomaly_score,
            failure_probability=p.failure_probability,
        )
        for p in predictions
    ]

    return MachineHistoryResponse(
        machine_id=machine_id,
        name=m.name,
        history=history_points,
    )

