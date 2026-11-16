// frontend/src/components/ui/FormulaPopover.jsx
import React, { useState, useRef, useEffect } from 'react'
import { HelpCircle, X } from 'lucide-react'

export default function FormulaPopover({
  title = 'Calculation formula',
  formula = '',
  breakdown = [],
  children,
}) {
  const [isOpen, setIsOpen] = useState(false)
  const containerRef = useRef(null)

  useEffect(() => {
    function handleClickOutside(event) {
      if (containerRef.current && !containerRef.current.contains(event.target)) {
        setIsOpen(false)
      }
    }
    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside)
      return () => document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [isOpen])

  return (
    <div className="relative inline-flex items-center" ref={containerRef}>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        onMouseEnter={() => setIsOpen(true)}
        className="text-text-muted hover:text-white transition-colors p-0.5 rounded focus-visible:ring-1 focus-visible:ring-white"
        aria-label="View calculation formula"
        title="View calculation formula"
      >
        {children || <HelpCircle className="w-3.5 h-3.5" />}
      </button>

      {isOpen && (
        <div
          role="dialog"
          aria-label={title}
          className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-72 p-3.5 bg-bg-card border border-border-default rounded-xl shadow-xl z-50 text-left"
        >
          <div className="flex items-center justify-between pb-2 mb-2 border-b border-border-subtle">
            <span className="caption-3 text-white font-medium">{title}</span>
            <button
              onClick={() => setIsOpen(false)}
              className="text-text-muted hover:text-white"
              aria-label="Close"
            >
              <X className="w-3 h-3" />
            </button>
          </div>

          {formula && (
            <div className="p-2 mb-2 rounded bg-bg-raised/70 border border-border-subtle mono text-xs text-text-primary break-all">
              {formula}
            </div>
          )}

          {breakdown.length > 0 && (
            <div className="space-y-1 caption-5 text-text-secondary">
              {breakdown.map((item, idx) => (
                <div key={idx} className="flex justify-between items-center py-0.5">
                  <span className="text-text-muted">{item.label}:</span>
                  <span className="mono text-white">{item.value}</span>
                </div>
              ))}
            </div>
          )}
          <div className="mt-2 pt-2 border-t border-border-subtle caption-5 text-text-muted">
            Configurable in Assumptions settings drawer.
          </div>
        </div>
      )}
    </div>
  )
}

