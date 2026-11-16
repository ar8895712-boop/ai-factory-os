# ==============================================================
# backend/schemas/machine.py — Machine & Telemetry Schemas
# ==============================================================
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SensorReadingSchema(BaseModel):
    sensor_name: str
    value: float
    description: Optional[str] = None
    unit: Optional[str] = None


class PredictionSummarySchema(BaseModel):
    cycle: int
    health_score: float
    rul_predicted: float
    anomaly_score: float
    failure_probability: float
    alert_level: str
    model_name: Optional[str] = None
    shap_explanation: Optional[Dict[str, Any]] = None


class MachineBaseSchema(BaseModel):
    id: int
    name: str
    type: str
    location: str
    status: str
    demo_engine_id: Optional[int] = None
    current_cycle: int
    speed_factor: float
    health_score: Optional[float] = None
    rul_predicted: Optional[float] = None
    anomaly_score: Optional[float] = None
    failure_probability: Optional[float] = None


class MachineDetailSchema(MachineBaseSchema):
    max_cycle: int = 200
    latest_readings: List[SensorReadingSchema] = Field(default_factory=list)
    latest_prediction: Optional[PredictionSummarySchema] = None


class MachineHistoryPoint(BaseModel):
    cycle: int
    timestamp: Optional[datetime] = None
    health_score: Optional[float] = None
    rul_predicted: Optional[float] = None
    anomaly_score: Optional[float] = None
    failure_probability: Optional[float] = None
    sensors: Dict[str, float] = Field(default_factory=dict)


class MachineHistoryResponse(BaseModel):
    machine_id: int
    name: str
    history: List[MachineHistoryPoint]

