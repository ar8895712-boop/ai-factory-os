// frontend/src/mocks/businessImpact.js
// Shape matches GET /api/business/impact
// All monetary values in Indian Rupees (₹)

export const DEFAULT_ASSUMPTIONS = {
  loss_per_hour_inr: 28500,       // ₹/hr downtime loss
  energy_tariff_inr_per_kwh: 7.4, // ₹/kWh
  delay_penalty_per_order_inr: 4200, // ₹/order delayed
  avg_orders_per_hour: 1.3,
  machine_power_kw: 45,
}

export const MOCK_BUSINESS_IMPACT = [
  {
    machine_id: 3,
    machine_name: "Milling Station C",
    status: "critical",
    rul_cycles: 11,
    estimated_downtime_hours: 14.7,
    production_loss_inr: 419_250,
    energy_wasted_inr: 48_900,
    delay_penalty_inr: 80_262,
    total_estimated_loss_inr: 548_412,
    formula: {
      production_loss: "downtime_hours × loss_per_hour",
      energy_wasted: "downtime_hours × machine_power_kw × energy_tariff",
      delay_penalty: "downtime_hours × avg_orders_per_hour × delay_penalty_per_order",
    },
    preventive_maintenance_cost_inr: 32_500,
    savings_vs_breakdown_inr: 515_912,
  },
  {
    machine_id: 2,
    machine_name: "Turbine Engine B",
    status: "warning",
    rul_cycles: 36,
    estimated_downtime_hours: 6.3,
    production_loss_inr: 179_550,
    energy_wasted_inr: 20_951,
    delay_penalty_inr: 34_398,
    total_estimated_loss_inr: 234_899,
    formula: {
      production_loss: "downtime_hours × loss_per_hour",
      energy_wasted: "downtime_hours × machine_power_kw × energy_tariff",
      delay_penalty: "downtime_hours × avg_orders_per_hour × delay_penalty_per_order",
    },
    preventive_maintenance_cost_inr: 18_200,
    savings_vs_breakdown_inr: 216_699,
  },
  {
    machine_id: 5,
    machine_name: "Conveyor Drive E",
    status: "warning",
    rul_cycles: 54,
    estimated_downtime_hours: 3.1,
    production_loss_inr: 88_350,
    energy_wasted_inr: 10_311,
    delay_penalty_inr: 16_926,
    total_estimated_loss_inr: 115_587,
    formula: {
      production_loss: "downtime_hours × loss_per_hour",
      energy_wasted: "downtime_hours × machine_power_kw × energy_tariff",
      delay_penalty: "downtime_hours × avg_orders_per_hour × delay_penalty_per_order",
    },
    preventive_maintenance_cost_inr: 9_400,
    savings_vs_breakdown_inr: 106_187,
  },
]

export const getTotalExposure = () =>
  MOCK_BUSINESS_IMPACT.reduce((s, m) => s + m.total_estimated_loss_inr, 0)

export const getTotalPreventiveCost = () =>
  MOCK_BUSINESS_IMPACT.reduce((s, m) => s + m.preventive_maintenance_cost_inr, 0)

