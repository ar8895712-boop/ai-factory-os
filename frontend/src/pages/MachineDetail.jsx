// frontend/src/pages/MachineDetail.jsx — Machine Detail Deep Dive
import React, { useState } from 'react'
import { useParams, Link, useOutletContext } from 'react-router-dom'
import {
  ArrowLeft,
  Flame,
  CheckCircle2,
  AlertTriangle,
  AlertCircle,
  Activity,
  Cpu,
  Clock,
  IndianRupee,
  Sliders
} from 'lucide-react'
import StatusBadge from '../components/ui/StatusBadge.jsx'
import MetricTile from '../components/ui/MetricTile.jsx'
import HealthTrendChart from '../components/charts/HealthTrendChart.jsx'
import SHAPBars from '../components/charts/SHAPBars.jsx'
import { MOCK_MACHINES, MOCK_INCIDENTS } from '../mocks/index.js'

export default function MachineDetail(props) {
  const params = useParams()
  const context = useOutletContext() || {}

  const machines = props.machines || context.machines || MOCK_MACHINES
  const currentId = Number(props.selectedId || params.id || 1)
  const [selectedSensor, setSelectedSensor] = useState('T50')

  const machine = machines.find((m) => m.id === currentId) || machines[0]

  const health = machine.health_score ?? 100
  const rul = machine.rul_predicted ?? 120
  const anom = machine.anomaly_score ?? 0.1
  const failProb = machine.failure_probability ?? 0.05
  const currentCycle = machine.current_cycle ?? 180
  const maxCycle = machine.max_cycles || machine.max_cycle || 350

  const statusVariant =
    machine.status || (health < 30 ? 'critical' : health < 60 ? 'warning' : 'healthy')

  // SHAP feature attribution
  const shapFeatures = machine.latest_prediction?.shap_explanation || [
    { feature: 'T50', value: -0.65, direction: 'positive' },
    { feature: 'Ps30', value: -0.42, direction: 'positive' },
    { feature: 'phi', value: -0.28, direction: 'positive' },
    { feature: 'NRc', value: -0.16, direction: 'negative' },
    { feature: 'P30', value: -0.09, direction: 'positive' },
  ]

  // Historical incidents for this machine
  const machineIncidents = MOCK_INCIDENTS.filter((i) => i.machine_id === machine.id)

  // Recommended actions with expected costs
  const recommendedActions = [
    {
      title: 'Immediate preventive component replacement',
      cost_inr: 32500,
      impact: 'Eliminates 14.7 hours expected downtime. Restores health score to 96%.',
      urgency: 'high',
    },
    {
      title: 'Derate operating speed by 15%',
      cost_inr: 8400,
      impact: 'Extends remaining useful life by approximately 22 cycles. Reduces hourly throughput by 14%.',
      urgency: 'medium',
    },
    {
      title: 'Re-route workload to standby unit',
      cost_inr: 4200,
      impact: 'Maintains floor production while scheduling maintenance in the next shift.',
      urgency: 'low',
    },
  ]

  return (
    <div className="space-y-8">
      {/* Navigation & Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-border-subtle">
        <div className="flex items-center gap-3">
          <Link
            to="/app/overview"
            className="p-2 rounded-lg bg-bg-card border border-border-subtle text-text-secondary hover:text-white transition-colors"
            title="Back to Overview"
          >
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div>
            <div className="flex items-center gap-2.5">
              <span className="mono text-xs px-2 py-0.5 rounded bg-bg-raised text-text-secondary border border-border-subtle font-semibold">
                M-0{machine.id}
              </span>
              <h1 className="heading-4 text-white">{machine.name}</h1>
              <StatusBadge status={statusVariant} size="sm" />
            </div>
            <p className="caption-4 text-text-muted mt-0.5">
              {machine.type} • {machine.location} • Benchmark: {machine.dataset_source || 'NASA C-MAPSS FD001'}
            </p>
          </div>
        </div>

        {/* Machine Switcher Pill */}
        <div className="flex items-center gap-2 overflow-x-auto pb-2 sm:pb-0">
          {machines.map((m) => (
            <Link
              key={m.id}
              to={`/app/machines/${m.id}`}
              className={`px-3 py-1.5 rounded-lg caption-4 mono transition-colors whitespace-nowrap ${
                m.id === machine.id
                  ? 'bg-white text-black font-semibold'
                  : 'bg-bg-card border border-border-subtle text-text-secondary hover:text-white'
              }`}
            >
              M-0{m.id}
            </Link>
          ))}
        </div>
      </div>

      {/* Top Health & RUL KPI Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricTile
          label="Health Score"
          value={`${health.toFixed(1)}%`}
          status={statusVariant}
          sublabel={`Cycle ${currentCycle} of ${maxCycle}`}
          icon={Activity}
        />
        <MetricTile
          label="Predicted RUL"
          value={rul.toFixed(0)}
          unit="cycles"
          status={rul < 30 ? 'critical' : rul < 60 ? 'warning' : 'healthy'}
          sublabel="Multi-layer LSTM trajectory forecast"
          icon={Clock}
        />
        <MetricTile
          label="Anomaly Score"
          value={anom.toFixed(2)}
          status={anom > 0.75 ? 'critical' : anom > 0.4 ? 'warning' : 'healthy'}
          sublabel="Autoencoder reconstruction error"
          icon={AlertCircle}
        />
        <MetricTile
          label="Failure Probability"
          value={`${(failProb * 100).toFixed(0)}%`}
          status={failProb > 0.7 ? 'critical' : failProb > 0.35 ? 'warning' : 'healthy'}
          sublabel="XGBoost hazard estimation"
          icon={Cpu}
        />
      </div>

      {/* Health Trend & SHAP Root Cause Attribution */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Health Trend Chart (2 cols) */}
        <div className="card p-5 lg:col-span-2 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 mb-3 border-b border-border-subtle">
              <div>
                <h2 className="title-3 text-white">Health Score Trajectory</h2>
                <p className="caption-5 text-text-muted">Historical degradation across completed operating cycles</p>
              </div>
              <span className="caption-4 mono text-text-secondary">
                Current: {health.toFixed(1)}%
              </span>
            </div>
            <HealthTrendChart
              data={machine.health_history || [
                { cycle: 1, health: 99.2 },
                { cycle: 50, health: 94.6 },
                { cycle: 100, health: 86.1 },
                { cycle: 150, health: 74.3 },
                { cycle: currentCycle, health },
              ]}
              height={260}
            />
          </div>
        </div>

        {/* Root Cause Hints / SHAP Bars (1 col) */}
        <div className="card p-5 flex flex-col justify-between">
          <div>
            <div className="pb-3 mb-3 border-b border-border-subtle">
              <h2 className="title-3 text-white">Root Cause Attributions</h2>
              <p className="caption-5 text-text-muted">Top contributing sensors explaining current risk</p>
            </div>
            <SHAPBars features={shapFeatures} />
          </div>
          <div className="mt-4 pt-3 border-t border-border-subtle caption-5 text-text-muted">
            Calculated via TreeSHAP explainer against baseline healthy cycles.
          </div>
        </div>
      </div>

      {/* Live Telemetry Sensor Table (Geist Mono per design system) */}
      <div className="card p-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 mb-4 border-b border-border-subtle">
          <div>
            <h2 className="title-3 text-white">Live Telemetry Readings</h2>
            <p className="caption-5 text-text-muted">Current sensor stream values (all sensor values rendered in Geist Mono)</p>
          </div>
          <span className="caption-4 mono text-text-secondary">
            Stream packet: Cycle {currentCycle}
          </span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          {machine.latest_readings ? (
            Object.entries(machine.latest_readings).map(([key, val]) => (
              <div
                key={key}
                onClick={() => setSelectedSensor(key)}
                className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                  selectedSensor === key
                    ? 'bg-bg-raised border-white'
                    : 'bg-bg-raised/50 border-border-subtle hover:border-border-default'
                }`}
              >
                <div className="caption-5 text-text-muted uppercase tracking-wider">{key}</div>
                <div className="title-4 mono text-white font-medium mt-1">
                  {typeof val === 'number' ? val.toFixed(2) : String(val)}
                </div>
              </div>
            ))
          ) : (
            <div className="caption-4 text-text-muted col-span-full py-4 text-center">
              No live sensor packet available
            </div>
          )}
        </div>
      </div>

      {/* Recommended Actions with Expected Cost in Indian Rupees */}
      <div className="card p-5">
        <div className="flex items-center justify-between pb-3 mb-4 border-b border-border-subtle">
          <div>
            <h2 className="title-3 text-white">Recommended Actions & Interventions</h2>
            <p className="caption-5 text-text-muted">Prioritized engineering mitigations with projected financial costs in Indian Rupees</p>
          </div>
          <Link
            to="/app/whatif"
            className="caption-4 text-white hover:underline flex items-center gap-1"
          >
            <span>Simulate in What-If</span>
            <Sliders className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {recommendedActions.map((action, idx) => (
            <div
              key={idx}
              className="p-4 rounded-xl bg-bg-raised/70 border border-border-subtle flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between gap-2 mb-2">
                  <span className="caption-5 uppercase font-semibold text-text-muted">
                    Option 0{idx + 1}
                  </span>
                  <span
                    className={`px-2 py-0.5 rounded-full text-xs font-medium mono ${
                      action.urgency === 'high'
                        ? 'bg-status-critical/15 text-status-critical'
                        : action.urgency === 'medium'
                        ? 'bg-status-warning/15 text-status-warning'
                        : 'bg-status-info/15 text-status-info'
                    }`}
                  >
                    {action.urgency} priority
                  </span>
                </div>
                <h3 className="title-4 text-white font-medium mb-2">
                  {action.title}
                </h3>
                <p className="caption-4 text-text-secondary leading-relaxed mb-4">
                  {action.impact}
                </p>
              </div>

              <div className="pt-3 border-t border-border-subtle flex items-baseline justify-between">
                <span className="caption-5 text-text-muted">Expected Cost</span>
                <span className="title-4 mono text-white font-semibold">
                  ₹{action.cost_inr.toLocaleString('en-IN')}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Machine Incident History */}
      {machineIncidents.length > 0 && (
        <div className="card p-5">
          <div className="pb-3 mb-3 border-b border-border-subtle">
            <h2 className="title-3 text-white">Historical Incidents for {machine.name}</h2>
            <p className="caption-5 text-text-muted">Logged records stored in Factory Memory</p>
          </div>
          <div className="space-y-3">
            {machineIncidents.map((inc) => (
              <div
                key={inc.id}
                className="p-3.5 rounded-lg bg-bg-raised/60 border border-border-subtle flex flex-col sm:flex-row sm:items-center justify-between gap-2"
              >
                <div>
                  <div className="title-4 text-white font-medium">{inc.root_cause}</div>
                  <div className="caption-4 text-text-secondary mt-1">Resolution: {inc.resolution}</div>
                  <div className="caption-5 text-text-muted mt-1">
                    Downtime: {inc.downtime_hours} hrs • Financial impact: ₹{inc.cost_inr.toLocaleString('en-IN')}
                  </div>
                </div>
                <div className="caption-5 mono px-2.5 py-1 rounded bg-bg-card border border-border-subtle text-text-secondary flex-shrink-0">
                  Similarity match: {(inc.similarity_score * 100).toFixed(0)}%
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export { MachineDetail }
