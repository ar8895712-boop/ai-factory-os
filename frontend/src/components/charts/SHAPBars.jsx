// frontend/src/components/charts/SHAPBars.jsx
import React from 'react'

export default function SHAPBars({ features = [] }) {
  if (!features || features.length === 0) {
    return (
      <div className="p-4 rounded-lg bg-bg-raised/40 border border-border-subtle caption-4 text-text-muted text-center">
        No feature attribution explanation available for this cycle
      </div>
    )
  }

  // Find max absolute value to normalize bar widths
  const maxAbs = Math.max(...features.map((f) => Math.abs(f.value)), 0.01)

  return (
    <div className="space-y-2.5">
      {features.map((f, idx) => {
        const pct = Math.min(100, Math.round((Math.abs(f.value) / maxAbs) * 100))
        const isRiskIncreasing = f.value < 0 || f.direction === 'positive'

        return (
          <div key={idx} className="space-y-1">
            <div className="flex justify-between items-center caption-4">
              <span className="mono text-white font-medium">{f.feature}</span>
              <span className="mono text-text-muted text-xs">
                {f.value > 0 ? `+${f.value.toFixed(2)}` : f.value.toFixed(2)}
              </span>
            </div>
            <div className="h-2 w-full bg-bg-raised rounded-full overflow-hidden flex">
              <div
                style={{ width: `${pct}%` }}
                className={`h-full rounded-full transition-all duration-500 ${
                  isRiskIncreasing ? 'bg-status-critical' : 'bg-status-info'
                }`}
              />
            </div>
          </div>
        )
      })}
      <div className="flex justify-between items-center pt-2 caption-5 text-text-muted">
        <span className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-status-critical" />
          <span>Elevates failure risk</span>
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-status-info" />
          <span>Stabilizing feature</span>
        </span>
      </div>
    </div>
  )
}

