# ==============================================================
# tests/test_business_impact.py — Unit tests for Phase 4
# ==============================================================
"""
Tests for:
1. BusinessImpactCalculator — all 4 cost formulas
2. SelfHealingEngine — action evaluation and minimum-cost selection
3. Formula invariants — costs must scale correctly with inputs
4. Edge cases — zero RUL, 100% health, 0% health

Run:
    python -m pytest tests/test_business_impact.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# ── Ensure project root is on sys.path ───────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.config import BusinessConfig
from backend.services.business_impact import BusinessImpactCalculator
from backend.services.self_healing import SelfHealingEngine


# ── Shared fixture: a BusinessConfig with known test values ───────────

@pytest.fixture
def test_biz_cfg() -> BusinessConfig:
    """
    Deterministic config for testing — no file I/O dependency.
    Values chosen to make formula assertions exact.
    """
    return BusinessConfig(
        currency="INR",
        currency_symbol="₹",
        loss_per_hour=100_000.0,
        planned_maintenance_cost_per_hour=20_000.0,
        energy_tariff_per_kwh=10.0,
        machine_power_kw=100.0,
        idle_power_fraction=0.10,
        delay_penalty_per_hour=50_000.0,
        daily_production_target=1000,
        avg_spare_part_cost=20_000.0,
        emergency_markup=2.0,
        technician_hourly_rate=1_000.0,
        overtime_multiplier=2.0,
    )


@pytest.fixture
def calc(monkeypatch, test_biz_cfg) -> BusinessImpactCalculator:
    """Calculator with _fresh_cfg() patched to return deterministic test config."""
    c = BusinessImpactCalculator()
    monkeypatch.setattr(c, "_fresh_cfg", lambda: test_biz_cfg)
    return c


@pytest.fixture
def healing(monkeypatch, test_biz_cfg) -> SelfHealingEngine:
    """SelfHealingEngine with _fresh_cfg patched."""
    from backend.config import SelfHealingAction, SelfHealingConfig
    test_healing_cfg = SelfHealingConfig(actions=[
        SelfHealingAction(
            name="reduce_speed",
            description="Reduce speed 20%",
            speed_reduction=0.20,
            rul_extension_factor=1.30,
        ),
        SelfHealingAction(
            name="shift_load",
            description="Shift load",
            min_target_health=70,
        ),
        SelfHealingAction(
            name="alert_operator",
            description="Alert operator",
            response_time_minutes=30,
        ),
        SelfHealingAction(
            name="schedule_maintenance",
            description="Schedule maintenance",
            lead_time_hours=4,
        ),
    ])
    e = SelfHealingEngine()
    monkeypatch.setattr(e, "_fresh_cfg", lambda: (test_biz_cfg, test_healing_cfg))
    monkeypatch.setattr(e, "_calc", BusinessImpactCalculator())
    return e


# ════════════════════════════════════════════════════════════════
# 1. DOWNTIME RISK TESTS
# ════════════════════════════════════════════════════════════════

class TestDowntimeRisk:

    def test_basic_formula(self, calc, test_biz_cfg):
        """
        P(fail)=0.5, RUL=10hrs, loss=₹100,000/hr
        → Expected cost = 0.5 × 10 × 100,000 = ₹500,000
        """
        result = calc.calc_downtime_risk(
            failure_probability=0.5,
            rul_predicted=10.0,
            cfg=test_biz_cfg,
        )
        assert result.expected_downtime_cost_inr == pytest.approx(500_000.0, rel=1e-3)

    def test_zero_failure_probability(self, calc, test_biz_cfg):
        """If P(fail)=0, downtime cost must be ₹0."""
        result = calc.calc_downtime_risk(0.0, 100.0, cfg=test_biz_cfg)
        assert result.expected_downtime_cost_inr == 0.0

    def test_low_rul_clamps_to_one(self, calc, test_biz_cfg):
        """RUL=0 is floored to 1 hour (machines at failure still have 1-hr downtime)."""
        result = calc.calc_downtime_risk(1.0, 0.0, cfg=test_biz_cfg)
        # 1.0 × max(1, 0) × 100000 → hours=1
        assert result.estimated_hours_to_failure == pytest.approx(1.0)

    def test_cost_scales_with_probability(self, calc, test_biz_cfg):
        """Higher failure probability → proportionally higher cost."""
        low  = calc.calc_downtime_risk(0.1, 20.0, cfg=test_biz_cfg)
        high = calc.calc_downtime_risk(0.9, 20.0, cfg=test_biz_cfg)
        assert high.expected_downtime_cost_inr == pytest.approx(
            9 * low.expected_downtime_cost_inr, rel=1e-3
        )

    def test_formula_string_populated(self, calc, test_biz_cfg):
        """Formula string must contain the key values for UI transparency."""
        result = calc.calc_downtime_risk(0.3, 15.0, cfg=test_biz_cfg)
        assert "0.300" in result.formula
        assert "15.0" in result.formula


# ════════════════════════════════════════════════════════════════
# 2. ENERGY WASTE TESTS
# ════════════════════════════════════════════════════════════════

class TestEnergyWaste:

    def test_healthy_machine_has_low_waste(self, calc, test_biz_cfg):
        """
        Health=100 → overhead_fraction = (100-100) × 0.003 = 0.0
        → daily_energy_waste = 0.
        """
        result = calc.calc_energy_waste(100.0, cfg=test_biz_cfg)
        assert result.daily_energy_waste_inr == pytest.approx(0.0, abs=0.1)

    def test_degraded_machine_has_higher_waste(self, calc, test_biz_cfg):
        """Health=50 should produce more energy waste than health=80."""
        waste_50 = calc.calc_energy_waste(50.0, cfg=test_biz_cfg)
        waste_80 = calc.calc_energy_waste(80.0, cfg=test_biz_cfg)
        assert waste_50.daily_energy_waste_inr > waste_80.daily_energy_waste_inr

    def test_zero_health_maximum_waste(self, calc, test_biz_cfg):
        """
        Health=0 → overhead = 100 × 0.003 = 0.30 (30% extra power)
        extra_kWh/day = 100kW × 0.30 × 16hrs = 480 kWh
        waste ₹/day   = 480 × ₹10 = ₹4,800
        """
        result = calc.calc_energy_waste(0.0, daily_operating_hours=16.0, cfg=test_biz_cfg)
        expected = 100.0 * 0.30 * 16.0 * 10.0  # 4800
        assert result.daily_energy_waste_inr == pytest.approx(expected, rel=1e-3)

    def test_health_clamped_between_0_and_100(self, calc, test_biz_cfg):
        """Out-of-range health values should not crash — clamp to [0, 100]."""
        r1 = calc.calc_energy_waste(-10.0, cfg=test_biz_cfg)
        r2 = calc.calc_energy_waste(150.0, cfg=test_biz_cfg)
        assert r1.daily_energy_waste_inr >= 0.0
        assert r2.daily_energy_waste_inr >= 0.0


# ════════════════════════════════════════════════════════════════
# 3. DELAY PENALTY TESTS
# ════════════════════════════════════════════════════════════════

class TestDelayPenalty:

    def test_full_health_zero_penalty(self, calc, test_biz_cfg):
        """Health=100 → no production deficit → no delay penalty."""
        result = calc.calc_delay_penalty(100.0, cfg=test_biz_cfg)
        assert result.daily_delay_penalty_inr == pytest.approx(0.0, abs=0.1)
        assert result.production_deficit_units == pytest.approx(0.0, abs=0.1)

    def test_zero_health_maximum_penalty(self, calc, test_biz_cfg):
        """
        Health=0 → actual_units=0, deficit=1000
        penalty = (1000/1000) × ₹50,000 × 24 = ₹1,200,000
        """
        result = calc.calc_delay_penalty(0.0, cfg=test_biz_cfg)
        expected = 1.0 * 50_000.0 * 24.0  # 1,200,000
        assert result.daily_delay_penalty_inr == pytest.approx(expected, rel=1e-3)

    def test_half_health_half_penalty(self, calc, test_biz_cfg):
        """Health=50 → deficit=500/1000=50% → penalty ≈ half of maximum."""
        full_penalty = calc.calc_delay_penalty(0.0, cfg=test_biz_cfg)
        half_penalty = calc.calc_delay_penalty(50.0, cfg=test_biz_cfg)
        assert half_penalty.daily_delay_penalty_inr == pytest.approx(
            0.5 * full_penalty.daily_delay_penalty_inr, rel=1e-3
        )

    def test_production_deficit_matches_health(self, calc, test_biz_cfg):
        """actual_production = target × (health/100)."""
        result = calc.calc_delay_penalty(70.0, cfg=test_biz_cfg)
        assert result.actual_production_units == pytest.approx(700.0, rel=1e-3)
        assert result.production_deficit_units == pytest.approx(300.0, rel=1e-3)


# ════════════════════════════════════════════════════════════════
# 4. MAINTENANCE SAVINGS TESTS
# ════════════════════════════════════════════════════════════════

class TestMaintenanceSavings:

    def test_emergency_always_more_expensive(self, calc, test_biz_cfg):
        """Emergency maintenance must always cost more than planned."""
        result = calc.calc_maintenance_savings(technician_hours=4.0, cfg=test_biz_cfg)
        assert result.emergency_maintenance_cost_inr > result.planned_maintenance_cost_inr

    def test_savings_always_positive(self, calc, test_biz_cfg):
        """savings_if_planned must be strictly positive (always save by planning)."""
        result = calc.calc_maintenance_savings(cfg=test_biz_cfg)
        assert result.savings_if_planned_inr > 0.0

    def test_planned_cost_formula(self, calc, test_biz_cfg):
        """
        Planned cost = spare_part + technician_hours × rate
        = ₹20,000 + 4 × ₹1,000 = ₹24,000
        """
        result = calc.calc_maintenance_savings(technician_hours=4.0, cfg=test_biz_cfg)
        assert result.planned_maintenance_cost_inr == pytest.approx(24_000.0, rel=1e-3)

    def test_emergency_cost_formula(self, calc, test_biz_cfg):
        """
        Emergency cost = spare_part × markup + technician_hours × rate × overtime
        = ₹20,000 × 2 + 4 × ₹1,000 × 2 = ₹40,000 + ₹8,000 = ₹48,000
        """
        result = calc.calc_maintenance_savings(technician_hours=4.0, cfg=test_biz_cfg)
        assert result.emergency_maintenance_cost_inr == pytest.approx(48_000.0, rel=1e-3)


# ════════════════════════════════════════════════════════════════
# 5. FULL REPORT TESTS
# ════════════════════════════════════════════════════════════════

class TestFullReport:

    def test_report_total_is_sum_of_components(self, calc, test_biz_cfg):
        """
        total_daily_exposure = downtime_risk + energy_waste/day + delay_penalty/day
        (Note: downtime_risk is a one-event cost, included for daily worst-case view)
        """
        monkeypatch_calc = BusinessImpactCalculator()
        # Patch fresh config
        monkeypatch_calc._fresh_cfg = lambda: test_biz_cfg

        report = monkeypatch_calc.generate_report(
            machine_id=1,
            machine_name="TestMachine",
            health_score=60.0,
            rul_predicted=30.0,
            failure_probability=0.3,
            anomaly_score=0.6,
            alert_level="warning",
        )

        expected_total = (
            report.downtime_risk.expected_downtime_cost_inr
            + report.energy_waste.daily_energy_waste_inr
            + report.delay_penalty.daily_delay_penalty_inr
        )
        assert report.total_daily_exposure_inr == pytest.approx(expected_total, rel=1e-3)

    def test_critical_alert_recommendation_mentions_maintenance(self, calc, test_biz_cfg):
        """CRITICAL alert level → recommendation must mention 'maintenance'."""
        c = BusinessImpactCalculator()
        c._fresh_cfg = lambda: test_biz_cfg
        report = c.generate_report(1, "CNC-01", 20.0, 10.0, 0.9, 0.95, "critical")
        assert "maintenance" in report.recommendation.lower()

    def test_healthy_machine_recommendation_says_healthy(self, calc, test_biz_cfg):
        """Health=95 → recommendation must say HEALTHY."""
        c = BusinessImpactCalculator()
        c._fresh_cfg = lambda: test_biz_cfg
        report = c.generate_report(1, "CNC-01", 95.0, 110.0, 0.02, 0.05, "normal")
        assert "healthy" in report.recommendation.lower()


# ════════════════════════════════════════════════════════════════
# 6. SELF-HEALING ENGINE TESTS
# ════════════════════════════════════════════════════════════════

class TestSelfHealingEngine:

    def test_always_selects_feasible_action(self, healing):
        """Engine must always select a feasible action."""
        decision = healing.evaluate(
            machine_id=1, machine_name="CNC-01",
            health_score=25.0, rul_predicted=10.0,
            failure_probability=0.8, anomaly_score=0.9,
            alert_level="critical",
            all_machine_states={
                1: {"health_score": 25.0, "name": "CNC-01"},
                2: {"health_score": 85.0, "name": "Pump-02"},
            },
        )
        assert decision.chosen_action is not None
        assert decision.chosen_cost_inr >= 0.0

    def test_shift_load_infeasible_when_no_healthy_peer(self, healing):
        """If all machines are degraded, shift_load must be marked infeasible."""
        all_states = {
            1: {"health_score": 20.0, "name": "CNC-01"},
            2: {"health_score": 10.0, "name": "Pump-02"},
            3: {"health_score": 15.0, "name": "Compressor-03"},
        }
        decision = healing.evaluate(
            machine_id=1, machine_name="CNC-01",
            health_score=20.0, rul_predicted=5.0,
            failure_probability=0.95, anomaly_score=0.95,
            alert_level="critical",
            all_machine_states=all_states,
        )
        # Verify shift_load is listed but infeasible
        shift_option = next(
            (o for o in decision.all_options if o.action_name == "shift_load"), None
        )
        assert shift_option is not None
        assert not shift_option.feasible

    def test_minimum_cost_selected(self, healing):
        """Chosen action must have the lowest cost among feasible options."""
        decision = healing.evaluate(
            machine_id=2, machine_name="Pump-02",
            health_score=55.0, rul_predicted=35.0,
            failure_probability=0.4, anomaly_score=0.7,
            alert_level="warning",
            all_machine_states={
                2: {"health_score": 55.0, "name": "Pump-02"},
                3: {"health_score": 90.0, "name": "Compressor-03"},
            },
        )
        feasible_costs = [
            o.expected_cost_inr for o in decision.all_options if o.feasible
        ]
        assert decision.chosen_cost_inr == min(feasible_costs)

    def test_decision_has_all_four_options(self, healing):
        """All 4 actions should be evaluated and present in all_options."""
        decision = healing.evaluate(
            machine_id=3, machine_name="Compressor-03",
            health_score=40.0, rul_predicted=20.0,
            failure_probability=0.6, anomaly_score=0.8,
            alert_level="warning",
            all_machine_states={3: {"health_score": 40.0, "name": "Compressor-03"}},
        )
        action_names = {o.action_name for o in decision.all_options}
        expected = {"reduce_speed", "shift_load", "alert_operator", "schedule_maintenance"}
        assert action_names == expected

    def test_decision_logged_to_history(self, healing):
        """Each evaluate() call must add an entry to the heal history."""
        from backend.services import self_healing as sh_module
        initial_len = len(sh_module._heal_history)
        healing.evaluate(
            machine_id=4, machine_name="Turbine-04",
            health_score=30.0, rul_predicted=15.0,
            failure_probability=0.7, anomaly_score=0.85,
            alert_level="critical",
            all_machine_states={4: {"health_score": 30.0, "name": "Turbine-04"}},
        )
        assert len(sh_module._heal_history) == initial_len + 1

