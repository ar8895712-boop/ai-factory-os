# ==============================================================
# backend/models/machine.py — Machine table
# ==============================================================
"""
Represents a physical (simulated) machine on the factory floor.
Each machine maps to one C-MAPSS demo-holdout engine trajectory.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class Machine(Base):
    """Factory machine entity."""

    __tablename__ = "machines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False,
                                       comment="Human-readable name, e.g. CNC-01")
    type: Mapped[str] = mapped_column(String(64), nullable=False,
                                       comment="Machine category, e.g. CNC Milling")
    location: Mapped[str] = mapped_column(String(128), nullable=False,
                                           comment="Physical location on floor")
    status: Mapped[str] = mapped_column(String(32), default="idle",
                                         comment="idle | running | warning | critical | maintenance")

    # Link to C-MAPSS demo engine
    demo_engine_id: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True,
        comment="Engine ID from DEMO-HOLDOUT split (never trained on)"
    )
    current_cycle: Mapped[int] = mapped_column(Integer, default=0,
                                                comment="Current replay cycle")
    speed_factor: Mapped[float] = mapped_column(Float, default=1.0,
                                                 comment="Replay speed multiplier")

    # Health metrics (updated each cycle by the digital twin)
    health_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True,
                                                           comment="Composite 0-100")
    rul_predicted: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    anomaly_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    failure_probability: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # ── Relationships (loaded lazily by default) ─────────────────────
    sensors: Mapped[list["Sensor"]] = relationship(           # type: ignore[name-defined]
        "Sensor", back_populates="machine", cascade="all, delete-orphan"
    )
    readings: Mapped[list["Reading"]] = relationship(         # type: ignore[name-defined]
        "Reading", back_populates="machine", cascade="all, delete-orphan"
    )
    predictions: Mapped[list["Prediction"]] = relationship(   # type: ignore[name-defined]
        "Prediction", back_populates="machine", cascade="all, delete-orphan"
    )
    incidents: Mapped[list["Incident"]] = relationship(       # type: ignore[name-defined]
        "Incident", back_populates="machine", cascade="all, delete-orphan"
    )
    maintenance_logs: Mapped[list["MaintenanceLog"]] = relationship(  # type: ignore[name-defined]
        "MaintenanceLog", back_populates="machine", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Machine(id={self.id}, name='{self.name}', status='{self.status}')>"

