// frontend/src/components/ui/EmptyState.jsx
import React from 'react'
import { Inbox, RefreshCw } from 'lucide-react'
import Button from './Button.jsx'

export default function EmptyState({
  title = 'No data available',
  description = 'There are currently no records matching this criteria.',
  icon: Icon = Inbox,
  actionLabel,
  onAction,
}) {
  return (
    <div className="card p-8 sm:p-12 text-center flex flex-col items-center justify-center">
      <div className="w-12 h-12 rounded-xl bg-bg-raised border border-border-default flex items-center justify-center text-text-muted mb-4">
        <Icon className="w-6 h-6" aria-hidden="true" />
      </div>
      <h3 className="title-2 text-white mb-1.5">{title}</h3>
      <p className="caption-2 text-text-secondary max-w-sm mb-6">{description}</p>
      {actionLabel && onAction && (
        <Button variant="secondary" size="sm" onClick={onAction} icon={RefreshCw}>
          {actionLabel}
        </Button>
      )}
    </div>
  )
}

