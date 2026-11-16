// frontend/src/mocks/index.js
// Barrel export for all mock data

export { MOCK_MACHINES, getMachineById, getFactoryHealthScore } from './machines.js'
export { MOCK_ALERTS, getActiveAlerts, getCriticalAlerts } from './alerts.js'
export { MOCK_INCIDENTS, getPatternsSummary } from './incidents.js'
export {
  DEFAULT_ASSUMPTIONS,
  MOCK_BUSINESS_IMPACT,
  getTotalExposure,
  getTotalPreventiveCost,
} from './businessImpact.js'
export {
  MOCK_SIMULATION_BASELINE,
  MOCK_WHATIF_RESULT,
  SCENARIO_ACTIONS,
} from './simulation.js'
export { MOCK_QUERIES, SUGGESTED_QUESTIONS } from './assistant.js'

