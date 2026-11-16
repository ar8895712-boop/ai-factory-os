# ==============================================================
# backend/schemas/alert.py — Incident & Alert Schemas
# ==============================================================
from __future__ import annotations

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class IncidentSchema(BaseModel):
    id: int
    machine_id: int
    machine_name: Optional[str] = None
    cycle: Optional[int] = None
    timestamp: datetime
    severity: str
    category: Optional[str] = None
    description: str
    health_score_at_time: Optional[float] = None
    rul_at_time: Optional[float] = None
    anomaly_score_at_time: Optional[float] = None
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    action_taken: Optional[str] = None


class ResolveAlertRequest(BaseModel):
    resolution_notes: str

