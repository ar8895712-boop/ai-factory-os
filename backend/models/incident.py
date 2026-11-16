# ==============================================================
# backend/models/incident.py — Incident / alert history table
# ==============================================================
"""
Records every alert or anomaly event.  The `embedding` column
stores the sentence-transformer vector (as JSON array) for
FAISS similarity search in the Factory Memory module.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean, DateTime, Float, ForeignKey, Index,
    Integer, String, Text, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class Incident(Base):
    """Recorded incident or alert event."""

    __tablename__ = "incidents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    machine_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("machines.id", ondelete="CASCADE"), nullable=False,
        index=True
    )
    cycle: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # ── Event details ─────────────────────────────────────────────────
    severity: Mapped[str] = mapped_column(
        String(16), nullable=False, default="warning",
        comment="info | warning | critical | failure"
    )
    category: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True,
        comment="e.g. anomaly, rul_low, failure_predicted, sensor_drift"
    )
    description: Mapped[str] = mapped_column(
        Text, nullable=False,
        comment="Human-readable description of the incident"
    )

    # ── ML context at time of incident ────────────────────────────────
    health_score_at_time: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    rul_at_time: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    anomaly_score_at_time: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # ── Resolution ────────────────────────────────────────────────────
    resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ── Embedding for FAISS similarity search ─────────────────────────
    embedding: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="JSON array of floats from sentence-transformers"
    )

    # ── Self-healing action taken ─────────────────────────────────────
    action_taken: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True,
        comment="Self-healing action, e.g. reduce_speed, shift_load"
    )

    # ── Relationships ─────────────────────────────────────────────────
    machine: Mapped["Machine"] = relationship("Machine", back_populates="incidents")  # type: ignore[name-defined]
    maintenance_logs: Mapped[list["MaintenanceLog"]] = relationship(  # type: ignore[name-defined]
        "MaintenanceLog", back_populates="incident", cascade="all, delete-orphan"
    )

    # ── Indexes ───────────────────────────────────────────────────────
    __table_args__ = (
        Index("ix_incidents_severity", "severity"),
        Index("ix_incidents_timestamp", "timestamp"),
    )

    def __repr__(self) -> str:
        return (f"<Incident(id={self.id}, machine={self.machine_id}, "
                f"severity='{self.severity}')>")

