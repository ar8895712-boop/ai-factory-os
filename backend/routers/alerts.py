# ==============================================================
# backend/routers/alerts.py — Incident & Alert Tracking
# ==============================================================
from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.incident import Incident
from backend.models.machine import Machine
from backend.schemas.alert import IncidentSchema, ResolveAlertRequest

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.get("", response_model=List[IncidentSchema])
def list_alerts(
    severity: Optional[str] = None,
    resolved: Optional[bool] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """Lists predictive alerts and incidents triggered across factory machines."""
    query = db.query(Incident).join(Machine, Incident.machine_id == Machine.id)
    if severity and isinstance(severity, str):
        query = query.filter(Incident.severity == severity)
    if resolved is not None and isinstance(resolved, bool):
        query = query.filter(Incident.resolved == resolved)

    incidents = query.order_by(Incident.timestamp.desc()).limit(limit).all()

    results = []
    for inc in incidents:
        results.append(
            IncidentSchema(
                id=inc.id,
                machine_id=inc.machine_id,
                machine_name=inc.machine.name if inc.machine else None,
                cycle=inc.cycle,
                timestamp=inc.timestamp,
                severity=inc.severity,
                category=inc.category,
                description=inc.description,
                health_score_at_time=inc.health_score_at_time,
                rul_at_time=inc.rul_at_time,
                anomaly_score_at_time=inc.anomaly_score_at_time,
                resolved=inc.resolved,
                resolved_at=inc.resolved_at,
                resolution_notes=inc.resolution_notes,
                action_taken=inc.action_taken,
            )
        )
    return results


@router.post("/{incident_id}/resolve", response_model=IncidentSchema)
def resolve_alert(
    incident_id: int,
    req: ResolveAlertRequest,
    db: Session = Depends(get_db),
):
    """Marks an incident as resolved with operator notes."""
    inc = db.query(Incident).filter(Incident.id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")

    inc.resolved = True
    inc.resolved_at = datetime.now()
    inc.resolution_notes = req.resolution_notes
    db.commit()
    db.refresh(inc)

    return IncidentSchema(
        id=inc.id,
        machine_id=inc.machine_id,
        machine_name=inc.machine.name if inc.machine else None,
        cycle=inc.cycle,
        timestamp=inc.timestamp,
        severity=inc.severity,
        category=inc.category,
        description=inc.description,
        health_score_at_time=inc.health_score_at_time,
        rul_at_time=inc.rul_at_time,
        anomaly_score_at_time=inc.anomaly_score_at_time,
        resolved=inc.resolved,
        resolved_at=inc.resolved_at,
        resolution_notes=inc.resolution_notes,
        action_taken=inc.action_taken,
    )
