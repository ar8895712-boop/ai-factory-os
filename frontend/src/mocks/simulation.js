// frontend/src/mocks/simulation.js
// Shape matches POST /api/whatif/run and GET /api/simulation/status

export const MOCK_SIMULATION_BASELINE = {
  horizon_cycles: 50,
  machines: [
    {
      machine_id: 2,
      machine_name: "Turbine Engine B",
      baseline: { production_pct: 100, downtime_hours: 0, cost_inr: 0, energy_kwh: 2250 },
      scenario: null,
    },
    {
      machine_id: 3,
      machine_name: "Milling Station C",
      baseline: { production_pct: 100, downtime_hours: 0, cost_inr: 0, energy_kwh: 2025 },
      scenario: null,
    },
    {
      machine_id: 5,
      machine_name: "Conveyor Drive E",
      baseline: { production_pct: 100, downtime_hours: 0, cost_inr: 0, energy_kwh: 1800 },
      scenario: null,
    },
  ],
}

export const MOCK_WHATIF_RESULT = {
  scenario_id: "s-20261116-001",
  horizon_cycles: 50,
  machines: [
    {
      machine_id: 2,
      machine_name: "Turbine Engine B",
      action: "speed_reduction_15pct",
      baseline: { production_pct: 100, downtime_hours: 6.3, cost_inr: 234_899, energy_kwh: 2250 },
      scenario: { production_pct: 86, downtime_hours: 1.1, cost_inr: 41_030, energy_kwh: 1912 },
      delta: { production_pct: -14, downtime_hours: -5.2, cost_inr: -193_869, energy_kwh: -338 },
    },
    {
      machine_id: 3,
      machine_name: "Milling Station C",
      action: "shutdown_and_maintenance",
      baseline: { production_pct: 100, downtime_hours: 14.7, cost_inr: 548_412, energy_kwh: 2025 },
      scenario: { production_pct: 0, downtime_hours: 2.5, cost_inr: 32_500, energy_kwh: 0 },
      delta: { production_pct: -100, downtime_hours: -12.2, cost_inr: -515_912, energy_kwh: -2025 },
    },
    {
      machine_id: 5,
      machine_name: "Conveyor Drive E",
      action: "workload_shift_20pct",
      baseline: { production_pct: 100, downtime_hours: 3.1, cost_inr: 115_587, energy_kwh: 1800 },
      scenario: { production_pct: 80, downtime_hours: 0.8, cost_inr: 22_800, energy_kwh: 1440 },
      delta: { production_pct: -20, downtime_hours: -2.3, cost_inr: -92_787, energy_kwh: -360 },
    },
  ],
  summary: {
    total_cost_baseline_inr: 898_898,
    total_cost_scenario_inr: 96_330,
    total_savings_inr: 802_568,
    total_production_impact_pct: -44.7,
  },
}

export const SCENARIO_ACTIONS = [
  { value: "shutdown_and_maintenance", label: "Shut down for maintenance" },
  { value: "speed_reduction_15pct",   label: "Reduce speed 15%" },
  { value: "speed_reduction_30pct",   label: "Reduce speed 30%" },
  { value: "workload_shift_20pct",    label: "Shift 20% workload to standby" },
  { value: "workload_shift_40pct",    label: "Shift 40% workload to standby" },
  { value: "run_to_failure",          label: "Run to failure (no action)" },
]

