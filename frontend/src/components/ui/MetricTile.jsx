// frontend/src/components/ui/MetricTile.jsx
import React from 'react'
import FormulaPopover from './FormulaPopover.jsx'

export default function MetricTile({
  label,
  value,
  unit,
  sublabel,
  formula,
  breakdown,
  status, // 'healthy' | 'warning' | 'critical' | 'info'
  icon: Icon,
  className = '',
}) {
  const statusColor = {
    healthy:  'text-status-healthy',
    warning:  'text-status-warning',
    critical: 'text-status-critical',
    info:     'text-status-info',
  }[status] || 'text-white'

  return (
    <div className={`card p-4 sm:p-5 flex flex-col justify-between ${className}`}>
      <div className="flex items-center justify-between gap-2 mb-2">
        <span className="caption-1 text-text-secondary truncate">{label}</span>
        <div className="flex items-center gap-1.5 flex-shrink-0">
          {formula && (
            <FormulaPopover title={`${label} formula`} formula={formula} breakdown={breakdown} />
          )}
          {Icon && <Icon className="w-4 h-4 text-text-muted" aria-hidden="true" />}
        </div>
      </div>

      <div className="flex items-baseline gap-1.5">
        <span className={`heading-4 mono font-semibold tracking-tight ${statusColor}`}>
          {value}
        </span>
        {unit && <span className="caption-4 text-text-muted mono">{unit}</span>}
      </div>

      {sublabel && (
        <div className="mt-2 pt-2 border-t border-border-subtle caption-4 text-text-muted truncate">
          {sublabel}
        </div>
      )}
    </div>
  )
}

