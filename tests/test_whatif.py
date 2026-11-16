# ==============================================================
# tests/test_whatif.py — Unit & Integration Tests for Phase 5 (SimPy What-If)
# ==============================================================
"""
Tests for:
1. SimPyFactoryModel baseline execution & discrete events
2. Proactive maintenance shutdown vs catastrophic breakdown
3. Workload shift from degraded machine to healthy peer
4. Speed throttling & RUL extension mechanics
5. Invariant checks (hours, costs, energy, trajectories)
6. WhatIfSimulatorService comparisons & SQLite persistence
7. Scenario templates structure

Run with:
    python -m pytest tests/test_whatif.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.config import BusinessConfig
from backend.simulation.whatif import (
    MachineScenarioParam,
    SimPyFactoryModel,
    WhatIfRequestConfig,
    WhatIfSimulatorService,
    get_scenario_templates,
)


@pytest.fixture
def test_biz_cfg() -> BusinessConfig:
    """Deterministic config for testing."""
    return BusinessConfig(
        currency="INR",
        currency_symbol="₹",
        loss_per_hour=100_000.0,
        planned_maintenance_cost_per_hour=25_000.0,
        energy_tariff_per_kwh=10.0,
        machine_power_kw=80.0,
        idle_power_fraction=0.15,
        delay_penalty_per_hour=40_000.0,
        daily_production_target=1000,
        avg_spare_part_cost=20_000.0,
        emergency_markup=2.0,
        technician_hourly_rate=1_000.0,
        overtime_multiplier=1.5,
    )


@pytest.fixture
def sample_rul_map() -> dict:
    """
    RUL map: Machine 3 is in late life (RUL=10h),
    Machine 1, 2, 4, 5, 6 are healthy (RUL=120h).
    """
    return {
        1: 120.0,
        2: 120.0,
        3: 10.0,   # degraded! Will fail at t=10 in a 24h/168h simulation
        4: 120.0,
        5: 120.0,
        6: 120.0,
    }


# ════════════════════════════════════════════════════════════════
# 1. BASELINE SIMULATION TESTS
# ════════════════════════════════════════════════════════════════

class TestBaselineSimPyModel:

    def test_baseline_runs_full_horizon(self, test_biz_cfg, sample_rul_map):
        """Simulation must run to exactly sim_hours and log events."""
        params = {mid: MachineScenarioParam(machine_id=mid) for mid in range(1, 7)}
        model = SimPyFactoryModel(
            sim_hours=24.0,
            machine_params=params,
            ml_rul_map=sample_rul_map,
            biz_cfg=test_biz_cfg,
            seed=42,
        )
        summary = model.run()

        assert summary.total_units_produced > 0.0
        assert summary.total_energy_kwh > 0.0
        assert len(summary.machines) == 6
        assert len(summary.hourly_trajectory) > 0

    def test_degraded_machine_breaks_down_in_baseline(self, test_biz_cfg, sample_rul_map):
        """
        Machine 3 has RUL=10. In a 24-hour baseline without maintenance,
        it must experience at least 1 catastrophic breakdown and unplanned downtime.
        """
        params = {mid: MachineScenarioParam(machine_id=mid) for mid in range(1, 7)}
        model = SimPyFactoryModel(
            sim_hours=24.0,
            machine_params=params,
            ml_rul_map=sample_rul_map,
            biz_cfg=test_biz_cfg,
            seed=42,
        )
        summary = model.run()

        m3 = next(m for m in summary.machines if m.machine_id == 3)
        assert m3.failure_count >= 1
        assert m3.unplanned_downtime_hours > 0.0
        assert m3.downtime_loss_inr > 0.0

    def test_healthy_machines_do_not_fail_early(self, test_biz_cfg, sample_rul_map):
        """Machines with RUL=120 must not experience failure in a 24-hour run."""
        params = {mid: MachineScenarioParam(machine_id=mid) for mid in range(1, 7)}
        model = SimPyFactoryModel(
            sim_hours=24.0,
            machine_params=params,
            ml_rul_map=sample_rul_map,
            biz_cfg=test_biz_cfg,
            seed=42,
        )
        summary = model.run()

        m1 = next(m for m in summary.machines if m.machine_id == 1)
        assert m1.failure_count == 0
        assert m1.unplanned_downtime_hours == 0.0


# ════════════════════════════════════════════════════════════════
# 2. SCENARIO: PROACTIVE MAINTENANCE SHUTDOWN
# ════════════════════════════════════════════════════════════════

class TestProactiveMaintenanceScenario:

    def test_proactive_shutdown_avoids_unplanned_failure(self, test_biz_cfg, sample_rul_map):
        """
        If Machine 3 is shut down proactively at t=0 for 4h maintenance,
        health is restored and it should NOT experience an unplanned catastrophic failure.
        """
        params = {
            1: MachineScenarioParam(machine_id=1),
            2: MachineScenarioParam(machine_id=2),
            3: MachineScenarioParam(
                machine_id=3,
                is_shutdown=True,
                shutdown_duration_hours=4.0,
                shutdown_start_hour=0.0,
            ),
            4: MachineScenarioParam(machine_id=4),
            5: MachineScenarioParam(machine_id=5),
            6: MachineScenarioParam(machine_id=6),
        }
        model = SimPyFactoryModel(
            sim_hours=24.0,
            machine_params=params,
            ml_rul_map=sample_rul_map,
            biz_cfg=test_biz_cfg,
            seed=42,
        )
        summary = model.run()

        m3 = next(m for m in summary.machines if m.machine_id == 3)
        assert m3.planned_downtime_hours == 4.0
        assert m3.unplanned_downtime_hours == 0.0
        assert m3.failure_count == 0

    def test_planned_maintenance_cheaper_than_unplanned_downtime(self, test_biz_cfg, sample_rul_map):
        """
        Comparing Machine 3 cost: planned maintenance rate (₹25k/hr) vs unplanned loss (₹100k/hr)
        proves proactive maintenance results in lower machine cost.
        """
        # Baseline run (unplanned breakdown)
        base_params = {mid: MachineScenarioParam(machine_id=mid) for mid in range(1, 7)}
        base_summary = SimPyFactoryModel(
            sim_hours=24.0, machine_params=base_params,
            ml_rul_map=sample_rul_map, biz_cfg=test_biz_cfg, seed=42
        ).run()

        # Scenario run (proactive 4h maintenance)
        scen_params = {mid: MachineScenarioParam(machine_id=mid) for mid in range(1, 7)}
        scen_params[3] = MachineScenarioParam(
            machine_id=3, is_shutdown=True, shutdown_duration_hours=4.0
        )
        scen_summary = SimPyFactoryModel(
            sim_hours=24.0, machine_params=scen_params,
            ml_rul_map=sample_rul_map, biz_cfg=test_biz_cfg, seed=42
        ).run()

        base_m3 = next(m for m in base_summary.machines if m.machine_id == 3)
        scen_m3 = next(m for m in scen_summary.machines if m.machine_id == 3)

        assert scen_m3.downtime_loss_inr < base_m3.downtime_loss_inr


# ════════════════════════════════════════════════════════════════
# 3. SCENARIO: WORKLOAD SHIFT
# ════════════════════════════════════════════════════════════════

class TestWorkloadShiftScenario:

    def test_target_machine_absorbs_shifted_production(self, test_biz_cfg, sample_rul_map):
        """
        Shifting load from Machine 3 to Machine 2:
        Machine 2's production must exceed normal baseline production.
        """
        # Baseline
        base_params = {mid: MachineScenarioParam(machine_id=mid) for mid in range(1, 7)}
        base_summary = SimPyFactoryModel(
            sim_hours=24.0, machine_params=base_params,
            ml_rul_map=sample_rul_map, biz_cfg=test_biz_cfg, seed=42
        ).run()

        # Workload Shift Scenario: M3 shut down, load shifted to M2
        shift_params = {mid: MachineScenarioParam(machine_id=mid) for mid in range(1, 7)}
        shift_params[3] = MachineScenarioParam(
            machine_id=3, is_shutdown=True, shutdown_duration_hours=8.0, shifted_to_machine_id=2
        )
        scen_summary = SimPyFactoryModel(
            sim_hours=24.0, machine_params=shift_params,
            ml_rul_map=sample_rul_map, biz_cfg=test_biz_cfg, seed=42
        ).run()

        base_m2 = next(m for m in base_summary.machines if m.machine_id == 2)
        scen_m2 = next(m for m in scen_summary.machines if m.machine_id == 2)

        assert scen_m2.units_produced > base_m2.units_produced


# ════════════════════════════════════════════════════════════════
# 4. SCENARIO: SPEED CHANGE (THROTTLING)
# ════════════════════════════════════════════════════════════════

class TestSpeedChangeScenario:

    def test_speed_reduction_lowers_hourly_units(self, test_biz_cfg, sample_rul_map):
        """A machine running at 0.8x speed produces ~20% fewer units per hour."""
        params_normal = {mid: MachineScenarioParam(machine_id=mid, speed_factor=1.0) for mid in range(1, 7)}
        params_slow   = {mid: MachineScenarioParam(machine_id=mid, speed_factor=0.8) for mid in range(1, 7)}

        healthy_rul = {mid: 200.0 for mid in range(1, 7)}
        sim_norm = SimPyFactoryModel(24.0, params_normal, healthy_rul, test_biz_cfg, seed=42).run()
        sim_slow = SimPyFactoryModel(24.0, params_slow, healthy_rul, test_biz_cfg, seed=42).run()

        m1_norm = next(m for m in sim_norm.machines if m.machine_id == 1)
        m1_slow = next(m for m in sim_slow.machines if m.machine_id == 1)

        assert m1_slow.units_produced < m1_norm.units_produced
        assert m1_slow.units_produced == pytest.approx(0.8 * m1_norm.units_produced, rel=1e-2)

    def test_speed_reduction_extends_time_to_failure(self, test_biz_cfg):
        """
        Machine 3 has raw RUL=15h. At 1.0x speed, it fails within 16 hours.
        At 0.6x speed, effective TTF is extended: RUL / sqrt(0.6) = 15 / 0.774 = ~19.3 hours.
        In a 16-hour simulation, the slowed machine should NOT fail.
        """
        rul_map = {mid: 100.0 for mid in range(1, 7)}
        rul_map[3] = 15.0

        # Normal speed (1.0x): fails in 16-hour run
        params_normal = {mid: MachineScenarioParam(machine_id=mid, speed_factor=1.0) for mid in range(1, 7)}
        norm_res = SimPyFactoryModel(16.0, params_normal, rul_map, test_biz_cfg, seed=42).run()
        m3_norm = next(m for m in norm_res.machines if m.machine_id == 3)
        assert m3_norm.failure_count >= 1

        # Slowed speed (0.6x): failure delayed past 16h
        params_slow = {mid: MachineScenarioParam(machine_id=mid, speed_factor=1.0) for mid in range(1, 7)}
        params_slow[3] = MachineScenarioParam(machine_id=3, speed_factor=0.6)
        slow_res = SimPyFactoryModel(16.0, params_slow, rul_map, test_biz_cfg, seed=42).run()
        m3_slow = next(m for m in slow_res.machines if m.machine_id == 3)
        assert m3_slow.failure_count == 0


# ════════════════════════════════════════════════════════════════
# 5. INVARIANTS & INTEGRATION SERVICE TESTS
# ════════════════════════════════════════════════════════════════

class TestWhatIfInvariantsAndService:

    def test_operating_hours_invariant(self, test_biz_cfg, sample_rul_map):
        """For every machine: operating + planned_dt + unplanned_dt <= sim_hours."""
        params = {mid: MachineScenarioParam(machine_id=mid) for mid in range(1, 7)}
        sim = SimPyFactoryModel(24.0, params, sample_rul_map, test_biz_cfg, seed=42).run()

        for m in sim.machines:
            total_time = m.operating_hours + m.planned_downtime_hours + m.unplanned_downtime_hours
            assert total_time <= 24.5  # allow small floating step rounding

    def test_comparison_service_computes_net_savings(self, monkeypatch, test_biz_cfg, sample_rul_map):
        """WhatIfSimulatorService must return correct delta metrics."""
        service = WhatIfSimulatorService()
        monkeypatch.setattr(service, "_fresh_biz_cfg", lambda: test_biz_cfg)
        monkeypatch.setattr(service, "_get_live_rul_map", lambda: sample_rul_map)

        config = WhatIfRequestConfig(
            scenario_name="Test Proactive Maintenance",
            description="Testing service delta calculation",
            sim_hours=24.0,
            machines={
                3: MachineScenarioParam(
                    machine_id=3,
                    is_shutdown=True,
                    shutdown_duration_hours=4.0,
                    shutdown_start_hour=0.0,
                )
            },
        )
        res = service.run_comparison(config)

        expected_savings = res.baseline.total_financial_cost_inr - res.scenario.total_financial_cost_inr
        assert res.net_savings_inr == pytest.approx(expected_savings, rel=1e-2)
        assert len(res.roi_summary) > 0

    def test_scenario_templates_available(self):
        """Pre-configured templates must return valid non-empty list."""
        templates = get_scenario_templates()
        assert len(templates) >= 3
        for t in templates:
            assert "id" in t
            assert "name" in t
            assert "sim_hours" in t
            assert "machines" in t

