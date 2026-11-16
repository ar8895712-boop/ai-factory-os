# ==============================================================
# backend/models/sensor.py — Sensor table
# ==============================================================
"""
Describes a sensor channel attached to a machine.
Mapped from the C-MAPSS sensor columns (s1–s21) plus op settings.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class Sensor(Base):
    """Sensor channel metadata."""

    __tablename__ = "sensors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    machine_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("machines.id", ondelete="CASCADE"), nullable=False,
        index=True
    )
    name: Mapped[str] = mapped_column(String(32), nullable=False,
                                       comment="e.g. s2, s7, op_setting_1")
    description: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    unit: Mapped[Optional[str]] = mapped_column(String(32), nullable=True,
                                                 comment="e.g. °R, psia, rpm")
    min_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True,
                                                        comment="Expected operating min")
    max_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True,
                                                        comment="Expected operating max")
    is_active: Mapped[bool] = mapped_column(Integer, default=1,
                                             comment="0 = dropped constant sensor")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # ── Relationships ─────────────────────────────────────────────────
    machine: Mapped["Machine"] = relationship("Machine", back_populates="sensors")  # type: ignore[name-defined]
    readings: Mapped[list["Reading"]] = relationship(  # type: ignore[name-defined]
        "Reading", back_populates="sensor", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Sensor(id={self.id}, machine={self.machine_id}, name='{self.name}')>"

