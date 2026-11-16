# ==============================================================
# backend/models/reading.py — Sensor readings table
# ==============================================================
"""
One row = one sensor value at one cycle for one machine.
This is the highest-volume table (thousands of rows per machine).
Indexed on (machine_id, cycle) for fast time-range queries.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class Reading(Base):
    """Individual sensor reading at a given cycle."""

    __tablename__ = "readings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    machine_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("machines.id", ondelete="CASCADE"), nullable=False
    )
    sensor_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("sensors.id", ondelete="CASCADE"), nullable=False
    )
    cycle: Mapped[int] = mapped_column(Integer, nullable=False,
                                        comment="C-MAPSS cycle number")
    value: Mapped[float] = mapped_column(Float, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
        comment="Wall-clock time of this reading (simulated)"
    )

    # ── Relationships ─────────────────────────────────────────────────
    machine: Mapped["Machine"] = relationship("Machine", back_populates="readings")  # type: ignore[name-defined]
    sensor: Mapped["Sensor"] = relationship("Sensor", back_populates="readings")    # type: ignore[name-defined]

    # ── Composite index for fast lookups ──────────────────────────────
    __table_args__ = (
        Index("ix_readings_machine_cycle", "machine_id", "cycle"),
    )

    def __repr__(self) -> str:
        return (f"<Reading(machine={self.machine_id}, sensor={self.sensor_id}, "
                f"cycle={self.cycle}, value={self.value:.4f})>")

