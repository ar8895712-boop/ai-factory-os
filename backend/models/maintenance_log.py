# ==============================================================
# backend/models/maintenance_log.py — Maintenance history table
# ==============================================================
"""
Logs every maintenance action (scheduled or triggered by self-healing).
Links to the incident that triggered it, if any.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class MaintenanceLog(Base):
    """Record of a maintenance action performed on a machine."""

    __tablename__ = "maintenance_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    machine_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("machines.id", ondelete="CASCADE"), nullable=False,
        index=True
    )
    incident_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("incidents.id", ondelete="SET NULL"), nullable=True,
        comment="Incident that triggered this maintenance (null if scheduled)"
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # ── Action details ────────────────────────────────────────────────
    action: Mapped[str] = mapped_column(
        String(64), nullable=False,
        comment="e.g. replace_bearing, reduce_speed, full_overhaul"
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    duration_hours: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="How long the maintenance took"
    )
    cost: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="Cost in INR"
    )
    performed_by: Mapped[Optional[str]] = mapped_column(
        String(128), nullable=True, comment="Technician name or 'auto'"
    )

    # ── Outcome ───────────────────────────────────────────────────────
    health_before: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    health_after: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ── Relationships ─────────────────────────────────────────────────
    machine: Mapped["Machine"] = relationship("Machine", back_populates="maintenance_logs")  # type: ignore[name-defined]
    incident: Mapped[Optional["Incident"]] = relationship(  # type: ignore[name-defined]
        "Incident", back_populates="maintenance_logs"
    )

    def __repr__(self) -> str:
        return (f"<MaintenanceLog(id={self.id}, machine={self.machine_id}, "
                f"action='{self.action}')>")

