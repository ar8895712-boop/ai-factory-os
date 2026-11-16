# ==============================================================
# tests/test_factory_gpt.py — Unit tests for Factory GPT & Tools
# ==============================================================
"""
Tests for:
1. Tool registry dispatching (all 6 tools)
2. Tool outputs match verified mathematical calculations
3. Local ReAct engine intent routing and tool execution:
   - "Why is Machine 3 failing?" -> calls get_machine_health, explain_prediction, find_similar_incidents
   - "What if I shut down Machine 2?" -> calls run_simulation
   - "What is the financial cost?" -> calls get_business_impact
   - "What happened last time?" -> calls find_similar_incidents
4. Strict number invariant: assistant explains numbers from backend tools without fabricating math.

Run:
    python -m pytest tests/test_factory_gpt.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.services.factory_gpt import (
    TOOL_REGISTRY,
    FactoryGPTService,
    LocalReActEngine,
    get_factory_gpt,
    tool_explain_prediction,
    tool_find_similar_incidents,
    tool_get_business_impact,
    tool_get_machine_health,
    tool_get_rul,
    tool_run_simulation,
)


class TestToolRegistry:

    def test_all_six_tools_registered(self):
        """All 6 core tools must be in TOOL_REGISTRY."""
        expected = {
            "get_machine_health",
            "get_rul",
            "explain_prediction",
            "find_similar_incidents",
            "run_simulation",
            "get_business_impact",
        }
        assert expected.issubset(set(TOOL_REGISTRY.keys()))

    def test_tool_get_machine_health(self):
        res = tool_get_machine_health(1)
        assert res["machine_id"] == 1
        assert "health_score" in res
        assert "status" in res
        assert 0.0 <= res["health_score"] <= 100.0

    def test_tool_get_rul(self):
        res = tool_get_rul(3)
        assert res["machine_id"] == 3
        assert "rul_predicted_cycles" in res
        assert res["rul_predicted_cycles"] >= 0.0

    def test_tool_explain_prediction(self):
        res = tool_explain_prediction(3)
        assert res["machine_id"] == 3
        assert "top_feature_drivers" in res
        assert "explanation_summary" in res

    def test_tool_find_similar_incidents(self):
        res = tool_find_similar_incidents("compressor surge and vibration", top_k=2)
        assert res["match_count"] > 0
        assert len(res["matches"]) <= 2
        assert "similarity_score" in res["matches"][0]

    def test_tool_run_simulation(self):
        res = tool_run_simulation("shutdown", machine_id=3, sim_hours=24.0)
        assert "net_savings_inr" in res
        assert "downtime_avoided_hours" in res
        assert "roi_summary" in res

    def test_tool_get_business_impact_single_machine(self):
        res = tool_get_business_impact(3)
        assert res["machine_id"] == 3
        assert "total_daily_exposure_inr" in res
        assert res["total_daily_exposure_inr"] >= 0.0

    def test_tool_get_business_impact_fleet(self):
        res = tool_get_business_impact(0)
        assert "fleet_total_daily_exposure_inr" in res
        assert "critical_machines" in res


class TestLocalReActEngine:

    @pytest.fixture
    def react_engine(self) -> LocalReActEngine:
        return LocalReActEngine()

    def test_why_machine_failing_calls_diagnostic_tools(self, react_engine):
        """'Why is Machine 3 failing?' must trigger health, SHAP, and memory search."""
        answer, tools = react_engine.respond("Why is Machine 3 failing?")
        called_names = [t.tool_name for t in tools]

        assert "get_machine_health" in called_names
        assert "explain_prediction" in called_names
        assert "find_similar_incidents" in called_names
        assert "Machine 3" in answer or "Compressor" in answer
        assert "SHAP" in answer or "Root Cause" in answer

    def test_what_if_shutdown_calls_simulation(self, react_engine):
        """'What if I shut down Machine 2?' must trigger SimPy simulation."""
        answer, tools = react_engine.respond("What if I shut down Machine 2?")
        called_names = [t.tool_name for t in tools]

        assert "run_simulation" in called_names
        assert "SimPy" in answer or "Simulation" in answer
        assert "₹" in answer

    def test_past_incident_query_calls_vector_memory(self, react_engine):
        """'What happened last time with high vibration?' must call find_similar_incidents."""
        answer, tools = react_engine.respond("What happened last time with high vibration?")
        called_names = [t.tool_name for t in tools]

        assert "find_similar_incidents" in called_names
        assert "FAISS" in answer or "Incident" in answer

    def test_financial_cost_query_calls_business_impact(self, react_engine):
        """'What is the financial cost and impact?' must call get_business_impact."""
        answer, tools = react_engine.respond("What is the financial cost and exposure across the factory?")
        called_names = [t.tool_name for t in tools]

        assert "get_business_impact" in called_names
        assert "₹" in answer

    def test_numbers_derived_from_tools_not_fabricated(self, react_engine):
        """
        Verify that numbers quoted in the answer match values returned in tool records.
        """
        answer, tools = react_engine.respond("What is the status of Machine 1?")
        assert len(tools) >= 1
        rul_tool = next((t for t in tools if t.tool_name == "get_rul"), None)
        assert rul_tool is not None
        rul_val = rul_tool.result["rul_predicted_cycles"]
        # The exact RUL number from tool must be present in the text response
        assert f"{rul_val:.1f}" in answer or f"{int(rul_val)}" in answer

