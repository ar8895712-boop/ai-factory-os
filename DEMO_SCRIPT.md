# ==============================================================
# AI Factory Operating System — 5-Minute Viva Demonstration Script
# ==============================================================

> **Project Title**: AI Factory Operating System: Predictive Maintenance Digital-Twin Platform  
> **Student Persona**: Final-Year B.Tech Computer Science / AI & ML Student  
> **Target Audience**: External Viva Examiners, Project Review Committee, Industry Evaluators  
> **Target Duration**: Exactly 5 Minutes (+ 5 Minutes Q&A)  
> **Golden Rule**: Never guess. Speak with mathematical confidence, point to exact UI metrics, and let the live system demonstrate zero-leakage ML and deterministic calculations.

---

## ⏱️ Timeline Overview

| Time | Segment | Screen / Action | Key Takeaway |
|---|---|---|---|
| **0:00 – 1:00** | Introduction & Problem Context | Slides / Architecture | Shift from reactive repairs to predictive digital twin |
| **1:00 – 2:00** | Digital Twin & Edge ML Inference | Factory Overview & Machine Detail | Real-time RUL, Failure Prob, Isolation Forest, SHAP |
| **2:00 – 3:00** | Business Impact & Self-Healing | Business Impact Page | ₹ Downtime Risk + Cost-minimizing mitigation |
| **3:00 – 4:00** | SimPy Discrete-Event What-If | What-If Simulator Page | 72h baseline breakdown vs proactive shutdown ROI |
| **4:00 – 5:00** | Factory GPT & Vector Incident Memory | Factory GPT Page | Autonomous ReAct loop, 0 hallucinated numbers |

---

## 🎬 Minute-by-Minute Walkthrough

### 🕒 Minute 1 (0:00 – 1:00): Problem Statement & Architecture

**What to do**:
- Open the application in the browser at `http://localhost:5173` (or show the running terminal with FastAPI and React).
- Keep the **Factory Overview** screen visible.

**What to say**:
> *"Good morning, respected professors and external examiners.*
>
> *Traditional manufacturing plants lose millions of rupees each year to unexpected equipment breakdowns. Today, most factories rely either on **reactive maintenance**—fixing things only after they break—or **calendar-based maintenance**, which replaces expensive components prematurely.*
>
> *I have built the **AI Factory Operating System**, an end-to-end predictive maintenance digital twin that monitors a 6-machine shop floor in real time. It continuously tracks 15 physical sensor channels, predicts Remaining Useful Life (RUL) with sub-15 RMSE, converts raw telemetry into financial exposure in Indian Rupees (₹), runs discrete-event What-If simulations to test operational decisions, and provides an offline-first conversational AI agent that never hallucinates numbers.*
>
> *Let us observe the live digital twin in action."*

---

### 🕒 Minute 2 (1:00 – 2:00): Digital Twin Floor & Multi-Model Inference

**What to do**:
1. Point to the **Factory Overview** grid showing 6 machines (`CNC-01`, `Pump-02`, `Compressor-03`, `Turbine-04`, `Conveyor-05`, `Grinder-06`).
2. Click on **CNC-01** to open its **Machine Detail** view.
3. In the cycle jumper input, enter `150` and click **"Jump to Cycle"** (or use the speed slider to set `2.0x`).
4. Point to the live Recharts telemetry, the RUL gauge, and the SHAP feature importance chart.

**What to say**:
> *"Here on the Factory Overview, each machine replays an unseen degradation trajectory from NASA's C-MAPSS FD001 engine benchmark. Crucially, to prevent data leakage, these 6 engines were strictly isolated into a **DEMO-HOLDOUT** set prior to training—our models never saw these trajectories during feature scaling or model optimization.*
>
> *When I jump CNC-01 to Cycle 150, look at how the ensemble responds:*
> 1. *Our PyTorch 1D-CNN and LSTM ensemble detects thermal-acoustic wear, dropping the predicted Remaining Useful Life to under 30 cycles.*
> 2. *Our XGBoost classifier (trained with `scale_pos_weight=28.54` to counter severe class imbalance) detects a 78% failure probability.*
> 3. *Our Isolation Forest flags sensor multidimensional anomalies.*
> 4. *Below, the **TreeSHAP attribution bar chart** explains the root cause in real time: sensor `s11` (Static Pressure) and sensor `s4` (LPT Exit Temperature) account for 68% of the negative degradation weight.*
>
> *The machine health score transitions from Green (Healthy) to Red (Critical)."*

---

### 🕒 Minute 3 (2:00 – 3:00): Real-Time Business Impact & Self-Healing Decision

**What to do**:
1. Click the **"Business Impact"** tab in the top navigation bar.
2. Select **CNC-01** (or view the Fleet Financial Summary).
3. Point to the ₹ cost breakdown tiles: Downtime Risk, Energy Waste, Delay Penalty.
4. Click **"Evaluate Self-Healing"**.

**What to say**:
> *"A machine alert alone is not enough for plant managers; decision-makers need financial numbers in Indian Rupees (₹). Our Business Impact engine translates raw ML probabilities into actionable economics using parameters defined in `config.yaml`:*
>
> $$\text{Downtime Risk} = P(\text{Failure}) \times \text{Hours to Failure} \times \text{Loss per Hour (₹)}$$
>
> *For CNC-01, current exposure is ₹3,75,000. Additionally, thermal degradation causes parasitic power loss, adding ₹12,400 per day in wasted energy tariffs.*
>
> *When I click **Evaluate Self-Healing**, our cost-aware decision engine evaluates four candidate interventions:*
> - *Option A: Speed reduction (20% throttle) → Costs ₹45,000 in lost throughput.*
> - *Option B: Shift workload to healthy peer Pump-02 → Costs ₹15,000 in setup.*
> - *Option C: Technician emergency callout → Costs ₹65,000.*
> - *Option D: Planned maintenance window → Saves ₹1,10,000 compared to catastrophic repair.*
>
> *The engine autonomously recommends **Shift Workload**, achieving the minimum expected total cost."*

---

### 🕒 Minute 4 (3:00 – 4:00): SimPy Discrete-Event What-If Scenario Simulator

**What to do**:
1. Navigate to the **"What-If Simulator"** tab.
2. Select the pre-configured template: **"Proactive Maintenance Shutdown (Machine 1)"**.
3. Keep the simulation horizon at **72 Hours**.
4. Click **"Run Simulation"**.
5. Point to the comparative trajectory graph and the Delta Metrics cards.

**What to say**:
> *"Before stopping a production line, the plant manager asks: 'What happens if we shut down CNC-01 for 6 hours of maintenance versus letting it run?'*
>
> *To answer this without guessing, I integrated **SimPy**, a discrete-event simulation engine in Python. It models stochastic order arrivals, finite machine resource queues, and ML RUL feedback as Time-To-Failure (TTF).*
>
> *In just 200 milliseconds, SimPy simulates both futures across a 72-hour horizon:*
> - *The **Baseline (red line)** experiences an unmanaged catastrophic failure at hour 28, causing 18 hours of unplanned downtime, emergency spare markups, and ₹4,20,000 in total loss.*
> - *The **Scenario (blue line)** schedules a proactive 6-hour planned shutdown at hour 10.*
> - *The comparison is definitive: **12 hours of downtime avoided, ₹2,85,000 net savings in ₹, and an ROI of 312%**.*
>
> *All simulation parameters are audited and persisted directly into SQLite for historical review."*

---

### 🕒 Minute 5 (4:00 – 5:00): Factory GPT Assistant & Vector Incident Memory

**What to do**:
1. Click the **"Factory GPT"** tab.
2. Click the quick prompt pill: *"Why is Machine 1 degrading and what is the financial risk in INR?"* (or type it into the input box and hit Enter).
3. Expand the **Tool Execution Drawer** (`get_machine_health`, `get_business_impact`, `find_similar_incidents`).
4. Point out the exact matching numbers between the tool JSON output and the assistant's written answer.

**What to say**:
> *"Finally, we present **Factory GPT**, our natural language maintenance copilot. In enterprise industrial AI, an LLM must **never compute numbers**—Large Language Models hallucinate arithmetic.*
>
> *Instead, our architecture enforces a strict **ReAct (Reason + Act)** tool-calling pattern:*
> 1. *Factory GPT inspects the operator's prompt.*
> 2. *It calls registered deterministic backend tools: `get_machine_health`, `get_business_impact`, and `find_similar_incidents`.*
> 3. *It searches our **Vector Incident Memory**, which maps failure symptoms to 384-dimensional dense semantic vectors using an offline-first normalized projection index, retrieving past incidents with similar high-vibration and exhaust temperature patterns.*
> 4. *The assistant synthesizes the answer, citing verified numbers from the Python backend.*
>
> *The entire system runs **100% locally and offline** on standard laptop hardware—zero cloud latency, zero external API costs, and total data privacy for factory floor telemetry.*
>
> *Respected examiners, the complete test suite is verified with **79 passing automated tests** across all 7 project phases. I am now ready for your questions."*

---

## 🛡️ Emergency Contingency Playbook

| Scenario | What to do | What to say |
|---|---|---|
| **Examiner asks: "What if there is no internet connection?"** | Disconnect Wi-Fi on laptop live. | *"Our entire system is designed offline-first. The PyTorch models, XGBoost, SQLite DB, SimPy simulator, React bundle, and Local ReAct assistant operate entirely offline without network access."* |
| **Examiner asks: "Did your model overfit on training data?"** | Open `tests/test_leakage.py` or run `pytest tests/test_leakage.py`. | *"We enforced engine-level splitting (70/15/15) rather than random row splitting. All scalers were fitted strictly on training engines. Our 4 automated leakage tests verify that zero holdout engines exist in the training set."* |
| **Examiner asks: "Can you change the loss per hour assumption?"** | Go to `config.yaml` or UI Config modal, change `loss_per_hour` from `100000` to `150000`. | *"All business assumptions live in `config.yaml` and reload dynamically. The business impact formulas automatically re-evaluate with zero code modifications."* |
| **Examiner asks: "Show me the test suite right now."** | Run `C:\Python314\python.exe -m pytest tests/ -v` in terminal. | *"Here is the complete test suite: 79 unit, integration, and E2E tests passing in under 20 seconds."* |

