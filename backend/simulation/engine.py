# ==============================================================
# backend/simulation/engine.py — Digital Twin Simulation Engine
# ==============================================================
"""
Replays unseen DEMO-HOLDOUT C-MAPSS engines as live physical machines.
Supports:
- Speed control (0.1x to 10.0x)
- 'Start degradation at cycle X' (jump to cycle)
- Automated periodic background stepping
- Real-time ML inference per cycle (RUL, Anomaly, Failure Risk, Health)
- WebSocket telemetry broadcasting
- Database persistence of readings, predictions, and incidents
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from backend.config import get_settings
from backend.database import SessionLocal
from backend.ml.inference import get_ml_engine
from backend.models.incident import Incident
from backend.models.machine import Machine
from backend.models.prediction import Prediction
from backend.models.reading import Reading
from backend.models.sensor import Sensor
from backend.simulation.websocket_manager import ws_hub
from ml.data_loader import ALL_CMAPSS_COLS, USEFUL_SENSORS

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
RAW_CMAPSS_PATH = PROJECT_ROOT / "data" / "raw" / "train_FD001.txt"


class DigitalTwinEngine:
    """
    Simulates a live manufacturing floor of 6 machines by streaming unseen
    C-MAPSS engine degradation trajectories through the trained ML models.
    """

    def __init__(self) -> None:
        self.settings = get_settings()
        self.ml_engine = get_ml_engine()
        self.is_running: bool = False
        self.speed_factor: float = 1.0
        self.window_size: int = 30
        self.feature_cols = USEFUL_SENSORS

        # Machine in-memory simulation state
        # machine_id -> { "demo_id": int, "df": pd.DataFrame, "cycle": int, "max_cycle": int, "status": str }
        self.machines_state: Dict[int, Dict[str, Any]] = {}
        self._bg_task: Optional[asyncio.Task] = None
        self._init_machines()

    def _init_machines(self) -> None:
        """Loads demo engine trajectories and initializes machine states."""
        assert RAW_CMAPSS_PATH.exists(), f"Missing {RAW_CMAPSS_PATH}"
        all_train_df = pd.read_csv(
            RAW_CMAPSS_PATH, sep=r"\s+", header=None, names=ALL_CMAPSS_COLS
        )

        db = SessionLocal()
        try:
            # Seed sensors for all machines if not present
            sensor_count = db.query(Sensor).count()
            if sensor_count == 0:
                print("🌱 Seeding sensors in DB for 6 machines...")
                for mc in self.settings.machines:
                    for s_name in self.feature_cols:
                        db.add(Sensor(
                            machine_id=mc.id,
                            name=s_name,
                            description=f"C-MAPSS telemetry channel {s_name}",
                            unit="sensor_units",
                            is_active=1,
                        ))
                db.commit()

            # Initialize states from config.yaml
            for mc in self.settings.machines:
                demo_id = mc.demo_engine_id or 3
                # Extract strictly this demo engine's data
                engine_data = all_train_df[all_train_df["engine_id"] == demo_id].sort_values("cycle").reset_index(drop=True)
                max_cycle = int(engine_data["cycle"].max())

                # Check if machine exists in DB
                db_machine = db.query(Machine).filter(Machine.id == mc.id).first()
                start_cycle = db_machine.current_cycle if db_machine and db_machine.current_cycle > 0 else 1

                self.machines_state[mc.id] = {
                    "id": mc.id,
                    "name": mc.name,
                    "type": mc.type,
                    "location": mc.location,
                    "demo_engine_id": demo_id,
                    "df": engine_data,
                    "cycle": start_cycle,
                    "max_cycle": max_cycle,
                    "status": "idle",
                    "latest_prediction": None,
                    "latest_readings": {},
                }
            print(f"🏭 Initialised Digital Twin engine with {len(self.machines_state)} machines.")
        finally:
            db.close()

    def get_window_data(self, machine_id: int, current_cycle: int) -> np.ndarray:
        """
        Extracts a (30, 15) sensor window ending at current_cycle.
        Pads with earliest cycle if current_cycle < 30.
        """
        m_state = self.machines_state[machine_id]
        edf = m_state["df"]

        # Filter up to current_cycle
        history = edf[edf["cycle"] <= current_cycle]
        sensor_values = history[self.feature_cols].values

        n_rows = len(sensor_values)
        if n_rows >= self.window_size:
            return sensor_values[-self.window_size :, :]
        else:
            # Pad with earliest available readings
            pad_len = self.window_size - n_rows
            pad_prefix = np.repeat(sensor_values[:1, :], pad_len, axis=0)
            return np.vstack([pad_prefix, sensor_values])

    def step_machine(self, machine_id: int, db: Any) -> Dict[str, Any]:
        """Advances one machine by 1 cycle, runs ML inference, and persists updates."""
        m_state = self.machines_state[machine_id]
        current_cycle = m_state["cycle"]
        max_cycle = m_state["max_cycle"]

        # Check if already reached failure
        if current_cycle >= max_cycle:
            m_state["status"] = "failed"
            return self._build_machine_summary(machine_id)

        # Increment cycle
        current_cycle += 1
        m_state["cycle"] = current_cycle

        # Extract 30-cycle sensor window & run inference
        window_raw = self.get_window_data(machine_id, current_cycle)
        pred = self.ml_engine.predict_window(window_raw)

        # Determine machine status
        if current_cycle >= max_cycle:
            status = "failed"
        elif pred["alert_level"] == "critical":
            status = "critical"
        elif pred["alert_level"] == "warning":
            status = "warning"
        else:
            status = "running"

        m_state["status"] = status
        m_state["latest_prediction"] = pred

        # Current sensor readings at this cycle
        current_row = m_state["df"][m_state["df"]["cycle"] == current_cycle].iloc[0]
        readings_dict = {col: float(current_row[col]) for col in self.feature_cols}
        m_state["latest_readings"] = readings_dict

        # ── Database Persistence ──────────────────────────────────────
        db_machine = db.query(Machine).filter(Machine.id == machine_id).first()
        if db_machine:
            db_machine.current_cycle = current_cycle
            db_machine.status = status
            db_machine.health_score = pred["health_score"]
            db_machine.rul_predicted = pred["rul_predicted"]
            db_machine.anomaly_score = pred["anomaly_score"]
            db_machine.failure_probability = pred["failure_probability"]

        # Record prediction
        db_pred = Prediction(
            machine_id=machine_id,
            cycle=current_cycle,
            rul_predicted=pred["rul_predicted"],
            failure_probability=pred["failure_probability"],
            anomaly_score=pred["anomaly_score"],
            health_score=pred["health_score"],
            model_name="xgboost_rul + isolation_forest",
            shap_explanation=json.dumps(pred["shap_explanation"]),
            alert_level=pred["alert_level"],
        )
        db.add(db_pred)

        # Trigger Incident if warning/critical (deduplicated by alert transition)
        if pred["alert_level"] in ("warning", "critical") and current_cycle % 5 == 0:
            incident = Incident(
                machine_id=machine_id,
                cycle=current_cycle,
                severity=pred["alert_level"],
                category="predictive_degradation",
                description=(
                    f"Machine {m_state['name']} at cycle {current_cycle}: "
                    f"Health score dropped to {pred['health_score']:.1f}%, "
                    f"RUL predicted {pred['rul_predicted']:.1f} cycles, "
                    f"Anomaly score {pred['anomaly_score']:.2f}."
                ),
                health_score_at_time=pred["health_score"],
                rul_at_time=pred["rul_predicted"],
                anomaly_score_at_time=pred["anomaly_score"],
                resolved=False,
            )
            db.add(incident)

        return self._build_machine_summary(machine_id)

    def _build_machine_summary(self, machine_id: int) -> Dict[str, Any]:
        """Formats machine snapshot for API and WebSocket payloads."""
        m_state = self.machines_state[machine_id]
        pred = m_state.get("latest_prediction") or {}
        return {
            "id": machine_id,
            "name": m_state["name"],
            "type": m_state["type"],
            "location": m_state["location"],
            "demo_engine_id": m_state["demo_engine_id"],
            "current_cycle": m_state["cycle"],
            "max_cycle": m_state["max_cycle"],
            "status": m_state["status"],
            "health_score": pred.get("health_score", 100.0),
            "rul_predicted": pred.get("rul_predicted", 125.0),
            "anomaly_score": pred.get("anomaly_score", 0.05),
            "failure_probability": pred.get("failure_probability", 0.02),
            "alert_level": pred.get("alert_level", "normal"),
            "latest_readings": m_state.get("latest_readings", {}),
            "shap_explanation": pred.get("shap_explanation", {}),
        }

    async def step_all(self) -> List[Dict[str, Any]]:
        """Advances all 6 machines simultaneously and broadcasts update."""
        db = SessionLocal()
        summaries = []
        try:
            for machine_id in self.machines_state:
                res = self.step_machine(machine_id, db)
                summaries.append(res)
            db.commit()
        except Exception as e:
            db.rollback()
            print(f"❌ Error during step_all: {e}")
        finally:
            db.close()

        # Broadcast live telemetry over WebSocket
        payload = {
            "type": "telemetry",
            "timestamp": datetime.now().isoformat(),
            "speed_factor": self.speed_factor,
            "machines": summaries,
        }
        await ws_hub.broadcast_json(payload)
        return summaries

    async def _simulation_loop(self) -> None:
        """Background coroutine ticking every 1.0 / speed_factor seconds."""
        print("▶️ Digital Twin simulation loop started.")
        while self.is_running:
            await self.step_all()
            interval = max(0.1, 1.0 / max(0.1, self.speed_factor))
            await asyncio.sleep(interval)
        print("⏸️ Digital Twin simulation loop stopped.")

    def start(self) -> None:
        """Starts real-time live replay."""
        if not self.is_running:
            self.is_running = True
            for m in self.machines_state.values():
                if m["status"] == "idle":
                    m["status"] = "running"
            self._bg_task = asyncio.create_task(self._simulation_loop())

    def pause(self) -> None:
        """Pauses live replay."""
        self.is_running = False
        if self._bg_task:
            self._bg_task.cancel()
            self._bg_task = None
        for m in self.machines_state.values():
            if m["status"] == "running":
                m["status"] = "paused"

    def set_speed(self, speed: float) -> None:
        """Adjusts replay speed factor."""
        self.speed_factor = max(0.1, min(10.0, float(speed)))

    def jump_to_cycle(self, machine_id: int, target_cycle: int) -> Dict[str, Any]:
        """
        'Start degradation at cycle X' feature:
        Directly sets machine cycle to target_cycle, runs inference, and persists.
        """
        assert machine_id in self.machines_state, f"Invalid machine {machine_id}"
        m_state = self.machines_state[machine_id]
        target_cycle = max(1, min(m_state["max_cycle"], target_cycle))
        m_state["cycle"] = target_cycle - 1  # will increment to target_cycle in step_machine

        db = SessionLocal()
        try:
            res = self.step_machine(machine_id, db)
            db.commit()
            return res
        finally:
            db.close()

    def reset(self) -> None:
        """Resets all machines to cycle 1 with pristine health."""
        self.pause()
        db = SessionLocal()
        try:
            for machine_id, m_state in self.machines_state.items():
                m_state["cycle"] = 1
                m_state["status"] = "idle"
                m_state["latest_prediction"] = None
                m_state["latest_readings"] = {}
                db_m = db.query(Machine).filter(Machine.id == machine_id).first()
                if db_m:
                    db_m.current_cycle = 1
                    db_m.status = "idle"
                    db_m.health_score = 100.0
                    db_m.rul_predicted = 125.0
                    db_m.anomaly_score = 0.05
                    db_m.failure_probability = 0.02
            db.commit()
            print("🔄 Reset all machines to cycle 1.")
        finally:
            db.close()

    def get_status(self) -> Dict[str, Any]:
        """Returns overall simulation status."""
        active_count = sum(1 for m in self.machines_state.values() if m["status"] in ("running", "warning", "critical"))
        summaries = [self._build_machine_summary(mid) for mid in self.machines_state]
        return {
            "is_running": self.is_running,
            "speed_factor": self.speed_factor,
            "total_machines": len(self.machines_state),
            "active_machines": active_count,
            "machines_summary": summaries,
        }


# Singleton engine instance
_engine_instance: Optional[DigitalTwinEngine] = None


def get_simulation_engine() -> DigitalTwinEngine:
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = DigitalTwinEngine()
    return _engine_instance

