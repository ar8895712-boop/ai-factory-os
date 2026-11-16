// frontend/src/pages/FactoryMemory.jsx — Institutional Incident Memory & Learned Patterns
import React, { useState } from 'react'
import {
  Database,
  Search,
  Clock,
  IndianRupee,
  Cpu,
  CheckCircle2,
  AlertTriangle,
  Lightbulb
} from 'lucide-react'
import { MOCK_INCIDENTS, getPatternsSummary } from '../mocks/index.js'
import MetricTile from '../components/ui/MetricTile.jsx'
import StatusBadge from '../components/ui/StatusBadge.jsx'

export default function FactoryMemory() {
  const [searchTerm, setSearchTerm] = useState('')
  const patterns = getPatternsSummary()

  const filteredIncidents = MOCK_INCIDENTS.filter((inc) => {
    const term = searchTerm.toLowerCase()
    return (
      inc.machine_name.toLowerCase().includes(term) ||
      inc.root_cause.toLowerCase().includes(term) ||
      inc.resolution.toLowerCase().includes(term) ||
      inc.type.toLowerCase().includes(term)
    )
  })

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-border-subtle">
        <div>
          <h1 className="heading-4 sm:heading-3 text-white">Factory Memory</h1>
          <p className="caption-1 text-text-secondary mt-1">
            Institutional knowledge store connecting past failure patterns to active anomalies
          </p>
        </div>

        {/* Search Input */}
        <div className="relative w-full sm:w-72">
          <Search className="w-4 h-4 text-text-muted absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search incident memory..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-4 py-2 bg-bg-card border border-border-default rounded-lg text-sm text-white placeholder-text-muted focus:ring-1 focus:ring-white"
          />
        </div>
      </div>

      {/* Memory KPIs */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <MetricTile
          label="Total Logged Incidents"
          value={MOCK_INCIDENTS.length}
          sublabel="Resolved failure events in memory database"
          icon={Database}
        />
        <MetricTile
          label="Identified Precursor Patterns"
          value={patterns.length}
          status="info"
          sublabel="Rules synthesized from benchmark datasets"
          icon={Lightbulb}
        />
        <MetricTile
          label="Average Case Similarity"
          value="81%"
          status="healthy"
          sublabel="Embedding match confidence on active alerts"
          icon={Cpu}
        />
      </div>

      {/* Learned Patterns Section */}
      <div className="card p-5">
        <div className="flex items-center gap-2 pb-3 mb-4 border-b border-border-subtle">
          <Lightbulb className="w-5 h-5 text-status-warning" />
          <div>
            <h2 className="title-3 text-white">Patterns The System Has Learned</h2>
            <p className="caption-5 text-text-muted">Extracted decision rules synthesized from NASA C-MAPSS and SKAB training cycles</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {patterns.map((item, idx) => (
            <div
              key={idx}
              className="p-4 rounded-xl bg-bg-raised/70 border border-border-subtle flex flex-col justify-between"
            >
              <div>
                <span className="caption-5 uppercase font-semibold text-text-muted">
                  Rule #{idx + 1}
                </span>
                <p className="title-4 text-white font-medium mt-1 mb-3">
                  {item.pattern}
                </p>
              </div>

              <div className="pt-3 border-t border-border-subtle flex items-center justify-between caption-5 mono text-text-muted">
                <span>Support: {item.support} cases</span>
                <span className="text-status-healthy font-semibold">
                  Confidence: {(item.confidence * 100).toFixed(0)}%
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Historical Incidents & Similar Cases Table */}
      <div className="card overflow-hidden">
        <div className="p-5 border-b border-border-subtle flex items-center justify-between">
          <div>
            <h2 className="title-3 text-white">Historical Failure Cases</h2>
            <p className="caption-4 text-text-muted">
              Matching incident logs with root causes, resolutions, and downtime costs in Rupees
            </p>
          </div>
          <span className="caption-4 text-text-muted mono">
            {filteredIncidents.length} records found
          </span>
        </div>

        <div className="divide-y divide-border-subtle">
          {filteredIncidents.map((inc) => (
            <div key={inc.id} className="p-5 hover:bg-bg-raised/40 transition-colors space-y-3">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div className="flex items-center gap-2.5">
                  <span className="title-4 text-white font-semibold">
                    {inc.machine_name}
                  </span>
                  <StatusBadge status={inc.severity} size="sm" />
                  <span className="caption-5 mono px-2 py-0.5 rounded bg-bg-raised text-text-muted border border-border-subtle">
                    {inc.id}
                  </span>
                </div>
                <div className="flex items-center gap-3 caption-5 mono text-text-muted">
                  <span>Downtime: {inc.downtime_hours} hrs</span>
                  <span>•</span>
                  <span>Impact: ₹{inc.cost_inr.toLocaleString('en-IN')}</span>
                  <span>•</span>
                  <span className="px-2 py-0.5 rounded bg-bg-card border border-border-subtle text-status-healthy">
                    {(inc.similarity_score * 100).toFixed(0)}% match
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-1">
                <div className="p-3 rounded-lg bg-bg-raised/50 border border-border-subtle">
                  <span className="caption-5 uppercase tracking-wider font-semibold text-text-muted block mb-1">
                    Root Cause
                  </span>
                  <p className="caption-2 text-text-primary leading-relaxed">
                    {inc.root_cause}
                  </p>
                </div>

                <div className="p-3 rounded-lg bg-bg-raised/50 border border-border-subtle">
                  <span className="caption-5 uppercase tracking-wider font-semibold text-text-muted block mb-1">
                    Applied Resolution
                  </span>
                  <p className="caption-2 text-text-primary leading-relaxed">
                    {inc.resolution}
                  </p>
                </div>
              </div>

              <div className="caption-5 text-text-muted flex flex-wrap items-center gap-3 pt-1">
                <span>Dataset reference: {inc.dataset_match}</span>
                <span>•</span>
                <span>Insight: {inc.lessons_learned}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

