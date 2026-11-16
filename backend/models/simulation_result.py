# ==============================================================
# backend/models/simulation_result.py — What-If simulation results
# ==============================================================
"""
Stores the inputs (scenario parameters) and outputs (production,
cost, energy) of each what-if simulation run.  `parameters` and
`results` are stored as JSON text for flexibility.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class SimulationResult(Base):
    """Record of one what-if simulation run."""

    __tablename__ = "simulation_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    scenario_name: Mapped[str] = mapped_column(
        String(128), nullable=False,
        comment="e.g. 'shutdown_machine_3', 'speed_reduction_all'"
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # ── Inputs ────────────────────────────────────────────────────────
    parameters: Mapped[str] = mapped_column(
        Text, nullable=False,
        comment="JSON dict of scenario parameters"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="Human-readable scenario description"
    )

    # ── Outputs ───────────────────────────────────────────────────────
    results: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="JSON dict of simulation output metrics"
    )
    baseline_results: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="JSON dict of baseline (no-change) metrics for comparison"
    )
    duration_seconds: Mapped[Optional[float]] = mapped_column(
        nullable=True, comment="How long the simulation took to run"
    )

    # ── Who ran it ────────────────────────────────────────────────────
    created_by: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # ── Relationships ─────────────────────────────────────────────────
    user: Mapped[Optional["User"]] = relationship(  # type: ignore[name-defined]
        "User", back_populates="simulation_results"
    )

    def __repr__(self) -> str:
        return (f"<SimulationResult(id={self.id}, "
                f"scenario='{self.scenario_name}')>")

