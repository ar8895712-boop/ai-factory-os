// frontend/src/components/ui/Skeleton.jsx
import React from 'react'

export function Skeleton({ className = '' }) {
  return <div className={`skeleton ${className}`} />
}

export function MetricTileSkeleton() {
  return (
    <div className="card p-5 space-y-3">
      <div className="flex justify-between items-center">
        <Skeleton className="h-4 w-24" />
        <Skeleton className="h-4 w-4 rounded-full" />
      </div>
      <Skeleton className="h-8 w-32" />
      <Skeleton className="h-3 w-40" />
    </div>
  )
}

export function CardSkeleton({ lines = 3 }) {
  return (
    <div className="card p-5 space-y-4">
      <Skeleton className="h-5 w-40" />
      <div className="space-y-2">
        {Array.from({ length: lines }).map((_, i) => (
          <Skeleton key={i} className="h-4 w-full" />
        ))}
      </div>
    </div>
  )
}

export function TableSkeleton({ rows = 4, cols = 4 }) {
  return (
    <div className="card p-4 space-y-3">
      <div className="flex gap-4 pb-2 border-b border-border-subtle">
        {Array.from({ length: cols }).map((_, i) => (
          <Skeleton key={i} className="h-4 flex-1" />
        ))}
      </div>
      {Array.from({ length: rows }).map((_, r) => (
        <div key={r} className="flex gap-4 py-2 border-b border-border-subtle/50">
          {Array.from({ length: cols }).map((_, c) => (
            <Skeleton key={c} className="h-4 flex-1" />
          ))}
        </div>
      ))}
    </div>
  )
}

