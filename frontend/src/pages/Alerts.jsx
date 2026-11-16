// frontend/src/pages/Alerts.jsx — Active and Historical Alerts Panel
import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import {
  AlertTriangle,
  AlertCircle,
  CheckCircle2,
  Info,
  ArrowRight,
  Filter,
  Check
} from 'lucide-react'
import StatusBadge from '../components/ui/StatusBadge.jsx'
import { MOCK_ALERTS } from '../mocks/index.js'

export default function Alerts() {
  const [alerts, setAlerts] = useState(MOCK_ALERTS)
  const [filter, setFilter] = useState('all') // 'all' | 'critical' | 'warning' | 'info'

  // Critical alerts placed first
  const sortedAlerts = [...alerts].sort((a, b) => {
    if (a.resolved !== b.resolved) return a.resolved ? 1 : -1
    if (a.severity === 'critical' && b.severity !== 'critical') return -1
    if (a.severity !== 'critical' && b.severity === 'critical') return 1
    return new Date(b.timestamp) - new Date(a.timestamp)
  })

  const filteredAlerts = sortedAlerts.filter((a) => {
    if (filter === 'all') return true
    return a.severity === filter
  })

  const handleResolve = (id) => {
    setAlerts((prev) =>
      prev.map((a) => (a.id === id ? { ...a, resolved: !a.resolved } : a))
    )
  }

  const criticalCount = alerts.filter((a) => a.severity === 'critical' && !a.resolved).length
  const warningCount = alerts.filter((a) => a.severity === 'warning' && !a.resolved).length

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-border-subtle">
        <div>
          <h1 className="heading-4 sm:heading-3 text-white">Alerts & Incidents</h1>
          <p className="caption-1 text-text-secondary mt-1">
            Real time detection queue ordered by criticality and remaining useful life
          </p>
        </div>

        {/* Severity Filter Pills */}
        <div className="flex items-center gap-1.5 p-1 rounded-xl bg-bg-card border border-border-subtle">
          {['all', 'critical', 'warning', 'info'].map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-3 py-1.5 rounded-lg caption-4 transition-colors capitalize ${
                filter === f
                  ? 'bg-white text-black font-semibold'
                  : 'text-text-secondary hover:text-white'
              }`}
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      {/* KPI Summary */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="card p-5">
          <div className="flex items-center justify-between">
            <span className="caption-1 text-text-secondary">Unresolved Critical</span>
            <AlertCircle className="w-4 h-4 text-status-critical" />
          </div>
          <div className="mt-2 heading-4 mono text-status-critical font-semibold">
            {criticalCount}
          </div>
          <p className="caption-4 text-text-muted mt-1">Requires immediate work stoppage</p>
        </div>

        <div className="card p-5">
          <div className="flex items-center justify-between">
            <span className="caption-1 text-text-secondary">Warning Alerts</span>
            <AlertTriangle className="w-4 h-4 text-status-warning" />
          </div>
          <div className="mt-2 heading-4 mono text-status-warning font-semibold">
            {warningCount}
          </div>
          <p className="caption-4 text-text-muted mt-1">Inspection due within 48 hours</p>
        </div>

        <div className="card p-5">
          <div className="flex items-center justify-between">
            <span className="caption-1 text-text-secondary">Total Logged</span>
            <Info className="w-4 h-4 text-text-muted" />
          </div>
          <div className="mt-2 heading-4 mono text-white font-semibold">
            {alerts.length}
          </div>
          <p className="caption-4 text-text-muted mt-1">Historical and active records</p>
        </div>
      </div>

      {/* Alert Feed (Critical First) */}
      <div className="card overflow-hidden">
        <div className="p-4 sm:p-5 border-b border-border-subtle flex items-center justify-between">
          <h2 className="title-3 text-white">Event Queue</h2>
          <span className="caption-4 text-text-muted mono">
            {filteredAlerts.length} events matching filter
          </span>
        </div>

        <div className="divide-y divide-border-subtle">
          {filteredAlerts.map((alert) => (
            <div
              key={alert.id}
              className={`p-5 transition-colors flex flex-col lg:flex-row lg:items-center justify-between gap-4 ${
                alert.resolved
                  ? 'bg-bg-card/40 opacity-60'
                  : alert.severity === 'critical'
                  ? 'bg-status-critical/5 hover:bg-status-critical/10'
                  : 'hover:bg-bg-raised/40'
              }`}
            >
              <div className="space-y-1.5 max-w-3xl">
                <div className="flex flex-wrap items-center gap-2">
                  <StatusBadge status={alert.severity} size="sm" />
                  <span className="title-4 text-white font-semibold">
                    {alert.machine_name}
                  </span>
                  <span className="caption-5 mono px-2 py-0.5 rounded bg-bg-raised text-text-muted border border-border-subtle">
                    M-0{alert.machine_id}
                  </span>
                  <span className="caption-5 text-text-muted">
                    {new Date(alert.timestamp).toLocaleString()}
                  </span>
                </div>

                <p className="body-6 text-text-primary leading-relaxed">
                  {alert.description}
                </p>

                {alert.recommended_action && (
                  <div className="caption-4 text-text-secondary flex items-start gap-1.5 pt-1">
                    <span className="text-white font-medium">Recommended:</span>
                    <span>{alert.recommended_action}</span>
                  </div>
                )}
              </div>

              {/* Actions */}
              <div className="flex items-center gap-3 flex-shrink-0 pt-2 lg:pt-0">
                <Link
                  to={`/app/machines/${alert.machine_id}`}
                  className="btn-secondary px-3 py-1.5 button-xsm gap-1.5"
                >
                  <span>Inspect</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </Link>

                <button
                  onClick={() => handleResolve(alert.id)}
                  className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg button-xsm transition-colors border ${
                    alert.resolved
                      ? 'bg-bg-raised text-text-muted border-border-subtle hover:text-white'
                      : 'bg-white text-black border-transparent hover:bg-neutral-200'
                  }`}
                >
                  <Check className="w-3.5 h-3.5" />
                  <span>{alert.resolved ? 'Mark active' : 'Resolve'}</span>
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export { Alerts }
