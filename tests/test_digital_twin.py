# ==============================================================
# tests/test_digital_twin.py — Digital Twin Simulation Engine Tests
# ==============================================================
import json
from pathlib import Path
import pytest
from backend.simulation.engine import get_simulation_engine
from backend.database import SessionLocal

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SPLITS_PATH = PROJECT_ROOT / "data" / "splits.json"


@pytest.fixture
def sim_engine():
    return get_simulation_engine()


def test_simulation_uses_only_demo_engines(sim_engine):
    """
    CRITICAL RULE:
    Asserts that the 6 simulated machines ONLY replay engines from the
    DEMO-HOLDOUT split and NEVER train or validation engines.
    """
    assert SPLITS_PATH.exists()
    with open(SPLITS_PATH, "r", encoding="utf-8") as f:
        splits = json.load(f)

    train_ids = set(splits["train_engines"])
    val_ids = set(splits["val_engines"])
    demo_ids = set(splits["demo_engines"])

    for mid, m_state in sim_engine.machines_state.items():
        demo_engine_id = m_state["demo_engine_id"]
        assert demo_engine_id in demo_ids, (
            f"Machine {mid} uses engine {demo_engine_id} which is NOT in DEMO-HOLDOUT!"
        )
        assert demo_engine_id not in train_ids, (
            f"DATA LEAKAGE: Machine {mid} uses TRAIN engine {demo_engine_id}!"
        )
        assert demo_engine_id not in val_ids, (
            f"DATA LEAKAGE: Machine {mid} uses VALIDATION engine {demo_engine_id}!"
        )


def test_simulation_speed_control(sim_engine):
    """Asserts that speed control sets and bounds speed correctly."""
    sim_engine.set_speed(2.5)
    assert sim_engine.speed_factor == 2.5

    # Should clamp between 0.1 and 10.0
    sim_engine.set_speed(0.01)
    assert sim_engine.speed_factor == 0.1
    sim_engine.set_speed(50.0)
    assert sim_engine.speed_factor == 10.0

    # Reset to default 1.0
    sim_engine.set_speed(1.0)
    assert sim_engine.speed_factor == 1.0


def test_simulation_jump_to_cycle(sim_engine):
    """
    Tests the 'start degradation at cycle X' feature.
    Jumping to a late-life cycle should immediately update health and RUL.
    """
    # Machine 1 has max_cycle ~ 179
    max_c = sim_engine.machines_state[1]["max_cycle"]
    jump_cycle = max_c - 15  # 15 cycles before failure

    summary = sim_engine.jump_to_cycle(machine_id=1, target_cycle=jump_cycle)
    assert summary["current_cycle"] == jump_cycle
    assert summary["rul_predicted"] < 50.0  # RUL must drop significantly
    assert summary["status"] in ("warning", "critical")


def test_simulation_reset(sim_engine):
    """Asserts that reset brings all machines back to cycle 1 and idle status."""
    sim_engine.reset()
    for mid, m_state in sim_engine.machines_state.items():
        assert m_state["cycle"] == 1
        assert m_state["status"] == "idle"

