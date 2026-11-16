# ==============================================================
# backend/services/business_impact.py — Business Impact Calculator
# ==============================================================
"""
Converts ML predictions (RUL, health score, failure probability,
anomaly score) into Indian Rupee costs using assumptions from config.yaml.

Design principle: This module contains ONLY pure functions and math.
The LLM (Phase 6) will explain the outputs — it never computes here.

Key formulas (all transparent, explained for viva):
─────────────────────────────────────────────────
1. Downtime Risk (₹) = P(failure) × hours_to_failure × loss_per_hour
2. Energy Waste (₹) = degradation_overhead_kWh × tariff_per_kWh
3. Delay Penalty (₹) = production_deficit_units / rate_per_hour × penalty_per_hour
4. Emergency vs Planned Maintenance Savings (₹) = emergency_cost − planned_cost
5. Total Daily Exposure (₹) = sum of all above, scaled to 24 hrs
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from backend.config import get_settings


# ── Data Classes (typed return objects) ─────────────────────────────

@dataclass
class DowntimeRiskBreakdown:
    """Unplanned downtime exposure in ₹."""
    failure_probability: float          # 0.0–1.0
    estimated_hours_to_failure: float   # derived from RUL (1 cycle ≈ 1 operational hour)
    loss_per_hour_inr: float            # from config
    expected_downtime_cost_inr: float   # = P(fail) × hours × loss_per_hour
    formula: str = ""

    def __post_init__(self):
        self.formula = (
            f"P(fail)={self.failure_probability:.3f} × "
            f"hrs_to_fail={self.estimated_hours_to_failure:.1f} × "
            f"₹{self.loss_per_hour_inr:,.0f}/hr"
            f" = ₹{self.expected_downtime_cost_inr:,.0f}"
        )


@dataclass
class EnergyWasteBreakdown:
    """Excess energy consumption due to degradation in ₹."""
    nominal_power_kw: float             # healthy machine power draw
    degradation_overhead_fraction: float  # extra % power due to wear
    daily_operating_hours: float
    extra_kwh_per_day: float            # = power_kw × overhead_frac × daily_hrs
    tariff_per_kwh_inr: float
    daily_energy_waste_inr: float       # = extra_kwh × tariff
    formula: str = ""

    def __post_init__(self):
        self.formula = (
            f"overhead={self.degradation_overhead_fraction*100:.1f}% × "
            f"{self.nominal_power_kw}kW × {self.daily_operating_hours}hrs × "
            f"₹{self.tariff_per_kwh_inr}/kWh"
            f" = ₹{self.daily_energy_waste_inr:,.0f}/day"
        )


@dataclass
class DelayPenaltyBreakdown:
    """Production delay penalty due to reduced throughput in ₹."""
    health_score: float                 # 0–100
    daily_target_units: int             # from config
    actual_production_units: float      # health_score/100 × target
    production_deficit_units: float     # target − actual
    penalty_per_hour_inr: float
    daily_delay_penalty_inr: float      # prorated to 24 hrs
    formula: str = ""

    def __post_init__(self):
        self.formula = (
            f"deficit={self.production_deficit_units:.0f}units/day × "
            f"(₹{self.penalty_per_hour_inr:,.0f}/hr × 24hrs / {self.daily_target_units}units)"
            f" = ₹{self.daily_delay_penalty_inr:,.0f}/day"
        )


@dataclass
class MaintenanceSavingsBreakdown:
    """Cost comparison: emergency repair vs. planned maintenance in ₹."""
    avg_spare_part_cost_inr: float
    emergency_markup: float
    technician_hours: float
    technician_rate_inr: float
    overtime_multiplier: float
    planned_maintenance_cost_inr: float    # scheduled
    emergency_maintenance_cost_inr: float  # reactive
    savings_if_planned_inr: float          # positive = save by planning
    formula: str = ""

    def __post_init__(self):
        self.formula = (
            f"Emergency=₹{self.emergency_maintenance_cost_inr:,.0f} "
            f"vs Planned=₹{self.planned_maintenance_cost_inr:,.0f} "
            f"→ Savings=₹{self.savings_if_planned_inr:,.0f}"
        )


@dataclass
class BusinessImpactReport:
    """Full business impact report for one machine at a snapshot in time."""
    machine_id: int
    machine_name: str
    health_score: float
    rul_predicted: float
    failure_probability: float
    anomaly_score: float

    downtime_risk: DowntimeRiskBreakdown
    energy_waste: EnergyWasteBreakdown
    delay_penalty: DelayPenaltyBreakdown
    maintenance_savings: MaintenanceSavingsBreakdown

    total_daily_exposure_inr: float    # sum of all daily costs
    recommendation: str               # plain language suggestion
    alert_level: str                  # "normal" | "warning" | "critical"


# ── Core Calculation Engine ──────────────────────────────────────────

class BusinessImpactCalculator:
    """
    Converts ML prediction outputs into financial metrics (₹).

    All formulas are deterministic given config.yaml + ML outputs.
    No randomness, no model calls here — pure arithmetic.
    """

    # Rough degradation overhead: a machine at 50% health uses ~15% more power
    _DEGRADATION_POWER_OVERHEAD_SLOPE: float = 0.003  # extra fraction per 1% health lost

    def __init__(self):
        # NOTE: config is reloaded fresh each time to pick up UI edits
        # (config_router writes to config.yaml, so we re-read instead of caching)
        pass

    def _fresh_cfg(self):
        """
        Re-reads config.yaml each call so live UI edits (PUT /api/config/business)
        are reflected immediately without server restart.
        """
        import yaml
        from pathlib import Path
        cfg_path = Path(__file__).resolve().parent.parent.parent / "config.yaml"
        with open(cfg_path, "r") as f:
            raw = yaml.safe_load(f)
        from backend.config import BusinessConfig
        return BusinessConfig(**raw.get("business", {}))

    # ── 1. Downtime Risk ─────────────────────────────────────────────

    def calc_downtime_risk(
        self,
        failure_probability: float,
        rul_predicted: float,
        cfg=None,
    ) -> DowntimeRiskBreakdown:
        """
        Expected monetary loss if failure occurs.

        Formula:
            estimated_hours = RUL × 1 hr/cycle   (1 cycle ≈ 1 operational hour)
            downtime_cost = P(fail) × hours_to_failure × loss_per_hour
        """
        if cfg is None:
            cfg = self._fresh_cfg()

        # 1 C-MAPSS cycle ≈ 1 operational hour (conservative assumption)
        hours_to_failure = max(1.0, float(rul_predicted))
        cost = failure_probability * hours_to_failure * cfg.loss_per_hour

        return DowntimeRiskBreakdown(
            failure_probability=failure_probability,
            estimated_hours_to_failure=hours_to_failure,
            loss_per_hour_inr=cfg.loss_per_hour,
            expected_downtime_cost_inr=round(cost, 2),
        )

    # ── 2. Energy Waste ──────────────────────────────────────────────

    def calc_energy_waste(
        self,
        health_score: float,
        daily_operating_hours: float = 16.0,
        cfg=None,
    ) -> EnergyWasteBreakdown:
        """
        Extra energy consumed due to mechanical degradation.

        A healthy machine (health=100) has 0% overhead.
        A machine at health=50 has ~15% extra power draw (worn seals,
        increased friction, reduced efficiency).

        Formula:
            overhead_fraction = (100 - health_score) × slope
            extra_kWh/day     = power_kw × overhead_fraction × daily_hrs
            waste_₹/day       = extra_kWh × tariff
        """
        if cfg is None:
            cfg = self._fresh_cfg()

        health_score = max(0.0, min(100.0, health_score))
        overhead_fraction = (100.0 - health_score) * self._DEGRADATION_POWER_OVERHEAD_SLOPE
        extra_kwh = cfg.machine_power_kw * overhead_fraction * daily_operating_hours
        daily_waste = extra_kwh * cfg.energy_tariff_per_kwh

        return EnergyWasteBreakdown(
            nominal_power_kw=cfg.machine_power_kw,
            degradation_overhead_fraction=overhead_fraction,
            daily_operating_hours=daily_operating_hours,
            extra_kwh_per_day=round(extra_kwh, 2),
            tariff_per_kwh_inr=cfg.energy_tariff_per_kwh,
            daily_energy_waste_inr=round(daily_waste, 2),
        )

    # ── 3. Delivery Delay Penalty ────────────────────────────────────

    def calc_delay_penalty(
        self,
        health_score: float,
        cfg=None,
    ) -> DelayPenaltyBreakdown:
        """
        Production throughput reduction due to degraded machine → SLA penalty.

        Formula:
            actual_units/day = target × (health_score / 100)
            deficit_units    = target - actual_units
            penalty/day      = deficit / target × penalty_per_hour × 24
        """
        if cfg is None:
            cfg = self._fresh_cfg()

        health_score = max(0.0, min(100.0, health_score))
        actual = cfg.daily_production_target * (health_score / 100.0)
        deficit = cfg.daily_production_target - actual

        # Scale penalty: full penalty at 0 health, 0 penalty at 100 health
        penalty_rate = cfg.daily_production_target  # units/day at target rate
        daily_penalty = (deficit / max(1, penalty_rate)) * cfg.delay_penalty_per_hour * 24.0

        return DelayPenaltyBreakdown(
            health_score=health_score,
            daily_target_units=cfg.daily_production_target,
            actual_production_units=round(actual, 1),
            production_deficit_units=round(deficit, 1),
            penalty_per_hour_inr=cfg.delay_penalty_per_hour,
            daily_delay_penalty_inr=round(daily_penalty, 2),
        )

    # ── 4. Maintenance Savings ───────────────────────────────────────

    def calc_maintenance_savings(
        self,
        technician_hours: float = 4.0,
        cfg=None,
    ) -> MaintenanceSavingsBreakdown:
        """
        Compares emergency (reactive) vs. planned (preventive) maintenance cost.

        Planned Maintenance Cost:
            = spare_parts + technician_hours × rate/hr

        Emergency Maintenance Cost:
            = spare_parts × emergency_markup + technician_hours × rate × overtime_multiplier

        Savings = Emergency − Planned  (always positive: acting early always saves money)
        """
        if cfg is None:
            cfg = self._fresh_cfg()

        planned_parts = cfg.avg_spare_part_cost
        planned_labour = technician_hours * cfg.technician_hourly_rate
        planned_total = planned_parts + planned_labour

        emergency_parts = cfg.avg_spare_part_cost * cfg.emergency_markup
        emergency_labour = technician_hours * cfg.technician_hourly_rate * cfg.overtime_multiplier
        emergency_total = emergency_parts + emergency_labour

        savings = emergency_total - planned_total

        return MaintenanceSavingsBreakdown(
            avg_spare_part_cost_inr=cfg.avg_spare_part_cost,
            emergency_markup=cfg.emergency_markup,
            technician_hours=technician_hours,
            technician_rate_inr=cfg.technician_hourly_rate,
            overtime_multiplier=cfg.overtime_multiplier,
            planned_maintenance_cost_inr=round(planned_total, 2),
            emergency_maintenance_cost_inr=round(emergency_total, 2),
            savings_if_planned_inr=round(savings, 2),
        )

    # ── 5. Full Report ───────────────────────────────────────────────

    def generate_report(
        self,
        machine_id: int,
        machine_name: str,
        health_score: float,
        rul_predicted: float,
        failure_probability: float,
        anomaly_score: float,
        alert_level: str = "normal",
    ) -> BusinessImpactReport:
        """
        Generates a complete financial impact report for one machine.
        All four sub-calculations are run with a single fresh config read.
        """
        cfg = self._fresh_cfg()

        downtime = self.calc_downtime_risk(failure_probability, rul_predicted, cfg)
        energy   = self.calc_energy_waste(health_score, cfg=cfg)
        delay    = self.calc_delay_penalty(health_score, cfg)
        maint    = self.calc_maintenance_savings(cfg=cfg)

        # Total daily exposure (downtime is per-event, scale by 24hrs for comparable daily view)
        # We treat downtime_cost as "if it fails today" single-event cost
        total_daily = (
            downtime.expected_downtime_cost_inr
            + energy.daily_energy_waste_inr
            + delay.daily_delay_penalty_inr
        )

        # Recommendation text (rule-based, LLM explains in Phase 6)
        if alert_level == "critical" or health_score < 30:
            rec = (
                f"⚠️ CRITICAL: Immediate maintenance required. "
                f"Daily exposure ₹{total_daily:,.0f}. "
                f"Save ₹{maint.savings_if_planned_inr:,.0f} by acting now vs emergency repair."
            )
        elif alert_level == "warning" or health_score < 60:
            rec = (
                f"⚡ WARNING: Schedule maintenance within 48 hours. "
                f"Current daily exposure ₹{total_daily:,.0f}."
            )
        else:
            rec = (
                f"✅ HEALTHY: Machine operating normally. "
                f"Monitor energy waste ₹{energy.daily_energy_waste_inr:,.0f}/day."
            )

        return BusinessImpactReport(
            machine_id=machine_id,
            machine_name=machine_name,
            health_score=health_score,
            rul_predicted=rul_predicted,
            failure_probability=failure_probability,
            anomaly_score=anomaly_score,
            downtime_risk=downtime,
            energy_waste=energy,
            delay_penalty=delay,
            maintenance_savings=maint,
            total_daily_exposure_inr=round(total_daily, 2),
            recommendation=rec,
            alert_level=alert_level,
        )


# ── Fleet Summary ────────────────────────────────────────────────────

def generate_fleet_summary(reports: List[BusinessImpactReport]) -> Dict[str, Any]:
    """
    Aggregates individual machine impact reports into a factory-wide
    financial dashboard summary.
    """
    total_exposure = sum(r.total_daily_exposure_inr for r in reports)
    total_energy_waste = sum(r.energy_waste.daily_energy_waste_inr for r in reports)
    total_delay_penalty = sum(r.delay_penalty.daily_delay_penalty_inr for r in reports)
    total_downtime_risk = sum(r.downtime_risk.expected_downtime_cost_inr for r in reports)

    critical_machines = [r.machine_name for r in reports if r.alert_level == "critical"]
    warning_machines  = [r.machine_name for r in reports if r.alert_level == "warning"]

    worst_machine = max(reports, key=lambda r: r.total_daily_exposure_inr, default=None)

    return {
        "fleet_total_daily_exposure_inr": round(total_exposure, 2),
        "fleet_total_daily_exposure_monthly_inr": round(total_exposure * 30, 2),
        "breakdown": {
            "downtime_risk_inr": round(total_downtime_risk, 2),
            "energy_waste_inr": round(total_energy_waste, 2),
            "delay_penalty_inr": round(total_delay_penalty, 2),
        },
        "critical_machines": critical_machines,
        "warning_machines": warning_machines,
        "worst_machine": worst_machine.machine_name if worst_machine else None,
        "worst_machine_exposure_inr": worst_machine.total_daily_exposure_inr if worst_machine else 0,
        "machines_count": len(reports),
    }


# ── Singleton instance ────────────────────────────────────────────────
_calculator_instance: Optional[BusinessImpactCalculator] = None


def get_business_calculator() -> BusinessImpactCalculator:
    global _calculator_instance
    if _calculator_instance is None:
        _calculator_instance = BusinessImpactCalculator()
    return _calculator_instance

