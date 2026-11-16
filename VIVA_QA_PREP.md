# ==============================================================
# AI Factory Operating System — 20 High-Probability Viva Q&A Guide
# ==============================================================

> **Author**: B.Tech Final Year Capstone Team  
> **Topic**: Predictive Maintenance Digital-Twin Platform with Edge ML & Agentic AI  
> **How to use this guide**:  
> Each question contains:  
> 1. **15-Second Crisp Answer** (memorize this for immediate confidence).  
> 2. **Deep Technical & Mathematical Justification** (equations, architectural trade-offs, algorithms).  
> 3. **Exact Code Reference** (files, functions, and automated tests to show examiners).

---

### Q1: Why did you split your data by Engine ID rather than random row-level k-fold cross-validation?

**15-Second Crisp Answer**:  
Random row splitting causes catastrophic **temporal data leakage**. Because degradation is a continuous time-series, consecutive cycles of the same engine share identical baseline wear. Splitting by rows puts cycle $t$ in train and $t+1$ in test, artificially inflating accuracy to ~99% while failing completely on new machines. We split by complete engine trajectories (70/15/15).

**Deep Technical Justification**:  
In industrial condition monitoring, readings from engine $i$ at cycle $t$ and cycle $t+1$ are highly autocorrelated ($\text{corr}(s_t, s_{t+1}) > 0.95$). If random row splitting is applied:
1. Feature scalers learn the specific min/max sensor envelopes of the test engines.
2. The model memorizes unit-specific calibration offsets rather than learning generalized wear dynamics.
3. In this project, we partitioned the 100 C-MAPSS engines into 70 train engines (IDs 1–70), 15 validation engines (IDs 71–85), and 15 strictly isolated DEMO-HOLDOUT engines (IDs 86–100, plus specific test holdouts like engines 3, 15, 21, 22, 24, 52). Scalers were fitted *only* on the training partition.

**Code Reference**:  
- `ml/data_loader.py` -> `create_engine_splits()`
- `tests/test_leakage.py` -> `test_zero_engine_leakage()`

---

### Q2: Why use asymmetric NASA scoring function / RMSE for RUL rather than standard MAE?

**15-Second Crisp Answer**:  
In industrial maintenance, late predictions are fatal while early predictions are acceptable. Predicting RUL $+10$ when the machine has only $2$ cycles left causes catastrophic physical failure. The NASA scoring function penalizes late predictions exponentially harder than early ones ($e^{d/10}-1$ vs $e^{-d/13}-1$).

**Deep Technical Justification**:  
Standard Mean Absolute Error ($\text{MAE} = \frac{1}{N}\sum |y - \hat{y}|$) is symmetric: an error of $+10$ cycles carries the exact same penalty as $-10$ cycles. In a physical turbine:
- $\hat{y} - y = -10$ (Early prediction): Maintenance happens 10 cycles early. Cost: minor remaining life sacrifice.
- $\hat{y} - y = +10$ (Late prediction): Machine breaks down in service. Cost: catastrophic damage, flying debris, safety hazards, emergency shutdown.

The NASA C-MAPSS scoring metric is defined as:
$$S = \sum_{i=1}^{N} s_i, \quad s_i = \begin{cases} e^{-\frac{d_i}{13}} - 1, & d_i < 0 \text{ (Early)} \\ e^{\frac{d_i}{10}} - 1, & d_i \ge 0 \text{ (Late)} \end{cases}$$
where $d_i = \hat{y}_i - y_i$. For optimization stability in PyTorch and XGBoost, we minimize RMSE as a surrogate loss and validate against both RMSE and the asymmetric NASA score.

**Code Reference**:  
- `ml/train_rul.py` -> `compute_nasa_score()`
- `data/evaluation_table.md` -> Model Comparison Table

---

### Q3: How did you handle severe class imbalance in the AI4I maintenance dataset?

**15-Second Crisp Answer**:  
The AI4I dataset has only 339 failure events out of 10,000 records (~3.4% failure rate). A naive classifier predicting "No Failure" achieves 96.6% accuracy but catches 0 breakdowns. We handled this by setting `scale_pos_weight = 28.54` in XGBoost and optimizing for PR-AUC and F1-score rather than accuracy.

**Deep Technical Justification**:  
The scale positive weight parameter is computed directly as:
$$\text{scale\_pos\_weight} = \frac{N_{\text{negative}}}{N_{\text{positive}}} = \frac{9661}{339} \approx 28.54$$
This scales the gradient of the loss function for positive (failure) instances by $28.54\times$, forcing the boosting trees to heavily penalize False Negatives (missed failures). In evaluation, we tracked:
- Precision-Recall AUC (PR-AUC): $0.841$
- Recall on Failure Class: $> 91\%$
- Receiver Operating Characteristic (ROC-AUC): $0.942$

**Code Reference**:  
- `ml/train_failure.py` -> `train_xgboost_failure_classifier()`
- `tests/test_leakage.py` -> `test_class_balance_and_scaling()`

---

### Q4: What is your sliding window size, and how do you handle early cycles before cycle 30?

**15-Second Crisp Answer**:  
We use a sliding window of **30 cycles** ($W = 30$) across 14 useful sensor channels. For early cycles ($t < 30$), we apply **left zero-padding (or forward replicate edge padding)** so that feature matrix dimensions remain constant at $(30, 14)$ from cycle 1 without discarding initial runtime.

**Deep Technical Justification**:  
Industrial degradation patterns such as temperature drift and vibration harmonics manifest across multi-step sequences rather than single snapshots. 
- Input tensor shape: $(B, 30, 14)$ where $B$ is batch size, $30$ is historical time steps, and $14$ is sensor channels.
- When an engine starts at cycle $t=5$, a window requiring 30 steps would fail if unhandled.
- We implement edge padding: the earliest observed reading is prepended $25$ times to form the initial window:
  $$X_{\text{padded}} = [\underbrace{x_1, x_1, \dots, x_1}_{30 - t \text{ times}}, x_1, x_2, \dots, x_t]$$
This guarantees the digital twin can perform inference on freshly commissioned machines immediately without waiting 30 cycles.

**Code Reference**:  
- `ml/data_loader.py` -> `create_sliding_windows()`
- `backend/ml/inference.py` -> `pad_sequence_window()`

---

### Q5: Why combine CNN and LSTM models, and how do their feature extraction mechanisms differ?

**15-Second Crisp Answer**:  
**1D-CNN** acts as a multi-channel spatial filter that extracts local sensor correlations (e.g. pressure spikes coinciding with temperature jumps). **LSTM** captures long-range temporal trends and cumulative degradation trajectories across the 30-cycle horizon. Combining both leverages both high-frequency localized anomalies and low-frequency monotonic degradation.

**Deep Technical Justification**:  
- **1D-CNN**: Applies 1D convolution kernels of sizes 3 and 5 across the temporal dimension. It computes:
  $$y_k = \text{ReLU}\left(\sum_{c=1}^{C} W_c * x_c + b\right)$$
  This is translation-invariant and detects instantaneous operational stress signatures across adjacent cycles.
- **LSTM**: Uses gating mechanisms (input $i_t$, forget $f_t$, output $o_t$, cell state $C_t$) to maintain an internal degradation memory state:
  $$f_t = \sigma(W_f [h_{t-1}, x_t] + b_f), \quad C_t = f_t \odot C_{t-1} + i_t \odot \tilde{C}_t$$
  The forget gate explicitly models component wear: once a baseline sensor drift occurs, the cell state retains this information across all future steps.

**Code Reference**:  
- `ml/models.py` -> `CNNRULModel`, `LSTMRULModel`
- `tests/test_leakage.py` -> `test_model_architectures()`

---

### Q6: How is the composite Health Score mathematically formulated, and why combine linear and harmonic means?

**15-Second Crisp Answer**:  
Health Score $H \in [0, 100]$ combines RUL, Failure Probability, and Anomaly Score. We use a **hybrid blend**: a weighted linear base modulated by a **harmonic penalty**. If any single sensor undergoes severe failure, harmonic averaging drags the composite score down instantly, preventing a healthy RUL from masking an acute vibration burst.

**Deep Technical Justification**:  
The health score formula is:
$$H_{\text{linear}} = w_1 \cdot \left(\frac{\min(\text{RUL}, 125)}{125} \times 100\right) + w_2 \cdot (1 - P_{\text{fail}}) \times 100 + w_3 \cdot (1 - S_{\text{anomaly}}) \times 100$$
where $w_1 = 0.45, w_2 = 0.35, w_3 = 0.20$.  
However, linear weighting suffers from the **compensation flaw**: a machine with $P_{\text{fail}} = 0.99$ could still retain a score of $65$ if RUL is high.  
Therefore, we apply a safety penalty function:
$$H_{\text{final}} = \min\left(H_{\text{linear}}, 100 \times (1 - P_{\text{fail}})^{1.5}\right)$$
This guarantees that whenever $P_{\text{fail}} > 0.70$, $H$ is guaranteed to fall into the **Critical (< 40)** range regardless of RUL.

**Code Reference**:  
- `backend/simulation/engine.py` -> `compute_health_score()`
- `tests/test_health_score.py` -> `test_health_score_bounds_and_edge_cases()`

---

### Q7: What is TreeSHAP, and how does it compute exact Shapley feature attributions in real time?

**15-Second Crisp Answer**:  
TreeSHAP is an algorithmic formulation of cooperative game theory Shapley values optimized for decision trees. It computes the exact conditional expectation of each sensor's contribution to the failure prediction in polynomial time $O(T L D^2)$, allowing our digital twin to produce millisecond-level root cause explanations.

**Deep Technical Justification**:  
Classical KernelSHAP requires exponential time $O(M 2^{|F|})$ by perturbing feature subsets. TreeSHAP exploits the internal tree structure of XGBoost:
$$\phi_i = \sum_{S \subseteq F \setminus \{i\}} \frac{|S|!(|F| - |S| - 1)!}{|F|!} \left[f(S \cup \{i\}) - f(S)\right]$$
TreeSHAP evaluates all subtrees simultaneously by keeping track of the proportion of training paths that fall into each leaf. The resulting $\phi_i$ values satisfy:
1. **Efficiency**: $\sum_{i=1}^{M} \phi_i = f(x) - \mathbb{E}[f(x)]$ (the sum of feature contributions equals the deviation from baseline expectation).
2. **Local Accuracy**: The top positive SHAP features pinpoint the exact sensors pushing the machine into failure (e.g. `s11` High Pressure Compressor static pressure).

**Code Reference**:  
- `ml/explainability.py` -> `TreeSHAPExplainer`
- `backend/ml/inference.py` -> `explain_prediction()`

---

### Q8: Why did you choose SimPy for What-If simulation instead of purely static queuing formulas?

**15-Second Crisp Answer**:  
Static formulas (like $M/M/1$ queues) assume steady-state averages and Poisson distributions. Manufacturing floors operate under **transient, non-stationary conditions**: machines degrade dynamically, maintenance crews have finite shifts, and downstream queues overflow. SimPy models exact state-dependent discrete event interactions across time.

**Deep Technical Justification**:  
SimPy is a process-based discrete-event simulation framework. In our `SimPyFactoryModel`:
1. Each machine is modeled as a SimPy `Resource(capacity=1)`.
2. Job arrivals represent production orders flowing between Shop Floor A and Assembly.
3. Degradation is dynamic: every operating hour consumes RUL. Time-To-Failure (TTF) is derived dynamically from our ML inference engine.
4. When a machine breaks down, it preempts the current job, releases the tool, and requests a `MaintenanceTechnician` resource. If all technicians are occupied, queueing delay builds up realistically.
This allows evaluating complex cascading effects—such as shifting load from Machine 1 to Machine 2 causing Machine 2 to degrade $40\%$ faster—which analytical formulas cannot capture.

**Code Reference**:  
- `backend/simulation/whatif.py` -> `SimPyFactoryModel`
- `tests/test_whatif.py` -> `test_simpy_baseline_and_scenario_events()`

---

### Q9: What is the exact mathematical formulation of Downtime Risk and Self-Healing Optimization?

**15-Second Crisp Answer**:  
Downtime risk is the expected monetary loss: $P(\text{fail}) \times \text{Hours to Failure} \times \text{Loss per Hour (₹)}$. The self-healing engine evaluates four candidate interventions ($A_k$), estimates their total implementation and residual failure costs in ₹, and autonomously selects:
$$A^* = \arg\min_{k} \left(C_{\text{action}}(A_k) + C_{\text{residual risk}}(A_k)\right)$$

**Deep Technical Justification**:  
The financial components are defined in `config.yaml` in Indian Rupees (₹):
1. **Unplanned Downtime Risk**:
   $$\text{Risk}_{\text{downtime}} = P_{\text{fail}} \times \left(\frac{\text{RUL}_{\text{cycles}}}{\text{rate}}\right) \times \text{LossPerHour}_{\text{INR}}$$
2. **Energy Waste**:
   $$\text{Waste}_{\text{energy}} = P_{\text{nominal}} \times \left(\frac{100 - H}{100} \times \eta_{\text{loss}}\right) \times 24 \times \text{Tariff}_{\text{INR/kWh}}$$
3. **Delay Penalty**:
   $$\text{Penalty}_{\text{delay}} = \max\left(0, \text{Target}_{\text{units}} - \text{Actual}_{\text{units}}\right) \times \text{PenaltyPerUnit}_{\text{INR}}$$
4. **Self-Healing Selection**:
   - `reduce_speed`: $C = \text{Lost Throughput} - \text{Extended Life Benefit}$
   - `shift_load`: $C = \text{Setup Cost} + \text{Peer Wear Increment}$
   - `schedule_maintenance`: $C = \text{Planned Maintenance Cost} \ll \text{Emergency Repair Cost}$

**Code Reference**:  
- `backend/services/business_impact.py` -> `BusinessImpactCalculator`
- `backend/services/self_healing.py` -> `SelfHealingEngine.evaluate()`
- `tests/test_business_impact.py` -> `test_cost_minimization()`

---

### Q10: How do you guarantee that the LLM (Factory GPT) does not hallucinate numbers?

**15-Second Crisp Answer**:  
We enforce a strict **Separation of Concerns**: the LLM has zero calculation authority. It operates strictly as a ReAct orchestrator. All mathematical calculations (health, RUL, ₹ costs, simulation deltas) are performed by deterministic Python functions. The LLM only receives structured JSON outputs and is forbidden by system prompt from computing numbers.

**Deep Technical Justification**:  
LLMs are autoregressive token predictors ($\arg\max P(w_t | w_{<t})$), not calculators. To eliminate hallucinations:
1. **Tool-Calling Architecture**: The LLM prompt binds 6 typed tools (`get_machine_health`, `get_rul`, `explain_prediction`, `find_similar_incidents`, `run_simulation`, `get_business_impact`).
2. **Local ReAct Engine**: In offline mode, regex and heuristic intent matchers route user queries directly to deterministic backend tools.
3. **Guardrails**: Our test suite (`test_factory_gpt.py`) validates that all numbers appearing in the assistant's dialogue match the tool execution JSON payload up to 2 decimal places. If an examiner asks *"Calculate 25 * 4000"*, the system does not guess—it calls the business impact calculator.

**Code Reference**:  
- `backend/services/factory_gpt.py` -> `LocalReActEngine`, `TOOL_REGISTRY`
- `tests/test_factory_gpt.py` -> `test_strict_number_invariant()`

---

### Q11: Explain your Vector Incident Memory. Why use cosine similarity on 384-d vectors over SQL `LIKE '%bearing%'`?

**15-Second Crisp Answer**:  
SQL `LIKE` requires exact keyword matches and fails when vocabulary differs (e.g. an operator reports "rotor friction" while the log says "bearing wear"). Our Vector Memory projects incident symptoms into a 384-dimensional semantic space, matching semantic meaning and failure physics using cosine similarity regardless of phrasing.

**Deep Technical Justification**:  
1. **Semantic Embeddings**: Sentences are mapped to vectors in $\mathbb{R}^{384}$. In offline mode, we implement a normalized semantic hash projection index that maps domain n-grams into a unit sphere:
   $$\vec{u} = \frac{\phi(text)}{\|\phi(text)\|_2}$$
2. **Cosine Similarity**:
   $$\text{Sim}(\vec{q}, \vec{d}) = \cos(\theta) = \frac{\vec{q} \cdot \vec{d}}{\|\vec{q}\|_2 \|\vec{d}\|_2} = \vec{q} \cdot \vec{d} \quad (\text{since } \|\vec{u}\| = 1)$$
3. **NumpyVectorIndex**: Because native FAISS binary wheels can suffer from C++ runtime incompatibilities across newer Python releases on Windows, we engineered an exact matrix dot product index ($Q \cdot M^T$) that computes exact inner-product nearest neighbors in sub-millisecond time with zero external DLL crashes.

**Code Reference**:  
- `backend/services/factory_memory.py` -> `NumpyVectorIndex`, `SemanticTextEmbedder`
- `tests/test_memory.py` -> `test_vector_similarity_search()`

---

### Q12: How does the system handle real-time concurrency between background simulation and user API requests?

**15-Second Crisp Answer**:  
We use **SQLite in WAL (Write-Ahead Logging) mode** with `check_same_thread=False` and separate session scopes. Read queries from the dashboard run concurrently with write queries from the digital twin simulation without database lock contention.

**Deep Technical Justification**:  
Standard SQLite in rollback journal mode locks the entire database file during a write, causing `sqlite3.OperationalError: database is locked` when multiple FastAPI worker threads access it.
In `backend/database.py`:
1. We execute `PRAGMA journal_mode=WAL;` at connection time. In WAL mode, writes are appended to a `-wal` file while readers access the main `.db` file simultaneously without blocking.
2. In-memory digital twin states are decoupled from disk: the simulation engine maintains a high-speed Python dictionary for real-time WebSocket broadcast, batching database flushes asynchronously.

**Code Reference**:  
- `backend/database.py` -> `_set_sqlite_pragma()`
- `backend/simulation/engine.py` -> `step_all()`

---

### Q13: What is the advantage of WebSockets over HTTP polling for digital twin telemetry?

**15-Second Crisp Answer**:  
HTTP polling incurs massive overhead: each request requires TCP handshakes, TLS negotiation, and HTTP headers (~800 bytes) every 500ms for 6 machines. **WebSockets establish a persistent, bidirectional TCP connection** with a 2-byte framing overhead, reducing network latency from ~80ms to < 2ms.

**Deep Technical Justification**:  
- **HTTP Polling**: 6 machines $\times$ 2 requests/sec = 12 HTTP requests/sec. At 1 KB per request/response header, that consumes ~100 Kbps of bandwidth per open browser tab and creates high CPU overhead in the ASGI event loop.
- **WebSocket Protocol (RFC 6455)**: After a single initial HTTP upgrade handshake, the connection remains open. The backend server pushes binary or JSON payloads only when state changes occur. Our `ConnectionManager` (`ws_hub`) broadcasts to all connected React clients concurrently using `asyncio.gather`.

**Code Reference**:  
- `backend/simulation/websocket_manager.py` -> `WebSocketHub`
- `backend/routers/websocket.py` -> `/ws/live`
- `frontend/src/context/WebSocketContext.jsx`

---

### Q14: How does Isolation Forest detect novel anomalies that the supervised classifier might miss?

**15-Second Crisp Answer**:  
Supervised models only recognize failure modes present in the training set (e.g. known tool wear). **Isolation Forest is unsupervised**: it isolates anomalies by randomly partitioning feature space with orthogonal hyperplanes. Rare and unusual sensor combinations require fewer splits and isolate near the root of the trees.

**Deep Technical Justification**:  
Given a dataset $X \in \mathbb{R}^{n \times d}$, an Isolation Tree recursively divides the space by selecting a random feature $q$ and split value $p \in [\min(q), \max(q)]$.
- Normal points cluster densely and require deep paths ($h(x) \gg \bar{h}$).
- Anomalous sensor spikes exist in sparse regions and isolate in very few splits ($h(x) \ll \bar{h}$).
The anomaly score is defined as:
$$s(x, n) = 2^{-\frac{\mathbb{E}(h(x))}{c(n)}}$$
where $c(n) = 2\ln(n - 1) + 0.5772 - \frac{2(n-1)}{n}$ is the average path length of unsuccessful searches in Binary Search Trees. If $s > 0.60$, the point is flagged as an anomaly, catching novel mechanical faults never seen during model training.

**Code Reference**:  
- `ml/train_anomaly.py` -> `train_isolation_forest()`
- `tests/test_leakage.py` -> `test_anomaly_detector()`

---

### Q15: In your self-healing engine, why isn't 'schedule_maintenance' always the best decision?

**15-Second Crisp Answer**:  
Planned maintenance takes the machine offline for 4 hours, causing direct production deficits and technician expenses. If a machine has a mild warning with 80 cycles of RUL remaining, **speed throttling (reducing speed by 20%)** extends RUL by 30% while preserving 80% throughput, yielding far lower total cost.

**Deep Technical Justification**:  
Self-healing is formulated as an optimization problem:
$$\min_{a \in \mathcal{A}} \text{TotalCost}(a) = \text{InterventionCost}(a) + \text{ProductionLoss}(a) + \text{ResidualRiskCost}(a)$$
- For `schedule_maintenance`:
  $$\text{Cost} = \text{TechnicianHours} \times \text{Rate} + \text{SpareCost} + (4 \text{ hrs} \times \text{LossPerHour}) \approx ₹1,80,000$$
- For `reduce_speed` (at health = 65):
  $$\text{Cost} = 0.20 \times \text{ProductionDeficit} \times \text{Margin} \approx ₹35,000$$
The rule engine evaluates machine health thresholds:
- $H \ge 60$ (Mild Warning): `reduce_speed` is optimal.
- $H < 40$ or $P_{\text{fail}} > 0.70$ (Severe Warning): `schedule_maintenance` or `shift_load` becomes mandatory to prevent catastrophic damage exceeding ₹5,00,000.

**Code Reference**:  
- `backend/services/self_healing.py` -> `_cost_reduce_speed()`, `_cost_schedule_maintenance()`

---

### Q16: How does your system operate 100% offline without sending factory data to OpenAI or external cloud servers?

**15-Second Crisp Answer**:  
Factory operational data contains proprietary production rates and trade secrets. We built an **Offline-First Local ReAct engine** and an in-memory normalized projection vector search index. All inferences—PyTorch RUL, XGBoost, Isolation Forest, SimPy, and NLP tool execution—run locally on CPU with zero outbound network calls.

**Deep Technical Justification**:  
1. **Model Weights**: PyTorch `.pt` state dictionaries, XGBoost `.json` models, and scikit-learn `.pkl` scalers reside locally in `data/models/`.
2. **Local ReAct Parser**: User natural language prompts are parsed by an intent classifier mapping regex and linguistic patterns to deterministic backend tool calls.
3. **Optional Cloud Hybrid**: While an OpenAI API client is implemented (`backend/services/factory_gpt.py`), the system automatically detects network availability: if offline or in sandbox mode, it falls back seamlessly to the local engine without failing or raising exceptions.

**Code Reference**:  
- `backend/services/factory_gpt.py` -> `LocalReActEngine`
- `tests/test_factory_gpt.py` -> `test_local_react_engine()`

---

### Q17: What is the fundamental difference between RUL (Remaining Useful Life) and MTTF (Mean Time To Failure)?

**15-Second Crisp Answer**:  
**MTTF** is a static, population-level statistical average (e.g. "this model fails after 5,000 hours on average"). **RUL** is a dynamic, machine-specific condition-based estimate of remaining cycles conditioned on that specific unit's actual past sensor stress and thermal history.

**Deep Technical Justification**:  
- **MTTF** comes from traditional reliability engineering (Weibull distributions):
  $$\text{MTTF} = \int_{0}^{\infty} R(t) dt$$
  It is identical for two brand-new machines, ignoring whether Machine A runs in a temperature-controlled room and Machine B runs at 100% load in a hot foundry.
- **RUL** is a conditional expectation:
  $$\text{RUL}(t) = \mathbb{E}[T_{\text{failure}} - t \mid X_{1:t}]$$
  where $X_{1:t}$ is the exact time-series telemetry observed for this unique asset. If an operator throttles the machine, RUL immediately recalculates upwards.

**Code Reference**:  
- `ml/train_rul.py`
- `backend/simulation/engine.py` -> `step_machine()`

---

### Q18: How does your system prevent catastrophic failure during high-speed production spikes?

**15-Second Crisp Answer**:  
The digital twin engine continuously computes the **rate of health degradation** ($\Delta H / \Delta t$). If the rate of degradation exceeds safe thresholds, the autonomous self-healing engine overrides operator speed settings, dynamically throttling the machine down to 0.5x or shifting incoming orders to a peer machine.

**Deep Technical Justification**:  
High-speed production increases thermal and mechanical friction non-linearly ($Q \propto v^2$). In `backend/services/self_healing.py`:
1. The engine checks current speed multiplier ($S$) and failure risk ($P_{\text{fail}}$).
2. When $P_{\text{fail}} > 0.60$ and $S > 1.0$, the rule engine triggers an emergency governor action:
   $$\text{speed\_factor} = \max\left(0.5, \text{speed\_factor} \times 0.80\right)$$
3. It broadcasts an urgent WebSocket notification to the React dashboard, alerting floor technicians before high-speed thermal runaway occurs.

**Code Reference**:  
- `backend/simulation/engine.py` -> `set_speed()`
- `backend/services/self_healing.py` -> `ActionOption`

---

### Q19: What database schema design choices ensure historical sensor readings don't degrade query performance?

**15-Second Crisp Answer**:  
We implemented **composite B-Tree indexes** on `(machine_id, timestamp)` and `(machine_id, cycle)`, avoided storing redundant raw arrays in the parent machine table, and separated operational telemetry (`readings`) from high-level events (`incidents`).

**Deep Technical Justification**:  
In high-frequency IoT streaming:
1. Table `readings` accumulates thousands of rows per hour. A query like `SELECT * FROM readings WHERE machine_id=1 ORDER BY timestamp DESC LIMIT 50` would cause full table scans ($O(N)$) without indexes.
2. In `backend/models/reading.py`:
   ```python
   __table_args__ = (
       Index("ix_readings_machine_time", "machine_id", "timestamp"),
       Index("ix_readings_machine_cycle", "machine_id", "cycle"),
   )
   ```
   This ensures history queries execute in $O(\log N)$ time.
3. Foreign key constraints with `ON DELETE CASCADE` ensure referential integrity while keeping SQLite WAL journal checkpoints fast.

**Code Reference**:  
- `backend/models/reading.py` -> `Reading.__table_args__`
- `backend/models/incident.py` -> `Incident.__table_args__`

---

### Q20: If this platform were deployed in a real manufacturing plant, what would be the edge integration pipeline?

**15-Second Crisp Answer**:  
Physical sensors connect via **MQTT or OPC-UA protocols** to an industrial edge gateway (such as a Raspberry Pi 4 or Siemens IPC). The gateway runs our lightweight PyTorch/ONNX inference models locally, while summary telemetry and alert payloads stream upstream to our FastAPI backend via WebSockets.

**Deep Technical Justification**:  
The production deployment architecture:
1. **Physical Layer**: Accelerometers, thermocouples, and pressure transducers wired to PLCs (Programmable Logic Controllers).
2. **Edge Ingestion**: PLCs publish telemetry over **OPC-UA / MQTT** topics (e.g. `factory/shopA/cnc01/telemetry`).
3. **Edge Inference Engine**: A Python or C++ edge daemon consumes MQTT messages, maintains a 30-step circular buffer, executes the ONNX runtime model in < 5ms, and computes the health score.
4. **Gateway-to-Server**: If an anomaly or threshold breach occurs, the edge gateway posts an alert to our FastAPI REST endpoint and pushes live streaming metrics to the WebSocket hub.
5. **Human Interface**: Plant engineers monitor the system via our responsive React 18 dashboard on floor tablets or desktop browsers.

**Code Reference**:  
- `backend/simulation/websocket_manager.py`
- `backend/main.py` -> REST & WebSocket architecture

