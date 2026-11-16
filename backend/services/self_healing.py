# ==============================================================
# backend/services/self_healing.py — Self-Healing Rule Engine
# ==============================================================
"""
Implements a cost-aware rule engine that automatically selects and executes
the cheapest corrective action when a machine enters WARNING or CRITICAL state.

Design: Pure decision logic — no ML, no LLM. The LLM (Phase 6) explains.
        Every decision is logged with its cost reasoning for audit trails.

Actions (from config.yaml):
─────────────────────────────────────────────────────────────────
1. reduce_speed       — Reduce machine speed 20% → extends RUL ~30%
                        Cost = energy savings MINUS lost production
2. shift_load         — Move workload to healthiest available machine
                        Cost = 0 (if feasible) or high (if infeasible)
3. alert_operator     — Send urgent notification → 30-min human response
                        Cost = technician time + potential late-action penalty
4. schedule_maintenance — Book preventive maintenance in next 4-hour slot
                        Cost = planned maintenance cost (cheapest long-term)

Selection criterion: MINIMUM expected total cost in ₹.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

from backend.config import get_settings
from backend.services.business_impact import get_business_calculator


# ── Typed result structures ──────────────────────────────────────────

@dataclass
class ActionOption:
    """Represents one evaluated self-healing action with its cost estimate."""
    action_name: str
    description: str
    feasible: bool
    expected_cost_inr: float
    cost_breakdown: Dict[str, float]
    reasoning: str


@dataclass
class SelfHealingDecision:
    """Full decision record: all evaluated options and the chosen action."""
    machine_id: int
    machine_name: str
    trigger_health: float
    trigger_rul: float
    trigger_failure_prob: float
    alert_level: str

    all_options: List[ActionOption]
    chosen_action: str
    chosen_cost_inr: float
    chosen_reasoning: str

    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    executed: bool = False
    execution_message: str = ""


# ── In-memory heal history ────────────────────────────────────────────
# Stored in memory for the demo; Phase 6 (Factory Memory) will persist to FAISS.
_heal_history: List[Dict[str, Any]] = []


# ── Rule Engine ──────────────────────────────────────────────────────

class SelfHealingEngine:
    """
    Cost-aware rule engine for autonomous machine recovery decisions.

    For each triggered machine, evaluates all configured actions,
    computes expected cost for each, and picks the minimum.
    """

    def __init__(self):
        self._calc = get_business_calculator()

    def _fresh_cfg(self):
        """Re-reads config.yaml each call to pick up live UI edits."""
        cfg_path = Path(__file__).resolve().parent.parent.parent / "config.yaml"
        with open(cfg_path, "r") as f:
            raw = yaml.safe_load(f)
        from backend.config import BusinessConfig, SelfHealingConfig
        biz = BusinessConfig(**raw.get("business", {}))
        healing = SelfHealingConfig(**raw.get("self_healing", {"actions": []}))
        return biz, healing

    # ── Cost estimators per action ───────────────────────────────────

    def _cost_reduce_speed(
        self,
        health_score: float,
        rul_predicted: float,
        failure_probability: float,
        biz_cfg,
        action_cfg,
    ) -> ActionOption:
        """
        Reduce speed by 20% → RUL extends by ~30% (from config rul_extension_factor).

        Expected Cost = new_downtime_risk − old_downtime_risk (net change)
                      + production_loss_from_speed_reduction

        Speed reduction lowers throughput:
            production_loss = speed_reduction × target_units/day × penalty_rate × 24hrs
        """
        speed_reduction = action_cfg.speed_reduction or 0.20
        rul_ext_factor = action_cfg.rul_extension_factor or 1.30

        # Extended RUL lowers failure probability proportionally
        new_rul = rul_predicted * rul_ext_factor
        new_fp  = failure_probability / rul_ext_factor  # less urgent

        old_risk = failure_probability * max(1, rul_predicted) * biz_cfg.loss_per_hour
        new_risk = new_fp * max(1, new_rul) * biz_cfg.loss_per_hour
        risk_saving = old_risk - new_risk  # positive = we save this much

        # Production loss from slowing down
        prod_loss_units_day = speed_reduction * biz_cfg.daily_production_target
        prod_loss_cost = (prod_loss_units_day / biz_cfg.daily_production_target) * \
                         biz_cfg.delay_penalty_per_hour * 24.0

        # Net cost = production penalty - risk saving (we want this to be small/negative)
        net_cost = prod_loss_cost - risk_saving

        return ActionOption(
            action_name="reduce_speed",
            description=f"Reduce speed {speed_reduction*100:.0f}% → RUL extends {(rul_ext_factor-1)*100:.0f}%",
            feasible=True,
            expected_cost_inr=round(max(0, net_cost), 2),
            cost_breakdown={
                "production_loss_inr": round(prod_loss_cost, 2),
                "risk_saving_inr": round(risk_saving, 2),
                "net_cost_inr": round(max(0, net_cost), 2),
            },
            reasoning=(
                f"Slowing machine {speed_reduction*100:.0f}% costs ₹{prod_loss_cost:,.0f}/day "
                f"in production, but saves ₹{risk_saving:,.0f} in downtime risk. "
                f"Net cost: ₹{max(0, net_cost):,.0f}."
            ),
        )

    def _cost_shift_load(
        self,
        machine_id: int,
        health_score: float,
        all_machine_states: Optional[Dict[int, Dict]] = None,
        biz_cfg=None,
        action_cfg=None,
    ) -> ActionOption:
        """
        Shift this machine's workload to the healthiest available peer.

        Feasible if any other machine has health > min_target_health.
        Cost ≈ 0 if feasible (the other machine absorbs load at no extra cost),
        VERY HIGH if infeasible (no machine can take the load — cascading failure risk).
        """
        min_health = action_cfg.min_target_health if action_cfg else 70

        # Find healthiest alternative
        best_target = None
        best_health = -1.0

        if all_machine_states:
            for mid, state in all_machine_states.items():
                if mid == machine_id:
                    continue
                h = state.get("health_score", 0)
                if h > min_health and h > best_health:
                    best_health = h
                    best_target = state.get("name", f"Machine {mid}")

        if best_target:
            # Feasible: some load overhead on the target machine (10% extra wear)
            # We model this as a small energy overhead cost
            overhead_cost = biz_cfg.machine_power_kw * 0.10 * 16 * biz_cfg.energy_tariff_per_kwh \
                            if biz_cfg else 0.0
            return ActionOption(
                action_name="shift_load",
                description=f"Shift load to {best_target} (health {best_health:.0f}%)",
                feasible=True,
                expected_cost_inr=round(overhead_cost, 2),
                cost_breakdown={"load_transfer_overhead_inr": round(overhead_cost, 2)},
                reasoning=(
                    f"Workload can be shifted to {best_target} (health={best_health:.0f}%). "
                    f"Small energy overhead ₹{overhead_cost:,.0f}. "
                    f"This machine gets time to recover."
                ),
            )
        else:
            # Infeasible: no healthy peer — model a high penalty
            infeasible_cost = (biz_cfg.loss_per_hour * 2.0) if biz_cfg else 999_999
            return ActionOption(
                action_name="shift_load",
                description="Shift load — NO healthy peer available",
                feasible=False,
                expected_cost_inr=infeasible_cost,
                cost_breakdown={"infeasibility_penalty_inr": infeasible_cost},
                reasoning=(
                    f"No machine has health > {min_health}%. "
                    f"Shifting load is infeasible; assigning a high penalty cost."
                ),
            )

    def _cost_alert_operator(
        self,
        rul_predicted: float,
        failure_probability: float,
        biz_cfg,
        action_cfg,
    ) -> ActionOption:
        """
        Alert operator → human responds in ~30 mins.

        Cost = technician callout (1 hour) + residual failure risk during response time.
        If failure probability is high and RUL < response window, risk remains large.
        """
        response_hrs = (action_cfg.response_time_minutes or 30) / 60.0

        # Technician callout cost (1-hour minimum)
        callout = biz_cfg.technician_hourly_rate * biz_cfg.overtime_multiplier

        # Residual downtime risk during response window (30 min delay)
        residual_risk = failure_probability * response_hrs * biz_cfg.loss_per_hour

        total = callout + residual_risk

        return ActionOption(
            action_name="alert_operator",
            description=f"Alert maintenance team — {action_cfg.response_time_minutes or 30}-min response",
            feasible=True,
            expected_cost_inr=round(total, 2),
            cost_breakdown={
                "technician_callout_inr": round(callout, 2),
                "residual_risk_during_response_inr": round(residual_risk, 2),
            },
            reasoning=(
                f"Technician callout ₹{callout:,.0f} + "
                f"failure risk during {response_hrs*60:.0f}-min response = ₹{residual_risk:,.0f}. "
                f"Total ₹{total:,.0f}."
            ),
        )

    def _cost_schedule_maintenance(
        self,
        biz_cfg,
        action_cfg,
    ) -> ActionOption:
        """
        Schedule planned maintenance in next available slot (4-hour lead time).

        Cost = planned maintenance cost (parts + labour at standard rate).
        This is always feasible and known upfront.
        """
        lead_hours = action_cfg.lead_time_hours or 4

        planned_parts = biz_cfg.avg_spare_part_cost
        planned_labour = lead_hours * biz_cfg.technician_hourly_rate
        planned_total = planned_parts + planned_labour

        # During lead_time, machine still operates (slight risk)
        lead_risk = 0.05 * lead_hours * biz_cfg.loss_per_hour  # ~5% base risk

        total = planned_total + lead_risk

        return ActionOption(
            action_name="schedule_maintenance",
            description=f"Schedule preventive maintenance (₹{planned_total:,.0f}) in {lead_hours}h",
            feasible=True,
            expected_cost_inr=round(total, 2),
            cost_breakdown={
                "planned_parts_inr": round(planned_parts, 2),
                "planned_labour_inr": round(planned_labour, 2),
                "lead_time_risk_inr": round(lead_risk, 2),
            },
            reasoning=(
                f"Planned maintenance: ₹{planned_parts:,.0f} parts + ₹{planned_labour:,.0f} labour "
                f"+ ₹{lead_risk:,.0f} lead-time risk = ₹{total:,.0f}."
            ),
        )

    # ── Main evaluation function ─────────────────────────────────────

    def evaluate(
        self,
        machine_id: int,
        machine_name: str,
        health_score: float,
        rul_predicted: float,
        failure_probability: float,
        anomaly_score: float,
        alert_level: str,
        all_machine_states: Optional[Dict[int, Dict]] = None,
    ) -> SelfHealingDecision:
        """
        Evaluates all configured actions and returns the minimum-cost decision.

        Steps:
        1. Load fresh config (supports live UI edits)
        2. Score each action with its expected ₹ cost
        3. Sort by cost (ascending), pick cheapest feasible action
        4. Build the decision record with full reasoning
        """
        biz_cfg, healing_cfg = self._fresh_cfg()

        # Build a lookup of action configs by name
        action_map = {a.name: a for a in healing_cfg.actions}

        options: List[ActionOption] = []

        # ── Evaluate each action ─────────────────────────────────────
        # 1. reduce_speed
        if "reduce_speed" in action_map:
            options.append(self._cost_reduce_speed(
                health_score, rul_predicted, failure_probability,
                biz_cfg, action_map["reduce_speed"]
            ))

        # 2. shift_load
        if "shift_load" in action_map:
            options.append(self._cost_shift_load(
                machine_id, health_score, all_machine_states,
                biz_cfg, action_map.get("shift_load")
            ))

        # 3. alert_operator
        if "alert_operator" in action_map:
            options.append(self._cost_alert_operator(
                rul_predicted, failure_probability,
                biz_cfg, action_map["alert_operator"]
            ))

        # 4. schedule_maintenance
        if "schedule_maintenance" in action_map:
            options.append(self._cost_schedule_maintenance(
                biz_cfg, action_map["schedule_maintenance"]
            ))

        # ── Pick minimum-cost feasible action ──────────────────────
        feasible_options = [o for o in options if o.feasible]
        if not feasible_options:
            feasible_options = options  # fallback: pick any

        # Sort by cost ascending
        feasible_options.sort(key=lambda o: o.expected_cost_inr)
        chosen = feasible_options[0]

        decision = SelfHealingDecision(
            machine_id=machine_id,
            machine_name=machine_name,
            trigger_health=health_score,
            trigger_rul=rul_predicted,
            trigger_failure_prob=failure_probability,
            alert_level=alert_level,
            all_options=options,
            chosen_action=chosen.action_name,
            chosen_cost_inr=chosen.expected_cost_inr,
            chosen_reasoning=chosen.reasoning,
            executed=True,
            execution_message=f"Action '{chosen.action_name}' selected with min cost ₹{chosen.expected_cost_inr:,.0f}",
        )

        # ── Persist to in-memory history ─────────────────────────────
        _heal_history.append(_decision_to_dict(decision))

        return decision

    def get_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Returns recent self-healing decisions (newest first)."""
        return list(reversed(_heal_history[-limit:]))


# ── Serialization helpers ─────────────────────────────────────────────

def _decision_to_dict(d: SelfHealingDecision) -> Dict[str, Any]:
    return {
        "machine_id": d.machine_id,
        "machine_name": d.machine_name,
        "trigger_health": d.trigger_health,
        "trigger_rul": d.trigger_rul,
        "trigger_failure_prob": d.trigger_failure_prob,
        "alert_level": d.alert_level,
        "chosen_action": d.chosen_action,
        "chosen_cost_inr": d.chosen_cost_inr,
        "chosen_reasoning": d.chosen_reasoning,
        "all_options": [
            {
                "action_name": o.action_name,
                "description": o.description,
                "feasible": o.feasible,
                "expected_cost_inr": o.expected_cost_inr,
                "cost_breakdown": o.cost_breakdown,
                "reasoning": o.reasoning,
            }
            for o in d.all_options
        ],
        "timestamp": d.timestamp,
        "executed": d.executed,
        "execution_message": d.execution_message,
    }


# ── Singleton ─────────────────────────────────────────────────────────
_healing_engine: Optional[SelfHealingEngine] = None


def get_healing_engine() -> SelfHealingEngine:
    global _healing_engine
    if _healing_engine is None:
        _healing_engine = SelfHealingEngine()
    return _healing_engine

