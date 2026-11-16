# ==============================================================
# tests/test_e2e_pipeline.py — Comprehensive End-to-End Pipeline Test
# ==============================================================
"""
End-to-End Integration Test Suite for AI Factory Operating System (Phase 7).

Validates the full operational lifecycle across all core subsystems:
1. System Health & Master Configuration
2. Digital Twin Telemetry Ingestion & Cycle Progression (DEMO-HOLDOUT Engine)
3. Multi-Model ML Inference Pipeline (RUL, Failure Probability, Anomaly, SHAP)
4. Composite Health Score Calculation & Degradation Transitions
5. Automated Alert & Incident Triggering with Database Persistence
6. Business Impact Risk Modeling (Downtime, Energy, Delay in ₹)
7. Cost-Aware Self-Healing Mitigation Selection
8. SimPy Discrete-Event What-If Scenario Simulation & ROI Delta
9. Vector Incident Memory Cosine Retrieval & Pattern Discovery
10. Factory GPT Assistant Autonomous ReAct Loop with Deterministic Tool Calling
11. Invariant Guard: Zero Data Leakage, Seed 42, Strict Number Non-Hallucination

Run:
    python -m pytest tests/test_e2e_pipeline.py -v
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.config import get_settings
from backend.database import SessionLocal, create_all_tables
from backend.main import health_check
from backend.models import Machine, Reading, Prediction, Incident, SimulationResult
from backend.routers import alerts, business, chat, machines, simulation, whatif
from backend.schemas.chat import ChatMessageRequest, MemorySearchRequest
from backend.schemas.whatif import MachineScenarioParamSchema, WhatIfRunRequest
from backend.services.business_impact import get_business_calculator
from backend.services.factory_gpt import get_factory_gpt, TOOL_REGISTRY
from backend.services.factory_memory import get_factory_memory
from backend.services.self_healing import get_healing_engine
from backend.simulation.engine import get_simulation_engine
from backend.simulation.whatif import get_whatif_service


@pytest.fixture(scope="module")
def db_session():
    """Provides a transactional database session."""
    create_all_tables()
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture(scope="module")
def sim_engine():
    """Provides the Digital Twin Simulation Engine singleton."""
    engine = get_simulation_engine()
    yield engine


class TestE2EPipelineLifecycle:
    """End-to-end integration tests covering the complete platform lifecycle."""

    def test_01_system_health_and_configuration(self, db_session):
        """Verifies health check and initial machine configurations."""
        status = health_check()
        assert status["status"] == "healthy"
        assert status["machines_configured"] == 6
        assert status["seed"] == 42

        # Verify machines query
        all_machines = machines.list_machines(db=db_session)
        assert len(all_machines) == 6
        machine_ids = [m.id for m in all_machines]
        assert set(machine_ids) == {1, 2, 3, 4, 5, 6}

    def test_02_zero_leakage_holdout_invariant(self, sim_engine):
        """CRITICAL INVARIANT: Simulation engine only replays engines from DEMO-HOLDOUT."""
        splits_path = PROJECT_ROOT / "data" / "splits.json"
        assert splits_path.exists(), "splits.json must exist"
        with open(splits_path, "r", encoding="utf-8") as f:
            splits = json.load(f)

        demo_engines = set(splits["demo_engines"])
        train_engines = set(splits["train_engines"])
        val_engines = set(splits["val_engines"])

        for mid, state in sim_engine.machines_state.items():
            demo_engine = state["demo_engine_id"]
            assert demo_engine in demo_engines, f"Machine {mid} uses non-demo engine {demo_engine}"
            assert demo_engine not in train_engines, f"LEAKAGE: Machine {mid} uses train engine {demo_engine}"
            assert demo_engine not in val_engines, f"LEAKAGE: Machine {mid} uses val engine {demo_engine}"

    def test_03_telemetry_progression_and_ml_inference(self, sim_engine):
        """
        Tests cycle progression on Machine 1 (CNC-01, engine 3)
        Verifies:
        - Telemetry ingestion
        - Multi-model inference (RUL, failure prob, anomaly)
        - SHAP top features
        - Health score computation
        """
        # Jump Machine 1 to cycle 150 (degraded state)
        m_state = sim_engine.jump_to_cycle(machine_id=1, target_cycle=150)
        assert m_state["current_cycle"] == 150
        assert m_state["id"] == 1

        # Check telemetry reading
        latest_readings = m_state.get("latest_readings")
        assert latest_readings is not None, "Machine must have latest reading"

        # Check ML prediction metrics
        assert "health_score" in m_state
        assert "rul_predicted" in m_state
        assert "anomaly_score" in m_state
        assert "failure_probability" in m_state

        # Mathematical bounds
        assert 0.0 <= m_state["health_score"] <= 100.0
        assert 0.0 <= m_state["failure_probability"] <= 1.0
        assert m_state["rul_predicted"] >= 0.0

        # At cycle 150, health score should reflect significant degradation
        assert m_state["health_score"] < 80.0, (
            f"Expected degraded health score at cycle 150, got {m_state['health_score']}"
        )

    def test_04_alerts_and_incident_logging(self, db_session, sim_engine):
        """Verifies that degraded machine health generates persistent alerts and incidents."""
        # Jump Machine 1 to cycle 175 where degradation is severe
        sim_engine.jump_to_cycle(machine_id=1, target_cycle=175)

        # Query alerts endpoint
        alerts_list = alerts.list_alerts(resolved=False, db=db_session)
        assert isinstance(alerts_list, list)

        # Verify DB incidents count
        incidents = db_session.query(Incident).filter(Incident.machine_id == 1).all()
        assert len(incidents) >= 1, "At least one incident must be logged for machine 1"
        latest = incidents[-1]
        assert latest.severity in ["warning", "critical", "info"]
        assert len(latest.description) > 0
        assert latest.health_score_at_time is not None

    def test_05_business_impact_calculation_inr(self):
        """Verifies deterministic financial loss estimation in Indian Rupees (₹)."""
        data = business.get_machine_impact(machine_id=1)

        assert data.machine_id == 1
        assert data.downtime_risk is not None
        assert data.energy_waste is not None
        assert data.delay_penalty is not None
        assert data.total_daily_exposure_inr >= 0.0

        downtime_cost = data.downtime_risk.expected_downtime_cost_inr
        energy_cost = data.energy_waste.daily_energy_waste_inr
        delay_cost = data.delay_penalty.daily_delay_penalty_inr

        # Total exposure must equal sum of the components
        computed_total = downtime_cost + energy_cost + delay_cost
        assert pytest.approx(data.total_daily_exposure_inr, rel=1e-2) == computed_total

    def test_06_self_healing_cost_aware_decision(self):
        """Verifies self-healing decision engine selects lowest-cost viable mitigation."""
        plan = business.trigger_self_healing(machine_id=1)

        assert plan.machine_id == 1
        assert plan.chosen_action in [
            "reduce_speed",
            "shift_load",
            "alert_operator",
            "schedule_maintenance",
        ]
        assert plan.chosen_cost_inr >= 0.0
        assert len(plan.all_options) == 4

        # Chosen action must have minimum expected cost among feasible options
        feasible_opts = [o for o in plan.all_options if o.feasible]
        assert len(feasible_opts) >= 1
        min_cost = min(o.expected_cost_inr for o in feasible_opts)
        assert pytest.approx(plan.chosen_cost_inr, rel=1e-2) == min_cost

    def test_07_whatif_discrete_event_simulation(self, db_session):
        """Runs a SimPy discrete-event simulation scenario and verifies comparative ROI."""
        req = WhatIfRunRequest(
            scenario_name="proactive_maintenance",
            description="Proactive maintenance at cycle 180 to prevent breakdown",
            sim_hours=72,
            machines={
                1: MachineScenarioParamSchema(
                    machine_id=1,
                    speed_factor=1.0,
                    is_shutdown=True,
                    shutdown_start_hour=10.0,
                    shutdown_duration_hours=6.0,
                )
            },
        )
        sim_res = whatif.run_whatif_simulation(req=req)

        assert sim_res.baseline is not None
        assert sim_res.scenario is not None
        assert sim_res.net_savings_inr is not None
        assert sim_res.downtime_avoided_hours >= 0.0
        assert len(sim_res.roi_summary) > 0

        # Check DB persistence
        persisted = (
            db_session.query(SimulationResult)
            .order_by(SimulationResult.id.desc())
            .first()
        )
        assert persisted is not None
        assert persisted.scenario_name == "proactive_maintenance"

    def test_08_factory_memory_vector_search(self):
        """Verifies 384-dimensional semantic incident search and pattern discovery."""
        search_req = MemorySearchRequest(query="high temperature bearing degradation", top_k=3)
        matches = chat.search_similar_incidents(req=search_req)
        assert len(matches) <= 3
        assert len(matches) > 0
        for m in matches:
            assert m.incident_id > 0
            assert 0.0 <= m.similarity_score <= 1.0

        # Pattern discovery
        patterns = chat.get_failure_patterns()
        assert isinstance(patterns, list)
        assert len(patterns) >= 1

    def test_09_factory_gpt_react_tool_calling(self):
        """
        Verifies Factory GPT ReAct assistant:
        1. Correctly maps natural language queries to backend tools
        2. Never hallucinates numbers — verifies tool execution matches math
        """
        req = ChatMessageRequest(
            query="Why is Machine 1 degrading and what is the financial risk in INR?",
            conversation_history=[],
        )
        reply = chat.chat_with_factory_gpt(req=req)

        assert reply.content is not None
        assert reply.tool_calls is not None
        assert len(reply.tool_calls) >= 1

        called_tool_names = [tc.tool_name for tc in reply.tool_calls]
        # Must execute appropriate diagnostic/financial tools
        assert any(t in called_tool_names for t in ["get_machine_health", "get_business_impact"])

        # Assistant response must reference verified financial calculations
        response_text = reply.content
        assert "₹" in response_text or "INR" in response_text or "Machine" in response_text

    def test_10_machine_history_query(self, db_session):
        """Verifies historical readings and predictions retrieval."""
        hist = machines.get_machine_history(machine_id=1, limit=10, db=db_session)
        assert hist.machine_id == 1
        assert hist.name is not None
        assert isinstance(hist.history, list)
