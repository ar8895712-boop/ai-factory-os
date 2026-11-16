# ==============================================================
# backend/simulation/whatif.py — SimPy Discrete-Event What-If Simulator
# ==============================================================
"""
SimPy-powered discrete-event simulation of the 6-machine production line.
Simulates production, degradation, machine failures, and energy over
a configurable horizon (default: 168 hours = 1 week).

Key features:
1. Reuses live ML RUL predictions as time-to-failure (TTF) inputs.
2. Supports Scenarios:
   - machine_shutdown (proactive maintenance vs catastrophic failure)
   - workload_shift (rerouting jobs from degraded to healthy peer)
   - speed_change (throttle speed to extend RUL vs higher output)
   - custom_scenario (combination of above)
3. Outputs full Baseline vs Scenario comparison:
   - Production throughput (units) & SLA deficit
   - Downtime hours (planned vs unplanned)
   - Energy consumption (kWh & ₹ tariff)
   - Financial breakdown in Indian Rupees (₹)
   - Hour-by-hour trajectory curves for Recharts
"""

from __future__ import annotations

import json
import math
import random
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import simpy
import yaml

from backend.config import get_settings
from backend.database import SessionLocal
from backend.models.simulation_result import SimulationResult


# ── Data classes for Scenario inputs & outputs ────────────────────────

@dataclass
class MachineScenarioParam:
    """Per-machine scenario parameters."""
    machine_id: int
    speed_factor: float = 1.0          # 0.5 to 1.5 multiplier on production rate
    is_shutdown: bool = False          # if True, proactively stopped for maintenance
    shutdown_duration_hours: float = 4.0  # duration of planned maintenance stoppage
    shutdown_start_hour: float = 0.0   # when maintenance begins in sim timeline
    shifted_to_machine_id: Optional[int] = None  # target machine if load shifted


@dataclass
class WhatIfRequestConfig:
    """Full scenario configuration requested by user."""
    scenario_name: str
    description: str = ""
    sim_hours: float = 168.0           # default 1 week
    machines: Dict[int, MachineScenarioParam] = field(default_factory=dict)


@dataclass
class MachineSimMetrics:
    """Metrics recorded for one machine at simulation conclusion."""
    machine_id: int
    machine_name: str
    units_produced: float
    operating_hours: float
    idle_hours: float
    unplanned_downtime_hours: float
    planned_downtime_hours: float
    failure_count: int
    energy_kwh: float
    energy_cost_inr: float
    downtime_loss_inr: float
    maintenance_cost_inr: float
    total_cost_inr: float


@dataclass
class SimulationRunSummary:
    """Aggregated output summary for a single run (Baseline or Scenario)."""
    total_units_produced: float
    target_units: float
    production_deficit_units: float
    total_operating_hours: float
    total_unplanned_downtime_hours: float
    total_planned_downtime_hours: float
    total_failures: int
    total_energy_kwh: float
    total_energy_cost_inr: float
    total_downtime_loss_inr: float
    total_maintenance_cost_inr: float
    total_delay_penalty_inr: float
    total_financial_cost_inr: float
    machines: List[MachineSimMetrics]
    # Hourly trajectory data for plotting: list of { "hour": h, "production": p, "cost": c, "energy": e }
    hourly_trajectory: List[Dict[str, float]]


@dataclass
class WhatIfComparisonResult:
    """Side-by-side comparison between Baseline and Scenario."""
    scenario_name: str
    description: str
    sim_hours: float
    timestamp: str
    baseline: SimulationRunSummary
    scenario: SimulationRunSummary
    # Key deltas (Scenario − Baseline: negative cost delta = savings)
    net_savings_inr: float             # baseline_cost − scenario_cost
    production_delta_units: float      # scenario_units − baseline_units
    downtime_avoided_hours: float      # baseline_unplanned_dt − scenario_unplanned_dt
    energy_saved_kwh: float            # baseline_energy − scenario_energy
    roi_summary: str                   # Human-readable conclusion


# ── SimPy Factory Model ───────────────────────────────────────────────

class SimPyFactoryModel:
    """
    Simulates manufacturing floor of 6 machines over `sim_hours`.
    Driven by discrete events:
      - Hourly production cycle
      - Scheduled planned maintenance shutdown
      - Stochastic or ML-RUL-triggered failure breakdowns
    """

    def __init__(
        self,
        sim_hours: float,
        machine_params: Dict[int, MachineScenarioParam],
        ml_rul_map: Dict[int, float],
        biz_cfg: Any,
        seed: int = 42,
    ) -> None:
        self.sim_hours = float(sim_hours)
        self.machine_params = machine_params
        self.ml_rul_map = ml_rul_map
        self.biz = biz_cfg
        self.seed = seed
        self.rng = random.Random(seed)

        self.env = simpy.Environment()

        # Pre-seed settings
        cfg = get_settings()
        self.nominal_prod_rate = cfg.simulator.production_rate_per_hour  # 42 units/hr
        self.base_power_kw = self.biz.machine_power_kw                    # 75 kW
        self.energy_tariff = self.biz.energy_tariff_per_kwh               # 8.50 ₹/kWh
        self.loss_per_hour = self.biz.loss_per_hour                       # 150,000 ₹/hr
        self.target_units = (self.sim_hours / 24.0) * self.biz.daily_production_target * len(cfg.machines)

        # Machine tracking structures
        self.machine_records: Dict[int, Dict[str, Any]] = {}
        for m in cfg.machines:
            self.machine_records[m.id] = {
                "name": m.name,
                "units": 0.0,
                "operating_hours": 0.0,
                "idle_hours": 0.0,
                "unplanned_dt_hours": 0.0,
                "planned_dt_hours": 0.0,
                "failures": 0,
                "energy_kwh": 0.0,
                "is_down": False,
                "down_type": None,  # "planned" | "unplanned"
            }

        # Global hourly log
        self.hourly_log: List[Dict[str, float]] = []

    def _get_machine_speed(self, machine_id: int) -> float:
        param = self.machine_params.get(machine_id)
        return param.speed_factor if param else 1.0

    def _setup_processes(self) -> None:
        """Schedules simulation processes for each machine."""
        for machine_id in self.machine_records:
            self.env.process(self._machine_process(machine_id))

        # Hourly factory monitor process
        self.env.process(self._hourly_monitor_process())

    def _machine_process(self, machine_id: int):
        """
        Life-cycle process for a single machine:
        - Runs hour by hour producing units and drawing power.
        - Triggers planned maintenance if scheduled.
        - Triggers unplanned breakdown when operating time reaches ML RUL.
        """
        rec = self.machine_records[machine_id]
        param = self.machine_params.get(machine_id)

        # Failure time derived from ML RUL:
        # If speed < 1.0, RUL is extended: effective_rul = rul / (speed^0.5)
        # If speed > 1.0, RUL decreases faster.
        raw_rul = self.ml_rul_map.get(machine_id, 125.0)
        speed = self._get_machine_speed(machine_id)
        effective_ttf = max(1.0, raw_rul / max(0.2, math.sqrt(speed)))

        # Planned maintenance config
        is_planned_shutdown = param.is_shutdown if param else False
        planned_start = param.shutdown_start_hour if param else 0.0
        planned_duration = param.shutdown_duration_hours if param else 4.0

        current_time = 0.0
        has_done_planned_maint = False
        hours_operated = 0.0

        while self.env.now < self.sim_hours:
            now = self.env.now
            step_duration = 1.0  # 1 hour simulation step

            # ── 1. Check if planned shutdown should start ─────────────
            if is_planned_shutdown and not has_done_planned_maint and now >= planned_start:
                rec["is_down"] = True
                rec["down_type"] = "planned"
                rec["planned_dt_hours"] += planned_duration
                # During planned maintenance, machine is off/standby (small idle power)
                rec["energy_kwh"] += self.base_power_kw * self.biz.idle_power_fraction * planned_duration
                # Yield until maintenance completes
                yield self.env.timeout(planned_duration)
                has_done_planned_maint = True
                rec["is_down"] = False
                rec["down_type"] = None
                # Planned maintenance restores machine health → resets time-to-failure!
                effective_ttf += 150.0
                continue

            # ── 2. Check if unplanned failure breakdown occurs ─────────
            # Breakdown occurs when hours operated reaches effective_ttf
            if hours_operated >= effective_ttf and not rec["is_down"]:
                # Catastrophic failure event!
                rec["is_down"] = True
                rec["down_type"] = "unplanned"
                rec["failures"] += 1
                repair_time = float(get_settings().simulator.repair_time_hours)  # 4 hrs
                rec["unplanned_dt_hours"] += repair_time
                rec["energy_kwh"] += self.base_power_kw * self.biz.idle_power_fraction * repair_time

                yield self.env.timeout(repair_time)
                # After emergency repair, machine resumes
                rec["is_down"] = False
                rec["down_type"] = None
                hours_operated = 0.0
                # Next failure happens after MTBF baseline
                effective_ttf = float(get_settings().simulator.machine_mtbf_hours) * self.rng.uniform(0.7, 1.3)
                continue

            # ── 3. Normal 1-hour operation step ───────────────────────
            # Check if this machine is absorbing shifted load from a peer
            extra_load_multiplier = 1.0
            for peer_id, p_param in self.machine_params.items():
                if p_param.shifted_to_machine_id == machine_id and p_param.is_shutdown:
                    extra_load_multiplier += 0.8  # absorbs 80% of peer's capacity

            effective_speed = speed * extra_load_multiplier
            units = self.nominal_prod_rate * effective_speed * step_duration
            rec["units"] += units
            rec["operating_hours"] += step_duration
            hours_operated += step_duration

            # Power draw: base_power * speed^1.2 (cubic-like energy scaling)
            power_draw = self.base_power_kw * (effective_speed ** 1.1)
            rec["energy_kwh"] += power_draw * step_duration

            yield self.env.timeout(step_duration)

    def _hourly_monitor_process(self):
        """Records hourly snapshots of factory performance."""
        while self.env.now < self.sim_hours:
            now = self.env.now
            cum_units = sum(r["units"] for r in self.machine_records.values())
            cum_energy = sum(r["energy_kwh"] for r in self.machine_records.values())
            cum_failures = sum(r["failures"] for r in self.machine_records.values())
            cum_unplanned_dt = sum(r["unplanned_dt_hours"] for r in self.machine_records.values())
            cum_planned_dt = sum(r["planned_dt_hours"] for r in self.machine_records.values())

            # Hourly cost accumulation
            cost = (
                (cum_energy * self.energy_tariff)
                + (cum_unplanned_dt * self.loss_per_hour)
                + (cum_planned_dt * self.biz.planned_maintenance_cost_per_hour)
                + (cum_failures * (self.biz.avg_spare_part_cost * self.biz.emergency_markup))
            )

            self.hourly_log.append({
                "hour": round(now, 1),
                "production": round(cum_units, 1),
                "energy_kwh": round(cum_energy, 1),
                "cost_inr": round(cost, 2),
                "failures": cum_failures,
            })
            yield self.env.timeout(max(1.0, self.sim_hours / 100.0))  # ~100 data points

    def run(self) -> SimulationRunSummary:
        """Executes the SimPy environment and returns typed run summary."""
        self._setup_processes()
        self.env.run(until=self.sim_hours)

        # Assemble per-machine metrics
        machine_metrics: List[MachineSimMetrics] = []
        for mid, rec in self.machine_records.items():
            energy_cost = rec["energy_kwh"] * self.energy_tariff
            downtime_cost = rec["unplanned_dt_hours"] * self.loss_per_hour
            planned_maint_cost = rec["planned_dt_hours"] * self.biz.planned_maintenance_cost_per_hour
            emergency_parts_cost = rec["failures"] * (self.biz.avg_spare_part_cost * self.biz.emergency_markup)
            maint_cost = planned_maint_cost + emergency_parts_cost
            total_m_cost = energy_cost + downtime_cost + maint_cost

            machine_metrics.append(MachineSimMetrics(
                machine_id=mid,
                machine_name=rec["name"],
                units_produced=round(rec["units"], 1),
                operating_hours=round(rec["operating_hours"], 1),
                idle_hours=round(max(0.0, self.sim_hours - rec["operating_hours"] - rec["unplanned_dt_hours"] - rec["planned_dt_hours"]), 1),
                unplanned_downtime_hours=round(rec["unplanned_dt_hours"], 1),
                planned_downtime_hours=round(rec["planned_dt_hours"], 1),
                failure_count=rec["failures"],
                energy_kwh=round(rec["energy_kwh"], 1),
                energy_cost_inr=round(energy_cost, 2),
                downtime_loss_inr=round(downtime_cost, 2),
                maintenance_cost_inr=round(maint_cost, 2),
                total_cost_inr=round(total_m_cost, 2),
            ))

        total_units = sum(m.units_produced for m in machine_metrics)
        deficit = max(0.0, self.target_units - total_units)
        # Delay penalty prorated to deficit
        delay_penalty = (deficit / max(1.0, self.target_units)) * self.biz.delay_penalty_per_hour * self.sim_hours

        total_unplanned_dt = sum(m.unplanned_downtime_hours for m in machine_metrics)
        total_planned_dt = sum(m.planned_downtime_hours for m in machine_metrics)
        total_failures = sum(m.failure_count for m in machine_metrics)
        total_energy_kwh = sum(m.energy_kwh for m in machine_metrics)
        total_energy_cost = sum(m.energy_cost_inr for m in machine_metrics)
        total_downtime_loss = sum(m.downtime_loss_inr for m in machine_metrics)
        total_maint_cost = sum(m.maintenance_cost_inr for m in machine_metrics)

        total_fin_cost = total_energy_cost + total_downtime_loss + total_maint_cost + delay_penalty

        return SimulationRunSummary(
            total_units_produced=round(total_units, 1),
            target_units=round(self.target_units, 1),
            production_deficit_units=round(deficit, 1),
            total_operating_hours=round(sum(m.operating_hours for m in machine_metrics), 1),
            total_unplanned_downtime_hours=round(total_unplanned_dt, 1),
            total_planned_downtime_hours=round(total_planned_dt, 1),
            total_failures=total_failures,
            total_energy_kwh=round(total_energy_kwh, 1),
            total_energy_cost_inr=round(total_energy_cost, 2),
            total_downtime_loss_inr=round(total_downtime_loss, 2),
            total_maintenance_cost_inr=round(total_maint_cost, 2),
            total_delay_penalty_inr=round(delay_penalty, 2),
            total_financial_cost_inr=round(total_fin_cost, 2),
            machines=machine_metrics,
            hourly_trajectory=self.hourly_log,
        )


# ── What-If Comparison Coordinator ────────────────────────────────────

class WhatIfSimulatorService:
    """
    Coordinates Baseline vs. Scenario runs, computes net ROI deltas,
    and persists execution records into SQLite.
    """

    def _get_live_rul_map(self) -> Dict[int, float]:
        """Extracts current predicted RULs from the Digital Twin engine."""
        from backend.simulation.engine import get_simulation_engine
        engine = get_simulation_engine()
        rul_map: Dict[int, float] = {}
        for mid, state in engine.machines_state.items():
            pred = state.get("latest_prediction")
            if pred and "rul_predicted" in pred:
                rul_map[mid] = float(pred["rul_predicted"])
            else:
                rul_map[mid] = 125.0  # healthy baseline
        return rul_map

    def _fresh_biz_cfg(self) -> Any:
        """Loads fresh business parameters from config.yaml."""
        from backend.services.business_impact import get_business_calculator
        return get_business_calculator()._fresh_cfg()

    def run_comparison(
        self,
        scenario_config: WhatIfRequestConfig,
        user_id: Optional[int] = None,
    ) -> WhatIfComparisonResult:
        """
        Executes:
        1. Baseline run (no changes: all speed=1.0, no shutdowns, no shifts).
        2. Scenario run (applies requested what-if overrides).
        3. Computes net ROI deltas & synthesizes conclusion.
        4. Persists record in database table `simulation_results`.
        """
        start_wall_time = time.time()
        biz_cfg = self._fresh_biz_cfg()
        rul_map = self._get_live_rul_map()
        sim_hours = scenario_config.sim_hours

        # ── 1. Baseline Model ─────────────────────────────────────────
        # Default parameters: every machine running normally at 1.0x speed
        cfg = get_settings()
        baseline_params: Dict[int, MachineScenarioParam] = {
            m.id: MachineScenarioParam(machine_id=m.id, speed_factor=1.0)
            for m in cfg.machines
        }
        baseline_sim = SimPyFactoryModel(
            sim_hours=sim_hours,
            machine_params=baseline_params,
            ml_rul_map=rul_map,
            biz_cfg=biz_cfg,
            seed=42,
        )
        baseline_summary = baseline_sim.run()

        # ── 2. Scenario Model ─────────────────────────────────────────
        scenario_sim = SimPyFactoryModel(
            sim_hours=sim_hours,
            machine_params=scenario_config.machines,
            ml_rul_map=rul_map,
            biz_cfg=biz_cfg,
            seed=42,
        )
        scenario_summary = scenario_sim.run()

        # ── 3. Delta Computations ─────────────────────────────────────
        net_savings = baseline_summary.total_financial_cost_inr - scenario_summary.total_financial_cost_inr
        prod_delta = scenario_summary.total_units_produced - baseline_summary.total_units_produced
        dt_avoided = baseline_summary.total_unplanned_downtime_hours - scenario_summary.total_unplanned_downtime_hours
        energy_saved = baseline_summary.total_energy_kwh - scenario_summary.total_energy_kwh

        if net_savings > 0:
            roi_text = (
                f"✅ SCENARIO RECOMMENDED: Saves ₹{net_savings:,.0f} over {sim_hours:.0f} hours. "
                f"Avoids {dt_avoided:.1f} hours of catastrophic downtime. "
                f"Production delta: {prod_delta:+.0f} units."
            )
        else:
            roi_text = (
                f"⚠️ BASELINE PREFERRED: Scenario costs ₹{abs(net_savings):,.0f} more. "
                f"Production delta: {prod_delta:+.0f} units. Review parameters before implementing."
            )

        duration = time.time() - start_wall_time
        timestamp_str = datetime.now().isoformat()

        result = WhatIfComparisonResult(
            scenario_name=scenario_config.scenario_name,
            description=scenario_config.description,
            sim_hours=sim_hours,
            timestamp=timestamp_str,
            baseline=baseline_summary,
            scenario=scenario_summary,
            net_savings_inr=round(net_savings, 2),
            production_delta_units=round(prod_delta, 1),
            downtime_avoided_hours=round(dt_avoided, 1),
            energy_saved_kwh=round(energy_saved, 1),
            roi_summary=roi_text,
        )

        # ── 4. Persist to Database ────────────────────────────────────
        try:
            db = SessionLocal()
            db_record = SimulationResult(
                scenario_name=scenario_config.scenario_name,
                description=scenario_config.description,
                parameters=json.dumps({
                    "sim_hours": sim_hours,
                    "machines": {
                        str(mid): asdict(param) for mid, param in scenario_config.machines.items()
                    },
                }),
                results=json.dumps(asdict(scenario_summary)),
                baseline_results=json.dumps(asdict(baseline_summary)),
                duration_seconds=round(duration, 3),
                created_by=user_id,
            )
            db.add(db_record)
            db.commit()
            db.close()
        except Exception as e:
            print(f"⚠️ Warning: Could not persist simulation result to DB: {e}")

        return result


# ── Preset Template Scenarios ─────────────────────────────────────────

def get_scenario_templates() -> List[Dict[str, Any]]:
    """Returns curated preset scenarios for rapid demo testing."""
    return [
        {
            "id": "proactive_shutdown_machine_3",
            "name": "Proactive 4h Maintenance on Machine 3 (Compressor-03)",
            "description": "Immediately pauses Compressor-03 for 4 hours of scheduled maintenance at t=0, avoiding its catastrophic breakdown later in the week.",
            "sim_hours": 168.0,
            "machines": {
                3: {
                    "machine_id": 3,
                    "speed_factor": 1.0,
                    "is_shutdown": True,
                    "shutdown_duration_hours": 4.0,
                    "shutdown_start_hour": 0.0,
                    "shifted_to_machine_id": None,
                }
            },
        },
        {
            "id": "shift_load_m3_to_m2",
            "name": "Shift Workload from Machine 3 to Pump-02",
            "description": "Shuts down degraded Compressor-03 for 8 hours while shifting its workload to healthy Pump-02 (+80% throughput) to avoid production loss.",
            "sim_hours": 168.0,
            "machines": {
                3: {
                    "machine_id": 3,
                    "speed_factor": 1.0,
                    "is_shutdown": True,
                    "shutdown_duration_hours": 8.0,
                    "shutdown_start_hour": 0.0,
                    "shifted_to_machine_id": 2,
                },
                2: {
                    "machine_id": 2,
                    "speed_factor": 1.0,
                    "is_shutdown": False,
                    "shutdown_duration_hours": 0.0,
                    "shutdown_start_hour": 0.0,
                    "shifted_to_machine_id": None,
                }
            },
        },
        {
            "id": "throttle_speed_degraded_machines",
            "name": "Throttle Speed by 20% on Degraded Machine 3",
            "description": "Reduces Compressor-03 speed to 0.8x to slow down mechanical wear and extend its RUL by ~30%, preventing immediate mid-week failure.",
            "sim_hours": 168.0,
            "machines": {
                3: {
                    "machine_id": 3,
                    "speed_factor": 0.80,
                    "is_shutdown": False,
                    "shutdown_duration_hours": 0.0,
                    "shutdown_start_hour": 0.0,
                    "shifted_to_machine_id": None,
                }
            },
        },
    ]


# Singleton instance
_whatif_service_instance: Optional[WhatIfSimulatorService] = None


def get_whatif_service() -> WhatIfSimulatorService:
    global _whatif_service_instance
    if _whatif_service_instance is None:
        _whatif_service_instance = WhatIfSimulatorService()
    return _whatif_service_instance

