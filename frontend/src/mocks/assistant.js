// frontend/src/mocks/assistant.js
// Shape matches POST /api/assistant/query

export const MOCK_QUERIES = [
  {
    query: "Why is Milling Station C flagged as critical?",
    answer: "Milling Station C (Machine #3) has a health score of 23.1 and a predicted RUL of 11 cycles. The model's top contributing sensors are T50 (exhaust temperature, contributing 74% of the risk signal) and Ps30 (static pressure, 61%). Both are trending significantly above their healthy baselines. The failure probability is 83%, which crosses the critical threshold of 75%. Based on historical incidents from the NASA C-MAPSS dataset, engines with this sensor profile failed within 8–14 cycles.",
    data_sources: [
      { label: "Health score", value: "23.1 / 100", source: "ML model output" },
      { label: "RUL", value: "11 cycles", source: "LSTM regression (NASA C-MAPSS FD001)" },
      { label: "Failure probability", value: "83%", source: "XGBoost classifier" },
      { label: "Top sensor: T50", value: "1431.07 (baseline: ~1400)", source: "Live telemetry" },
    ],
    suggested_actions: [
      "Schedule immediate inspection of bearing assembly and exhaust manifold",
      "Reduce machine load to below 60% until inspection",
      "Prepare replacement bearing kit (Part #BRG-3042)",
    ],
    timestamp: "2026-11-16T10:12:07Z",
  },
  {
    query: "Which machine should I prioritize for maintenance this week?",
    answer: "Based on current health scores and RUL predictions, Milling Station C is the highest priority (RUL: 11 cycles, health: 23.1). Second priority is Turbine Engine B (RUL: 36 cycles, health: 54.7). Both show active warning alerts. The other machines are healthy with RUL > 50 cycles and do not require intervention this week.",
    data_sources: [
      { label: "Machine #3 RUL",  value: "11 cycles",  source: "ML model" },
      { label: "Machine #2 RUL",  value: "36 cycles",  source: "ML model" },
      { label: "Machine #5 RUL",  value: "54 cycles",  source: "ML model" },
      { label: "Active alerts",   value: "5 unresolved", source: "Alert system" },
    ],
    suggested_actions: [
      "Book maintenance for Machine #3 today",
      "Schedule Machine #2 inspection within 72 hours",
      "Monitor Machine #5 anomaly score daily",
    ],
    timestamp: "2026-11-16T09:44:31Z",
  },
  {
    query: "What is the estimated financial risk if I do not act on Machine 3?",
    answer: "If Milling Station C runs to failure (no intervention), the estimated total loss is ₹5,48,412 — comprising ₹4,19,250 in production loss (14.7 hours downtime × ₹28,500/hr), ₹48,900 in wasted energy, and ₹80,262 in order delay penalties. Preventive maintenance costs approximately ₹32,500. Early intervention saves roughly ₹5,15,912.",
    data_sources: [
      { label: "Est. downtime",     value: "14.7 hours",    source: "RUL model + historical avg" },
      { label: "Loss rate",         value: "₹28,500/hr",    source: "User assumption (editable)" },
      { label: "Preventive cost",   value: "₹32,500",       source: "Maintenance log estimate" },
      { label: "Potential saving",  value: "₹5,15,912",     source: "Formula: loss - preventive cost" },
    ],
    suggested_actions: [
      "Open Business Impact page to adjust loss assumptions",
      "Run the What-If simulator to compare shutdown vs. run-to-failure",
    ],
    timestamp: "2026-11-16T08:57:19Z",
  },
]

export const SUGGESTED_QUESTIONS = [
  "Why is Milling Station C flagged as critical?",
  "Which machine should I prioritize for maintenance this week?",
  "What is the estimated financial risk if I do not act on Machine 3?",
  "What sensors are driving the anomaly on Turbine Engine B?",
  "How accurate is the RUL prediction for Machine 2?",
  "Show me past incidents similar to what Machine 3 is showing now",
  "What is the factory health score and what affects it?",
  "If I shut down Machine 3 today, what happens to production?",
]

