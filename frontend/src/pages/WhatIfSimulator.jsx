// frontend/src/pages/WhatIfSimulator.jsx — What-If Scenario Simulator
import React, { useState } from 'react'
import {
  Sliders,
  Play,
  RotateCcw,
  TrendingDown,
  Activity,
  IndianRupee,
  Zap,
  Clock,
  ArrowRight
} from 'lucide-react'
import MetricTile from '../components/ui/MetricTile.jsx'
import ComparisonChart from '../components/charts/ComparisonChart.jsx'
import {
  MOCK_WHATIF_RESULT,
  SCENARIO_ACTIONS,
  MOCK_MACHINES
} from '../mocks/index.js'

export default function WhatIfSimulator() {
  const [targetMachineId, setTargetMachineId] = useState(3)
  const [selectedAction, setSelectedAction] = useState('shutdown_and_maintenance')
  const [workloadShiftPct, setWorkloadShiftPct] = useState(20)
  const [speedReductionPct, setSpeedReductionPct] = useState(15)
  const [hasRun, setHasRun] = useState(true)

  // In a full implementation, this could call POST /api/whatif/run
  const result = MOCK_WHATIF_RESULT

  const costComparisonData = [
    { name: 'M-02 (Turbine B)', baseline: 234899, scenario: 41030 },
    { name: 'M-03 (Milling C)', baseline: 548412, scenario: 32500 },
    { name: 'M-05 (Conveyor E)', baseline: 115587, scenario: 22800 },
  ]

  const downtimeComparisonData = [
    { name: 'M-02', baseline: 6.3, scenario: 1.1 },
    { name: 'M-03', baseline: 14.7, scenario: 2.5 },
    { name: 'M-05', baseline: 3.1, scenario: 0.8 },
  ]

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-border-subtle">
        <div>
          <h1 className="heading-4 sm:heading-3 text-white">What-If Simulation Engine</h1>
          <p className="caption-1 text-text-secondary mt-1">
            Simulate operational interventions to evaluate trade-offs in downtime, production, and cost
          </p>
        </div>
      </div>

      {/* Scenario Control Form */}
      <div className="card p-6 bg-bg-card border border-border-default">
        <div className="flex items-center gap-2 pb-3 mb-5 border-b border-border-subtle">
          <Sliders className="w-5 h-5 text-white" />
          <h2 className="title-2 text-white">Scenario Parameters</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Target Machine */}
          <div>
            <label className="block caption-1 text-white font-medium mb-2">
              Select Target Machine
            </label>
            <select
              value={targetMachineId}
              onChange={(e) => setTargetMachineId(Number(e.target.value))}
              className="w-full px-3.5 py-2.5 bg-bg-raised border border-border-default rounded-lg text-white text-sm focus:ring-1 focus:ring-white"
            >
              {MOCK_MACHINES.map((m) => (
                <option key={m.id} value={m.id}>
                  M-0{m.id} — {m.name} ({m.status})
                </option>
              ))}
            </select>
            <p className="caption-5 text-text-muted mt-1.5">
              The operational unit undergoing hypothetical intervention.
            </p>
          </div>

          {/* Intervention Strategy */}
          <div>
            <label className="block caption-1 text-white font-medium mb-2">
              Intervention Strategy
            </label>
            <select
              value={selectedAction}
              onChange={(e) => setSelectedAction(e.target.value)}
              className="w-full px-3.5 py-2.5 bg-bg-raised border border-border-default rounded-lg text-white text-sm focus:ring-1 focus:ring-white"
            >
              {SCENARIO_ACTIONS.map((action) => (
                <option key={action.value} value={action.value}>
                  {action.label}
                </option>
              ))}
            </select>
            <p className="caption-5 text-text-muted mt-1.5">
              Operational procedure simulated over a 50 cycle planning horizon.
            </p>
          </div>

          {/* Sliders for Dynamic Tuning */}
          <div className="space-y-3">
            <div>
              <div className="flex justify-between caption-4 mb-1">
                <span className="text-white font-medium">Speed Reduction</span>
                <span className="mono text-text-secondary">{speedReductionPct}%</span>
              </div>
              <input
                type="range"
                min="0"
                max="50"
                step="5"
                value={speedReductionPct}
                onChange={(e) => setSpeedReductionPct(Number(e.target.value))}
                className="w-full accent-white"
              />
            </div>

            <div>
              <div className="flex justify-between caption-4 mb-1">
                <span className="text-white font-medium">Workload Shift to Standby</span>
                <span className="mono text-text-secondary">{workloadShiftPct}%</span>
              </div>
              <input
                type="range"
                min="0"
                max="50"
                step="10"
                value={workloadShiftPct}
                onChange={(e) => setWorkloadShiftPct(Number(e.target.value))}
                className="w-full accent-white"
              />
            </div>
          </div>
        </div>

        {/* Action button */}
        <div className="mt-6 pt-4 border-t border-border-subtle flex justify-end">
          <button
            onClick={() => setHasRun(true)}
            className="btn-primary py-2.5 px-6 button-sm gap-2"
          >
            <Play className="w-4 h-4" />
            <span>Run Simulation</span>
          </button>
        </div>
      </div>

      {/* Simulation Result Section */}
      {hasRun && (
        <div className="space-y-6">
          {/* Top Outcome KPIs */}
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
            <MetricTile
              label="Net Financial Savings"
              value={`₹${result.summary.total_savings_inr.toLocaleString('en-IN')}`}
              status="healthy"
              sublabel="Baseline risk vs scenario execution"
              icon={IndianRupee}
            />
            <MetricTile
              label="Downtime Prevented"
              value="19.7"
              unit="hours"
              status="healthy"
              sublabel="Cumulative hours saved across line"
              icon={Clock}
            />
            <MetricTile
              label="Production Impact"
              value={`${result.summary.total_production_impact_pct}%`}
              status="warning"
              sublabel="Planned production throughput variance"
              icon={Activity}
            />
            <MetricTile
              label="Energy Reduction"
              value="2,723"
              unit="kWh"
              status="info"
              sublabel="Avoided power consumption in degraded state"
              icon={Zap}
            />
          </div>

          {/* Comparison Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="card p-5">
              <div className="pb-3 mb-3 border-b border-border-subtle">
                <h3 className="title-3 text-white">Cost Exposure Comparison (₹)</h3>
                <p className="caption-5 text-text-muted">Unmitigated baseline failure vs simulated intervention</p>
              </div>
              <ComparisonChart
                data={costComparisonData}
                unit=" ₹"
                height={240}
              />
            </div>

            <div className="card p-5">
              <div className="pb-3 mb-3 border-b border-border-subtle">
                <h3 className="title-3 text-white">Expected Downtime Comparison (Hours)</h3>
                <p className="caption-5 text-text-muted">Unscheduled breakdown duration vs controlled maintenance</p>
              </div>
              <ComparisonChart
                data={downtimeComparisonData}
                unit=" hrs"
                height={240}
              />
            </div>
          </div>

          {/* Per Machine Scenario Detail Table */}
          <div className="card overflow-hidden">
            <div className="p-5 border-b border-border-subtle">
              <h3 className="title-3 text-white">Detailed Asset Scenario Matrix</h3>
              <p className="caption-4 text-text-muted">50-cycle horizon delta analysis</p>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-border-subtle bg-bg-raised/40 caption-4 text-text-muted">
                    <th className="py-3 px-4 font-medium">Machine</th>
                    <th className="py-3 px-4 font-medium">Action Assigned</th>
                    <th className="py-3 px-4 font-medium">Production Output</th>
                    <th className="py-3 px-4 font-medium">Downtime Delta</th>
                    <th className="py-3 px-4 font-medium">Energy Delta</th>
                    <th className="py-3 px-4 font-medium text-right">Net Financial Delta</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border-subtle">
                  {result.machines.map((m) => (
                    <tr key={m.machine_id} className="hover:bg-bg-raised/30 transition-colors">
                      <td className="py-3.5 px-4">
                        <div className="title-4 text-white font-medium">{m.machine_name}</div>
                        <div className="caption-5 mono text-text-muted">ID: {m.machine_id}</div>
                      </td>
                      <td className="py-3.5 px-4 caption-4 text-text-secondary capitalize">
                        {m.action.replace(/_/g, ' ')}
                      </td>
                      <td className="py-3.5 px-4 mono text-sm text-white">
                        {m.scenario.production_pct}% ({m.delta.production_pct > 0 ? `+${m.delta.production_pct}%` : `${m.delta.production_pct}%`})
                      </td>
                      <td className="py-3.5 px-4 mono text-sm text-status-healthy">
                        {m.delta.downtime_hours} hrs
                      </td>
                      <td className="py-3.5 px-4 mono text-sm text-text-secondary">
                        {m.delta.energy_kwh} kWh
                      </td>
                      <td className="py-3.5 px-4 mono text-sm font-semibold text-status-healthy text-right">
                        ₹{Math.abs(m.delta.cost_inr).toLocaleString('en-IN')} saved
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export { WhatIfSimulator }
