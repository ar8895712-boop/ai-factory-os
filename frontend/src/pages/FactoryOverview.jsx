// frontend/src/pages/FactoryOverview.jsx — Fleet Health Dashboard
import React from 'react'
import { Link, useNavigate, useOutletContext } from 'react-router-dom'
import {
  Activity,
  AlertTriangle,
  AlertCircle,
  Clock,
  ArrowRight,
  Flame,
  Calendar,
  IndianRupee,
  Cpu,
  Bot
} from 'lucide-react'
import StatusBadge from '../components/ui/StatusBadge.jsx'
import MetricTile from '../components/ui/MetricTile.jsx'
import Sparkline from '../components/charts/Sparkline.jsx'
import AnomalyTrendChart from '../components/charts/AnomalyTrendChart.jsx'
import { MOCK_MACHINES, MOCK_ALERTS, MOCK_INCIDENTS } from '../mocks/index.js'

export default function FactoryOverview(props) {
  const context = useOutletContext() || {}
  const navigate = useNavigate()

  const machines = props.machines || context.machines || MOCK_MACHINES
  const onSelectMachine = props.onSelectMachine || ((id) => navigate(`/app/machines/${id}`))
  const onJumpMachine = props.onJumpMachine || ((id, cycle) => navigate(`/app/machines/${id}`))

  // Calculate fleet aggregated statistics
  const total = machines.length || 6
  const avgHealth = +(
    machines.reduce((acc, m) => acc + (m.health_score || 100), 0) / (machines.length || 1)
  ).toFixed(1)

  const criticalMachines = machines.filter(
    (m) => m.status === 'critical' || (m.health_score || 100) < 30
  )
  const warningMachines = machines.filter(
    (m) => m.status === 'warning' || ((m.health_score || 100) >= 30 && (m.health_score || 100) < 60)
  )
  const avgRul = Math.round(
    machines.reduce((acc, m) => acc + (m.rul_predicted || 120), 0) / (machines.length || 1)
  )

  // Critical alerts ordered first
  const activeAlerts = [...MOCK_ALERTS].sort((a, b) => {
    if (a.severity === 'critical' && b.severity !== 'critical') return -1
    if (a.severity !== 'critical' && b.severity === 'critical') return 1
    return 0
  })

  // Sample anomaly chart data from Machine 3
  const anomalyData = [
    { cycle: 60, score: 0.18 },
    { cycle: 70, score: 0.27 },
    { cycle: 80, score: 0.44 },
    { cycle: 88, score: 0.62 },
    { cycle: 93, score: 0.76 },
    { cycle: 97, score: 0.89 },
  ]

  return (
    <div className="space-y-8">
      {/* Page Title & Context Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-border-subtle">
        <div>
          <h1 className="heading-4 sm:heading-3 text-white">Factory Overview</h1>
          <p className="caption-1 text-text-secondary mt-1">
            Real time digital twin status across {total} monitored industrial assets
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Link
            to="/app/assistant"
            className="btn-secondary px-3.5 py-2 button-sm gap-2"
          >
            <Bot className="w-4 h-4 text-text-secondary" />
            <span>Ask assistant</span>
          </Link>
          <Link
            to="/app/whatif"
            className="btn-primary px-3.5 py-2 button-sm gap-2"
          >
            <span>Simulate what if</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </div>

      {/* Fleet Top Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricTile
          label="Fleet Health Index"
          value={`${avgHealth}%`}
          status={avgHealth < 40 ? 'critical' : avgHealth < 70 ? 'warning' : 'healthy'}
          sublabel="Calculated average across all active machine units"
          icon={Activity}
        />
        <MetricTile
          label="Critical Alerts"
          value={criticalMachines.length}
          status={criticalMachines.length > 0 ? 'critical' : 'healthy'}
          sublabel={criticalMachines.length > 0 ? 'Immediate intervention advised' : 'All assets operational'}
          icon={AlertCircle}
        />
        <MetricTile
          label="Degradation Warnings"
          value={warningMachines.length}
          status={warningMachines.length > 0 ? 'warning' : 'healthy'}
          sublabel="Assets with RUL below 60 cycles"
          icon={AlertTriangle}
        />
        <MetricTile
          label="Average Fleet RUL"
          value={avgRul}
          unit="cycles"
          sublabel="Estimated remaining run cycles"
          icon={Clock}
        />
      </div>

      {/* Machine Status Cards Grid */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="title-2 text-white">Monitored Assets</h2>
            <p className="caption-4 text-text-muted">Select an asset to view live sensor telemetry and SHAP attributions</p>
          </div>
          <span className="caption-4 mono text-text-muted">
            {machines.length} active digital twins
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {machines.map((m) => {
            const health = m.health_score ?? 100
            const rul = m.rul_predicted ?? 120
            const anom = m.anomaly_score ?? 0.1
            const maxC = m.max_cycles || m.max_cycle || 350
            const currentC = m.current_cycle || 100
            const statusVariant = m.status || (health < 30 ? 'critical' : health < 60 ? 'warning' : 'healthy')

            const sparklineData = m.health_history?.map((h) => ({ health: h.health })) || [
              { health: Math.min(100, health + 10) },
              { health: Math.min(100, health + 6) },
              { health: Math.min(100, health + 3) },
              { health },
            ]

            return (
              <div
                key={m.id}
                className="card p-5 flex flex-col justify-between hover:border-neutral-700 transition-colors"
              >
                <div>
                  {/* Card Header */}
                  <div className="flex items-start justify-between gap-3 mb-3">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="mono text-xs font-semibold px-2 py-0.5 rounded bg-bg-raised text-text-secondary border border-border-subtle">
                          M-0{m.id}
                        </span>
                        <h3 className="title-3 text-white font-medium">{m.name}</h3>
                      </div>
                      <p className="caption-5 text-text-muted mt-1">{m.location}</p>
                    </div>
                    <StatusBadge status={statusVariant} size="sm" />
                  </div>

                  {/* Health Bar */}
                  <div className="mt-3 mb-4">
                    <div className="flex justify-between caption-4 mb-1.5">
                      <span className="text-text-muted">Health score</span>
                      <span className="mono text-white font-medium">{health.toFixed(1)}%</span>
                    </div>
                    <div className="w-full bg-bg-raised h-1.5 rounded-full overflow-hidden">
                      <div
                        className={`h-full transition-all duration-300 ${
                          health < 30 ? 'bg-status-critical' : health < 60 ? 'bg-status-warning' : 'bg-status-healthy'
                        }`}
                        style={{ width: `${Math.min(100, Math.max(0, health))}%` }}
                      />
                    </div>
                  </div>

                  {/* Core Metrics Grid */}
                  <div className="grid grid-cols-3 gap-2 p-3 rounded-lg bg-bg-raised/60 border border-border-subtle text-center mb-3">
                    <div>
                      <span className="block caption-5 text-text-muted">RUL</span>
                      <span className="mono font-semibold text-sm text-white">
                        {rul.toFixed(0)} <span className="caption-5 text-text-muted font-normal">cyc</span>
                      </span>
                    </div>
                    <div>
                      <span className="block caption-5 text-text-muted">Anomaly</span>
                      <span className={`mono font-semibold text-sm ${anom > 0.7 ? 'text-status-critical' : 'text-text-primary'}`}>
                        {anom.toFixed(2)}
                      </span>
                    </div>
                    <div>
                      <span className="block caption-5 text-text-muted">Cycle</span>
                      <span className="mono font-semibold text-sm text-text-secondary">
                        {currentC} <span className="caption-5 text-text-muted font-normal">/ {maxC}</span>
                      </span>
                    </div>
                  </div>

                  {/* Mini Sparkline */}
                  <div className="py-1">
                    <div className="caption-5 text-text-muted mb-1">Health trajectory</div>
                    <Sparkline data={sparklineData} status={statusVariant} height={32} />
                  </div>
                </div>

                {/* Card Action footer */}
                <div className="mt-4 pt-3 border-t border-border-subtle flex items-center justify-between gap-2">
                  <button
                    onClick={() => onJumpMachine(m.id, Math.max(1, maxC - 15))}
                    className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-medium text-status-warning bg-status-warning/10 hover:bg-status-warning/20 border border-status-warning/20 transition-colors"
                    title="Jump near failure point"
                  >
                    <Flame className="w-3.5 h-3.5" />
                    <span>Cycle {maxC - 15}</span>
                  </button>

                  <button
                    onClick={() => onSelectMachine(m.id)}
                    className="inline-flex items-center gap-1 caption-4 text-white hover:text-neutral-300 font-medium py-1 px-2 rounded hover:bg-bg-raised transition-colors"
                  >
                    <span>Inspect</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Two Column Layout: Critical Alert Panel & Anomaly Progression */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Alert Panel (Critical alerts first per spec) */}
        <div className="card p-5 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 mb-3 border-b border-border-subtle">
              <div className="flex items-center gap-2">
                <AlertCircle className="w-4 h-4 text-status-critical" />
                <h3 className="title-3 text-white">Active Alerts</h3>
              </div>
              <Link to="/app/alerts" className="caption-4 text-text-secondary hover:text-white transition-colors">
                View all ({activeAlerts.length})
              </Link>
            </div>

            <div className="space-y-3">
              {activeAlerts.slice(0, 4).map((alert) => (
                <div
                  key={alert.id}
                  className={`p-3.5 rounded-xl border ${
                    alert.severity === 'critical'
                      ? 'bg-status-critical/5 border-status-critical/30'
                      : 'bg-bg-raised/60 border-border-subtle'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="caption-3 text-white font-medium">
                      {alert.machine_name}
                    </span>
                    <StatusBadge status={alert.severity} size="sm" />
                  </div>
                  <p className="caption-4 text-text-secondary leading-relaxed">
                    {alert.description}
                  </p>
                  <div className="mt-2.5 pt-2 border-t border-border-subtle/50 flex justify-between items-center caption-5 mono text-text-muted">
                    <span>RUL: {alert.rul_at_time} cycles</span>
                    <span>{new Date(alert.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Anomaly Trend Chart Panel */}
        <div className="card p-5 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 mb-3 border-b border-border-subtle">
              <div>
                <h3 className="title-3 text-white">Critical Anomaly Progression</h3>
                <p className="caption-5 text-text-muted">Milling Station C (Machine 3) degradation window</p>
              </div>
              <span className="caption-4 mono text-status-critical">
                Score: 0.89
              </span>
            </div>
            <AnomalyTrendChart data={anomalyData} height={220} />
          </div>

          <div className="mt-4 pt-3 border-t border-border-subtle flex items-center justify-between caption-4 text-text-secondary">
            <span>Critical threshold set at 0.75</span>
            <Link to="/app/machines/3" className="text-white hover:underline flex items-center gap-1">
              <span>View sensor breakdown</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>
      </div>

      {/* Maintenance Calendar & Incident Timeline Strip */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Maintenance Calendar */}
        <div className="card p-5 lg:col-span-1">
          <div className="flex items-center gap-2 pb-3 mb-3 border-b border-border-subtle">
            <Calendar className="w-4 h-4 text-text-muted" />
            <h3 className="title-3 text-white">Upcoming Interventions</h3>
          </div>
          <div className="space-y-3">
            <div className="p-3 rounded-lg bg-bg-raised/60 border border-border-subtle">
              <div className="flex justify-between items-center caption-4 text-status-critical font-medium">
                <span>Milling Station C</span>
                <span className="mono">Cycle 98</span>
              </div>
              <p className="caption-5 text-text-secondary mt-1">
                Bearing replacement and manifold inspection
              </p>
            </div>
            <div className="p-3 rounded-lg bg-bg-raised/60 border border-border-subtle">
              <div className="flex justify-between items-center caption-4 text-status-warning font-medium">
                <span>Turbine Engine B</span>
                <span className="mono">Cycle 300</span>
              </div>
              <p className="caption-5 text-text-secondary mt-1">
                Scheduled compressor water wash and blade inspect
              </p>
            </div>
            <div className="p-3 rounded-lg bg-bg-raised/60 border border-border-subtle">
              <div className="flex justify-between items-center caption-4 text-text-primary font-medium">
                <span>Compressor Unit A</span>
                <span className="mono">Cycle 210</span>
              </div>
              <p className="caption-5 text-text-secondary mt-1">
                Routine filter change and lubrication
              </p>
            </div>
          </div>
        </div>

        {/* Historical Incident Highlights */}
        <div className="card p-5 lg:col-span-2 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 mb-3 border-b border-border-subtle">
              <h3 className="title-3 text-white">Recent Incident Timeline</h3>
              <Link to="/app/memory" className="caption-4 text-text-secondary hover:text-white transition-colors">
                View factory memory
              </Link>
            </div>
            <div className="space-y-2.5">
              {MOCK_INCIDENTS.slice(0, 3).map((inc) => (
                <div
                  key={inc.id}
                  className="p-3 rounded-lg bg-bg-raised/50 border border-border-subtle flex flex-col sm:flex-row sm:items-center justify-between gap-2"
                >
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="title-5 text-white">{inc.machine_name}</span>
                      <span className="caption-5 text-text-muted">• {inc.root_cause.slice(0, 52)}...</span>
                    </div>
                    <div className="caption-5 text-text-muted mt-0.5">
                      Downtime: {inc.downtime_hours} hrs • Impact: ₹{inc.cost_inr.toLocaleString('en-IN')}
                    </div>
                  </div>
                  <span className="caption-5 mono px-2 py-0.5 rounded bg-bg-card border border-border-subtle text-text-secondary flex-shrink-0">
                    Match score: {(inc.similarity_score * 100).toFixed(0)}%
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export { FactoryOverview }
