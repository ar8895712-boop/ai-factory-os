# ==============================================================
# backend/services/factory_gpt.py — Factory GPT (RAG + Tool Calling)
# ==============================================================
"""
Factory GPT: Industrial AI assistant with RAG and Tool Calling.

CRITICAL RULE:
The LLM NEVER computes numbers. It decides which backend tools to invoke,
reads the verified calculations from the Phase 1–5 backend engines,
and explains the results in plain, actionable engineering language.

Tools:
1. get_machine_health(machine_id)
2. get_rul(machine_id)
3. explain_prediction(machine_id)
4. find_similar_incidents(query, top_k)
5. run_simulation(scenario_type, machine_id, sim_hours)
6. get_business_impact(machine_id)

Supports:
- OpenAI API (via OPENAI_API_KEY) with function calling.
- Autonomous Local ReAct Engine (100% free, offline laptop execution).
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple

from backend.config import get_settings
from backend.services.business_impact import get_business_calculator
from backend.services.factory_memory import get_factory_memory
from backend.services.self_healing import get_healing_engine
from backend.simulation.engine import get_simulation_engine
from backend.simulation.whatif import (
    MachineScenarioParam,
    WhatIfRequestConfig,
    get_whatif_service,
)


@dataclass
class ToolCallRecord:
    """Record of an executed tool call for UI inspection and verification."""
    tool_name: str
    arguments: Dict[str, Any]
    result: Any
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ChatMessage:
    """Chat message in the dialogue."""
    role: str                          # "user" | "assistant" | "system"
    content: str
    tool_calls: List[ToolCallRecord] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


# ── Tool Definitions for OpenAI Function Calling ──────────────────────

OPENAI_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_machine_health",
            "description": "Fetches current health score (0-100), operating status, cycles run, and alert level for a specific machine.",
            "parameters": {
                "type": "object",
                "properties": {
                    "machine_id": {
                        "type": "integer",
                        "description": "ID of the machine (1 to 6)",
                    }
                },
                "required": ["machine_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_rul",
            "description": "Fetches the machine learning Remaining Useful Life (RUL in cycles/hours) and failure probability for a machine.",
            "parameters": {
                "type": "object",
                "properties": {
                    "machine_id": {
                        "type": "integer",
                        "description": "ID of the machine (1 to 6)",
                    }
                },
                "required": ["machine_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "explain_prediction",
            "description": "Returns SHAP explainability feature contributions showing which specific sensor readings are driving the RUL reduction.",
            "parameters": {
                "type": "object",
                "properties": {
                    "machine_id": {
                        "type": "integer",
                        "description": "ID of the machine (1 to 6)",
                    }
                },
                "required": ["machine_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "find_similar_incidents",
            "description": "Performs semantic vector search over FAISS factory memory to find historical breakdown events with similar symptoms, root causes, and resolutions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Description of the symptom, failure pattern, or sensor behavior to search.",
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Number of similar incidents to return (default: 3).",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_simulation",
            "description": "Executes a SimPy what-if discrete-event simulation (e.g. shutdown for maintenance or speed throttling) to evaluate production deltas and net financial savings (₹).",
            "parameters": {
                "type": "object",
                "properties": {
                    "scenario_type": {
                        "type": "string",
                        "enum": ["shutdown", "throttle_speed"],
                        "description": "Type of intervention to simulate.",
                    },
                    "machine_id": {
                        "type": "integer",
                        "description": "Target machine ID (1 to 6).",
                    },
                    "sim_hours": {
                        "type": "number",
                        "description": "Simulation horizon in hours (default: 168h = 1 week).",
                    },
                },
                "required": ["scenario_type", "machine_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_business_impact",
            "description": "Calculates complete financial exposure in Indian Rupees (₹) including unplanned downtime risk, energy waste, delay penalties, and preventive maintenance savings.",
            "parameters": {
                "type": "object",
                "properties": {
                    "machine_id": {
                        "type": "integer",
                        "description": "Machine ID (1 to 6) or 0 for fleet-wide financial summary.",
                    }
                },
                "required": ["machine_id"],
            },
        },
    },
]


# ── Tool Implementations (Dispatch Table) ─────────────────────────────

def tool_get_machine_health(machine_id: int) -> Dict[str, Any]:
    engine = get_simulation_engine()
    if machine_id not in engine.machines_state:
        return {"error": f"Machine {machine_id} not found."}
    s = engine._build_machine_summary(machine_id)
    return {
        "machine_id": s["id"],
        "name": s["name"],
        "type": s["type"],
        "location": s["location"],
        "current_cycle": s["current_cycle"],
        "health_score": round(s["health_score"], 1),
        "status": s["status"],
        "alert_level": s["alert_level"],
        "anomaly_score": round(s["anomaly_score"], 3),
        "failure_probability": round(s["failure_probability"], 3),
    }


def tool_get_rul(machine_id: int) -> Dict[str, Any]:
    engine = get_simulation_engine()
    if machine_id not in engine.machines_state:
        return {"error": f"Machine {machine_id} not found."}
    s = engine._build_machine_summary(machine_id)
    return {
        "machine_id": s["id"],
        "name": s["name"],
        "rul_predicted_cycles": round(s["rul_predicted"], 1),
        "health_score": round(s["health_score"], 1),
        "failure_probability": round(s["failure_probability"], 3),
        "alert_level": s["alert_level"],
    }


def tool_explain_prediction(machine_id: int) -> Dict[str, Any]:
    engine = get_simulation_engine()
    if machine_id not in engine.machines_state:
        return {"error": f"Machine {machine_id} not found."}
    s = engine._build_machine_summary(machine_id)
    shap = s.get("shap_explanation", {})
    return {
        "machine_id": s["id"],
        "name": s["name"],
        "rul_predicted": s["rul_predicted"],
        "top_feature_drivers": shap.get("top_features", []),
        "explanation_summary": (
            f"Machine {s['name']} RUL is {s['rul_predicted']:.1f} cycles. "
            f"Main negative driver is sensor {shap.get('top_features', [{}])[0].get('feature', 's11')} "
            f"contributing {shap.get('top_features', [{}])[0].get('impact', 0):.1f} cycles."
            if shap.get("top_features") else "Normal baseline sensor behavior."
        ),
    }


def tool_find_similar_incidents(query: str, top_k: int = 3) -> Dict[str, Any]:
    memory = get_factory_memory()
    matches = memory.search_similar(query=query, top_k=top_k)
    return {
        "query": query,
        "match_count": len(matches),
        "matches": [asdict(m) for m in matches],
    }


def tool_run_simulation(
    scenario_type: str,
    machine_id: int,
    sim_hours: float = 168.0,
) -> Dict[str, Any]:
    whatif = get_whatif_service()
    is_shutdown = scenario_type.lower() == "shutdown"
    speed = 0.80 if "throttle" in scenario_type.lower() or "speed" in scenario_type.lower() else 1.0

    param = MachineScenarioParam(
        machine_id=machine_id,
        speed_factor=speed,
        is_shutdown=is_shutdown,
        shutdown_duration_hours=4.0 if is_shutdown else 0.0,
        shutdown_start_hour=0.0,
    )
    req = WhatIfRequestConfig(
        scenario_name=f"What-If {scenario_type.title()} on Machine {machine_id}",
        description=f"Automated scenario evaluation triggered via Factory GPT",
        sim_hours=sim_hours,
        machines={machine_id: param},
    )
    res = whatif.run_comparison(req)
    return {
        "scenario_name": res.scenario_name,
        "sim_hours": res.sim_hours,
        "net_savings_inr": res.net_savings_inr,
        "production_delta_units": res.production_delta_units,
        "downtime_avoided_hours": res.downtime_avoided_hours,
        "energy_saved_kwh": res.energy_saved_kwh,
        "roi_summary": res.roi_summary,
    }


def tool_get_business_impact(machine_id: int) -> Dict[str, Any]:
    calc = get_business_calculator()
    engine = get_simulation_engine()

    if machine_id == 0:
        # Fleet-wide roll up
        reports = []
        for mid in engine.machines_state:
            s = engine._build_machine_summary(mid)
            rep = calc.generate_report(
                machine_id=mid,
                machine_name=s["name"],
                health_score=s["health_score"],
                rul_predicted=s["rul_predicted"],
                failure_probability=s["failure_probability"],
                anomaly_score=s["anomaly_score"],
                alert_level=s["alert_level"],
            )
            reports.append(rep)
        from backend.services.business_impact import generate_fleet_summary
        return generate_fleet_summary(reports)

    if machine_id not in engine.machines_state:
        return {"error": f"Machine {machine_id} not found."}

    s = engine._build_machine_summary(machine_id)
    rep = calc.generate_report(
        machine_id=machine_id,
        machine_name=s["name"],
        health_score=s["health_score"],
        rul_predicted=s["rul_predicted"],
        failure_probability=s["failure_probability"],
        anomaly_score=s["anomaly_score"],
        alert_level=s["alert_level"],
    )
    return {
        "machine_id": rep.machine_id,
        "name": rep.machine_name,
        "total_daily_exposure_inr": rep.total_daily_exposure_inr,
        "downtime_risk_inr": rep.downtime_risk.expected_downtime_cost_inr,
        "daily_energy_waste_inr": rep.energy_waste.daily_energy_waste_inr,
        "daily_delay_penalty_inr": rep.delay_penalty.daily_delay_penalty_inr,
        "planned_maintenance_savings_inr": rep.maintenance_savings.savings_if_planned_inr,
        "recommendation": rep.recommendation,
    }


TOOL_REGISTRY: Dict[str, Callable[..., Any]] = {
    "get_machine_health": tool_get_machine_health,
    "get_rul": tool_get_rul,
    "explain_prediction": tool_explain_prediction,
    "find_similar_incidents": tool_find_similar_incidents,
    "run_simulation": tool_run_simulation,
    "get_business_impact": tool_get_business_impact,
}


# ── Autonomous ReAct Engine (Offline / Local Fallback) ────────────────

class LocalReActEngine:
    """
    Deterministic rule-guided ReAct agent.
    Parses user natural language queries, selects and executes backend tools,
    and synthesizes comprehensive answers with zero external API dependencies.
    """

    def _extract_machine_id(self, query: str) -> Optional[int]:
        # Match "machine 3", "machine #3", "cnc-01", "m3", "compressor-03", etc.
        m = re.search(r"\bmachine\s*#?\s*([1-6])\b", query, re.IGNORECASE)
        if m:
            return int(m.group(1))
        m2 = re.search(r"\bm([1-6])\b", query, re.IGNORECASE)
        if m2:
            return int(m2.group(1))

        # Check machine names
        names = {
            "cnc": 1, "cnc-01": 1,
            "pump": 2, "pump-02": 2,
            "compressor": 3, "compressor-03": 3,
            "turbine": 4, "turbine-04": 4,
            "conveyor": 5, "conveyor-05": 5,
            "grinder": 6, "grinder-06": 6,
        }
        for name, mid in names.items():
            if name in query.lower():
                return mid
        return None

    def respond(self, query: str) -> Tuple[str, List[ToolCallRecord]]:
        q_lower = query.lower()
        tool_records: List[ToolCallRecord] = []
        mid = self._extract_machine_id(query) or 3  # default to Machine 3 if ambiguous

        # ── Route 1: "Why is Machine X failing?" / Anomaly / Explain ───
        if any(w in q_lower for w in ["why", "failing", "degraded", "cause", "explain", "reason", "abnormal"]):
            # 1. get_machine_health
            h_res = tool_get_machine_health(mid)
            tool_records.append(ToolCallRecord("get_machine_health", {"machine_id": mid}, h_res))

            # 2. explain_prediction (SHAP)
            shap_res = tool_explain_prediction(mid)
            tool_records.append(ToolCallRecord("explain_prediction", {"machine_id": mid}, shap_res))

            # 3. find_similar_incidents
            sim_res = tool_find_similar_incidents(f"Machine {mid} failure pressure and temperature degradation", top_k=2)
            tool_records.append(ToolCallRecord("find_similar_incidents", {"query": f"Machine {mid} symptoms", "top_k": 2}, sim_res))

            # Synthesize answer
            m_name = h_res.get("name", f"Machine {mid}")
            health = h_res.get("health_score", 0)
            status = h_res.get("status", "unknown")
            rul = shap_res.get("rul_predicted", 0)
            top_features = shap_res.get("top_feature_drivers", [])

            feat_str = ", ".join([f"`{f.get('feature', 'sensor')}` (impact: {f.get('impact', 0):+.1f} cyc)" for f in top_features[:3]]) or "sensor telemetry channels"

            history_note = ""
            if sim_res.get("matches"):
                top_match = sim_res["matches"][0]
                history_note = (
                    f"\n\n**Historical Precedent (FAISS Memory Match: {top_match.get('similarity_score', 0)*100:.1f}% confidence)**:\n"
                    f"- In incident #{top_match.get('incident_id')}, {top_match.get('description')}\n"
                    f"- **Resolution Taken**: {top_match.get('resolution_notes', 'Standard overhaul.')}"
                )

            answer = (
                f"### Diagnostic Assessment: {m_name} (Machine {mid})\n\n"
                f"- **Current Operational Status**: `{status.upper()}` with Health Score of **{health}%**.\n"
                f"- **Predicted RUL**: **{rul:.1f} cycles/hours** before functional breakdown.\n"
                f"- **Root Cause (SHAP Explainability)**: The primary contributors driving RUL reduction are {feat_str}.\n"
                f"- **Physical Interpretation**: Divergence in compressor outlet pressure and core speed indicates progressive mechanical wear and seal degradation."
                f"{history_note}\n\n"
                f"**Recommended Action**: Initiate proactive maintenance within 48 hours or throttle machine speed by 20% to avoid catastrophic breakdown."
            )
            return answer, tool_records

        # ── Route 2: What-if / Simulation ("What if I shut down Machine X?") ─
        if any(w in q_lower for w in ["what if", "simulate", "shut down", "shutdown", "throttle", "reduce speed"]):
            scen_type = "shutdown" if "shut" in q_lower else "throttle_speed"
            sim_res = tool_run_simulation(scen_type, mid, sim_hours=168.0)
            tool_records.append(ToolCallRecord("run_simulation", {"scenario_type": scen_type, "machine_id": mid, "sim_hours": 168.0}, sim_res))

            net_sav = sim_res.get("net_savings_inr", 0)
            prod_delta = sim_res.get("production_delta_units", 0)
            dt_avoided = sim_res.get("downtime_avoided_hours", 0)

            sav_text = f"saves **₹{net_sav:,.0f}**" if net_sav >= 0 else f"costs an additional **₹{abs(net_sav):,.0f}**"

            answer = (
                f"### What-If Simulation Results (SimPy 168-Hour Horizon)\n\n"
                f"I simulated a **{scen_type.replace('_', ' ').title()}** on **Machine {mid}** across the 6-machine production line:\n\n"
                f"- **Financial Impact**: The scenario {sav_text} compared to business-as-usual baseline.\n"
                f"- **Unplanned Downtime Avoided**: **{dt_avoided:.1f} hours** of emergency breakdown prevented.\n"
                f"- **Production Delta**: **{prod_delta:+.0f} units** across the weekly operating schedule.\n\n"
                f"**Operational Verdict**: {sim_res.get('roi_summary', 'Scenario execution completed.')}"
            )
            return answer, tool_records

        # ── Route 3: Past Incidents / Memory ("What happened last time?") ───
        if any(w in q_lower for w in ["last time", "history", "similar", "past", "memory", "incident", "pattern"]):
            sim_res = tool_find_similar_incidents(query, top_k=3)
            tool_records.append(ToolCallRecord("find_similar_incidents", {"query": query, "top_k": 3}, sim_res))

            matches = sim_res.get("matches", [])
            if not matches:
                return "No matching historical incidents found in FAISS vector memory.", tool_records

            items = []
            for i, m in enumerate(matches, 1):
                items.append(
                    f"**{i}. {m.get('machine_name')} — Incident #{m.get('incident_id')} ({m.get('similarity_score', 0)*100:.1f}% match)**\n"
                    f"- *Description*: {m.get('description')}\n"
                    f"- *Action Taken*: `{m.get('action_taken', 'N/A')}`\n"
                    f"- *Resolution*: {m.get('resolution_notes', 'Closed.')}\n"
                )

            answer = (
                f"### Historical Incidents (Retrieved via FAISS Semantic Search)\n\n"
                f"Here are the closest historical occurrences matching your query:\n\n"
                + "\n".join(items)
            )
            return answer, tool_records

        # ── Route 4: Business Impact / Cost / Exposure ─────────────────────
        if any(w in q_lower for w in ["cost", "impact", "money", "rupee", "inr", "financial", "exposure", "loss"]):
            target_id = mid if "machine" in q_lower or mid != 3 else 0
            biz_res = tool_get_business_impact(target_id)
            tool_records.append(ToolCallRecord("get_business_impact", {"machine_id": target_id}, biz_res))

            if target_id == 0:
                total_exp = biz_res.get("fleet_total_daily_exposure_inr", 0)
                worst_m = biz_res.get("worst_machine", "None")
                crit_m = ", ".join(biz_res.get("critical_machines", [])) or "None"
                answer = (
                    f"### Factory-Wide Financial Impact Summary\n\n"
                    f"- **Total Daily Exposure**: **₹{total_exp:,.0f}** across all 6 machines.\n"
                    f"- **Monthly Pro-Rata Projection**: **₹{total_exp * 30:,.0f}**.\n"
                    f"- **Critical Machines**: {crit_m}.\n"
                    f"- **Highest Financial Risk Asset**: **{worst_m}** (₹{biz_res.get('worst_machine_exposure_inr', 0):,.0f}/day).\n\n"
                    f"**Cost Breakdown**:\n"
                    f"- Downtime Risk: ₹{biz_res.get('breakdown', {}).get('downtime_risk_inr', 0):,.0f}\n"
                    f"- Delay Penalties: ₹{biz_res.get('breakdown', {}).get('delay_penalty_inr', 0):,.0f}\n"
                    f"- Energy Waste: ₹{biz_res.get('breakdown', {}).get('energy_waste_inr', 0):,.0f}"
                )
            else:
                total_exp = biz_res.get("total_daily_exposure_inr", 0)
                savings = biz_res.get("planned_maintenance_savings_inr", 0)
                answer = (
                    f"### Financial Risk Report: {biz_res.get('name', f'Machine {mid}')}\n\n"
                    f"- **Total Daily Financial Exposure**: **₹{total_exp:,.0f}**.\n"
                    f"- **Downtime Failure Risk**: ₹{biz_res.get('downtime_risk_inr', 0):,.0f}.\n"
                    f"- **Daily Energy Waste**: ₹{biz_res.get('daily_energy_waste_inr', 0):,.0f}.\n"
                    f"- **Potential Savings by Planning**: You will save **₹{savings:,.0f}** by scheduling preventive maintenance now vs reactive emergency repair.\n\n"
                    f"**Recommendation**: {biz_res.get('recommendation', 'Inspect asset.')}"
                )
            return answer, tool_records

        # ── Route 5: General Machine Health & RUL Query ────────────────────
        rul_res = tool_get_rul(mid)
        tool_records.append(ToolCallRecord("get_rul", {"machine_id": mid}, rul_res))

        answer = (
            f"### Status Overview: {rul_res.get('name', f'Machine {mid}')}\n\n"
            f"- **Predicted RUL**: **{rul_res.get('rul_predicted_cycles', 0):.1f} cycles**.\n"
            f"- **Health Score**: **{rul_res.get('health_score', 0)}%**.\n"
            f"- **Failure Probability**: **{rul_res.get('failure_probability', 0)*100:.1f}%**.\n"
            f"- **Alert Status**: `{rul_res.get('alert_level', 'normal').upper()}`.\n\n"
            f"Ask me: *'Why is it failing?'*, *'What if I shut it down?'*, or *'What is the financial impact?'* for deeper insights."
        )
        return answer, tool_records


# ── Live OpenAI Client Handler ────────────────────────────────────────

class FactoryGPTService:
    """
    Main Factory GPT service. Dispatches to live OpenAI API if configured,
    or falls back to the deterministic LocalReActEngine.
    """

    def __init__(self) -> None:
        self.settings = get_settings()
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        self.local_engine = LocalReActEngine()

    def ask(self, query: str, conversation_history: Optional[List[Dict[str, str]]] = None) -> ChatMessage:
        """
        Executes query with tool calling and returns a typed ChatMessage.
        """
        # If API key is present and valid, attempt OpenAI tool calling
        if self.api_key and self.api_key.startswith("sk-"):
            try:
                return self._ask_openai(query, conversation_history)
            except Exception as e:
                print(f"⚠️ OpenAI API error: {e}. Falling back to Local ReAct Engine...")

        # Autonomous local engine
        content, tool_records = self.local_engine.respond(query)
        return ChatMessage(role="assistant", content=content, tool_calls=tool_records)

    def _ask_openai(self, query: str, history: Optional[List[Dict[str, str]]] = None) -> ChatMessage:
        from openai import OpenAI
        client = OpenAI(api_key=self.api_key)

        system_prompt = (
            "You are Factory GPT, the AI asset reliability assistant for the AI Factory Operating System. "
            "You have access to 6 live manufacturing machines simulated from NASA C-MAPSS engine telemetry. "
            "CRITICAL INVARIANT: You NEVER compute numbers yourself. You MUST ALWAYS call the backend tools "
            "to fetch telemetry, RUL, SHAP values, similar incidents, simulation results, or business financial calculations. "
            "Explain all tool outputs in simple, professional engineering language."
        )

        messages = [{"role": "system", "content": system_prompt}]
        if history:
            for h in history[-4:]:
                messages.append({"role": h["role"], "content": h["content"]})
        messages.append({"role": "user", "content": query})

        # 1. First model call with tools
        response = client.chat.completions.create(
            model=self.settings.llm.model or "gpt-4o-mini",
            messages=messages,
            tools=OPENAI_TOOLS,
            tool_choice="auto",
            temperature=0.2,
        )

        msg = response.choices[0].message
        tool_records: List[ToolCallRecord] = []

        if msg.tool_calls:
            messages.append(msg)
            for tc in msg.tool_calls:
                fn_name = tc.function.name
                args = json.loads(tc.function.arguments) if tc.function.arguments else {}

                if fn_name in TOOL_REGISTRY:
                    result = TOOL_REGISTRY[fn_name](**args)
                else:
                    result = {"error": f"Tool {fn_name} not found."}

                tool_records.append(ToolCallRecord(tool_name=fn_name, arguments=args, result=result))

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "name": fn_name,
                    "content": json.dumps(result),
                })

            # 2. Final synthesis call
            final_resp = client.chat.completions.create(
                model=self.settings.llm.model or "gpt-4o-mini",
                messages=messages,
                temperature=0.2,
            )
            final_content = final_resp.choices[0].message.content or "Completed."
            return ChatMessage(role="assistant", content=final_content, tool_calls=tool_records)

        return ChatMessage(role="assistant", content=msg.content or "", tool_calls=[])


# Singleton instance
_factory_gpt_instance: Optional[FactoryGPTService] = None


def get_factory_gpt() -> FactoryGPTService:
    global _factory_gpt_instance
    if _factory_gpt_instance is None:
        _factory_gpt_instance = FactoryGPTService()
    return _factory_gpt_instance

