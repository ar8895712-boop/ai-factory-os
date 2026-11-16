// frontend/src/components/ui/StatusBadge.jsx
import React from 'react'
import { CheckCircle2, AlertTriangle, AlertCircle, Info } from 'lucide-react'

const VARIANTS = {
  healthy: {
    bg: 'bg-status-healthy/10',
    border: 'border-status-healthy/30',
    text: 'text-status-healthy',
    icon: CheckCircle2,
    defaultLabel: 'Healthy',
  },
  warning: {
    bg: 'bg-status-warning/10',
    border: 'border-status-warning/30',
    text: 'text-status-warning',
    icon: AlertTriangle,
    defaultLabel: 'Warning',
  },
  critical: {
    bg: 'bg-status-critical/10',
    border: 'border-status-critical/30',
    text: 'text-status-critical',
    icon: AlertCircle,
    defaultLabel: 'Critical',
  },
  info: {
    bg: 'bg-status-info/10',
    border: 'border-status-info/30',
    text: 'text-status-info',
    icon: Info,
    defaultLabel: 'Info',
  },
}

export default function StatusBadge({
  status = 'healthy',
  label,
  size = 'md',
  className = '',
}) {
  const normalized = String(status).toLowerCase()
  const config = VARIANTS[normalized] || VARIANTS.info
  const Icon = config.icon
  const displayLabel = label || config.defaultLabel

  const sizeClasses =
    size === 'sm'
      ? 'px-2 py-0.5 text-xs gap-1'
      : 'px-2.5 py-1 caption-4 gap-1.5'

  return (
    <span
      className={`inline-flex items-center font-medium rounded-full border ${config.bg} ${config.border} ${config.text} ${sizeClasses} ${className}`}
    >
      <Icon className={size === 'sm' ? 'w-3 h-3' : 'w-3.5 h-3.5'} aria-hidden="true" />
      <span>{displayLabel}</span>
    </span>
  )
}

