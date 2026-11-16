# ==============================================================
# backend/models/prediction.py — ML prediction results table
# ==============================================================
"""
Stores every ML prediction made for a machine at a given cycle:
RUL estimate, failure probability, anomaly score, and the
composite health score.  Also stores SHAP explanation as JSON.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class Prediction(Base):
    """ML prediction record for one machine at one cycle."""

    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    machine_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("machines.id", ondelete="CASCADE"), nullable=False
    )
    cycle: Mapped[int] = mapped_column(Integer, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # ── Model outputs ─────────────────────────────────────────────────
    rul_predicted: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="Remaining Useful Life in cycles"
    )
    failure_probability: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="Probability of imminent failure (0–1)"
    )
    anomaly_score: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="Anomaly score from autoencoder / IForest"
    )
    health_score: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="Weighted composite health (0–100)"
    )

    # ── Metadata ──────────────────────────────────────────────────────
    model_name: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True, comment="Which model produced this, e.g. xgboost_rul"
    )
    model_version: Mapped[Optional[str]] = mapped_column(
        String(32), nullable=True, comment="Model version or run ID"
    )
    shap_explanation: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="JSON-serialised SHAP values for this prediction"
    )
    alert_level: Mapped[Optional[str]] = mapped_column(
        String(16), nullable=True, comment="none | warning | critical"
    )

    # ── Relationships ─────────────────────────────────────────────────
    machine: Mapped["Machine"] = relationship("Machine", back_populates="predictions")  # type: ignore[name-defined]

    # ── Indexes ───────────────────────────────────────────────────────
    __table_args__ = (
        Index("ix_predictions_machine_cycle", "machine_id", "cycle"),
        Index("ix_predictions_alert", "alert_level"),
    )

    def __repr__(self) -> str:
        return (f"<Prediction(machine={self.machine_id}, cycle={self.cycle}, "
                f"health={self.health_score}, rul={self.rul_predicted})>")

