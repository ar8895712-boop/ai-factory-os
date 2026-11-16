// ==============================================================
// frontend/src/components/HealthBadge.jsx — Status & Health Pill
// ==============================================================
import React from 'react'

export function HealthBadge({ healthScore = 100, status = 'idle', size = 'md' }) {
  let colorBg = 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
  let dotBg = 'bg-emerald-400'

  if (status === 'critical' || healthScore < 30) {
    colorBg = 'bg-rose-500/10 text-rose-400 border-rose-500/30'
    dotBg = 'bg-rose-400'
  } else if (status === 'warning' || healthScore < 60) {
    colorBg = 'bg-amber-500/10 text-amber-400 border-amber-500/30'
    dotBg = 'bg-amber-400'
  } else if (status === 'idle') {
    colorBg = 'bg-slate-500/10 text-slate-400 border-slate-500/30'
    dotBg = 'bg-slate-400'
  }

  const sizeClass = size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-3 py-1 text-sm'

  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full border font-medium ${colorBg} ${sizeClass}`}>
      <span className={`w-2 h-2 rounded-full ${dotBg} animate-pulse`} />
      <span className="capitalize">{status}</span>
      <span className="opacity-75 font-mono">({healthScore.toFixed(0)}%)</span>
    </span>
  )
}

