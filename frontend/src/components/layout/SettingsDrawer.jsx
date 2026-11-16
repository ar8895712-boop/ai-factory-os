// frontend/src/components/layout/SettingsDrawer.jsx
import React from 'react'
import { X, SlidersHorizontal, RotateCcw } from 'lucide-react'

export default function SettingsDrawer({
  isOpen,
  onClose,
  assumptions,
  onUpdateAssumptions,
  onResetAssumptions,
}) {
  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 overflow-hidden">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/70 backdrop-blur-sm transition-opacity"
        onClick={onClose}
      />

      <div className="fixed inset-y-0 right-0 max-w-full flex pl-10">
        <div className="w-screen max-w-md bg-bg-card border-l border-border-default shadow-2xl flex flex-col">
          {/* Header */}
          <div className="p-5 border-b border-border-subtle flex items-center justify-between">
            <div className="flex items-center gap-2">
              <SlidersHorizontal className="w-5 h-5 text-text-primary" />
              <div>
                <h3 className="title-2 text-white">Financial Assumptions</h3>
                <p className="caption-4 text-text-muted">
                  Parameters used across loss calculations
                </p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-text-muted hover:text-white hover:bg-bg-raised transition-colors"
              aria-label="Close settings"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Form Content */}
          <div className="p-6 space-y-6 flex-1 overflow-y-auto">
            {/* Loss per Hour */}
            <div>
              <label className="block title-4 text-white mb-1.5">
                Production Loss Rate (₹ per hour)
              </label>
              <div className="relative">
                <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-text-muted mono">
                  ₹
                </span>
                <input
                  type="number"
                  value={assumptions.loss_per_hour_inr}
                  onChange={(e) =>
                    onUpdateAssumptions({
                      ...assumptions,
                      loss_per_hour_inr: Number(e.target.value) || 0,
                    })
                  }
                  className="w-full pl-8 pr-4 py-2.5 bg-bg-raised border border-border-default rounded-lg text-white mono text-sm focus:border-border-default focus:ring-1 focus:ring-white"
                />
              </div>
              <p className="caption-4 text-text-muted mt-1">
                Standard downtime cost per operating line hour.
              </p>
            </div>

            {/* Energy Tariff */}
            <div>
              <label className="block title-4 text-white mb-1.5">
                Energy Tariff (₹ per kWh)
              </label>
              <div className="relative">
                <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-text-muted mono">
                  ₹
                </span>
                <input
                  type="number"
                  step="0.1"
                  value={assumptions.energy_tariff_inr_per_kwh}
                  onChange={(e) =>
                    onUpdateAssumptions({
                      ...assumptions,
                      energy_tariff_inr_per_kwh: Number(e.target.value) || 0,
                    })
                  }
                  className="w-full pl-8 pr-4 py-2.5 bg-bg-raised border border-border-default rounded-lg text-white mono text-sm focus:border-border-default focus:ring-1 focus:ring-white"
                />
              </div>
              <p className="caption-4 text-text-muted mt-1">
                Industrial grid power cost per kilowatt hour.
              </p>
            </div>

            {/* Delay Penalty */}
            <div>
              <label className="block title-4 text-white mb-1.5">
                Delay Penalty per Order (₹)
              </label>
              <div className="relative">
                <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-text-muted mono">
                  ₹
                </span>
                <input
                  type="number"
                  value={assumptions.delay_penalty_per_order_inr}
                  onChange={(e) =>
                    onUpdateAssumptions({
                      ...assumptions,
                      delay_penalty_per_order_inr: Number(e.target.value) || 0,
                    })
                  }
                  className="w-full pl-8 pr-4 py-2.5 bg-bg-raised border border-border-default rounded-lg text-white mono text-sm focus:border-border-default focus:ring-1 focus:ring-white"
                />
              </div>
              <p className="caption-4 text-text-muted mt-1">
                Contractual penalty for late delivery due to unpredicted stoppages.
              </p>
            </div>

            {/* Explanation box */}
            <div className="p-4 rounded-xl bg-bg-raised/60 border border-border-subtle">
              <h4 className="title-4 text-white mb-2">Calculation Transparency</h4>
              <p className="caption-4 text-text-secondary leading-relaxed">
                Total Business Loss = (Downtime Hours × Hourly Rate) + (Wasted kWh × Tariff) + (Delayed Orders × SLA Penalty).
                All models are transparent: adjust values to match your specific plant profile.
              </p>
            </div>
          </div>

          {/* Footer with Reset */}
          <div className="p-5 border-t border-border-subtle flex items-center justify-between bg-bg-raised/30">
            <button
              onClick={onResetAssumptions}
              className="inline-flex items-center gap-1.5 px-3 py-2 text-text-muted hover:text-white transition-colors title-5"
            >
              <RotateCcw className="w-4 h-4" />
              <span>Reset to defaults</span>
            </button>
            <button
              onClick={onClose}
              className="btn-primary py-2 px-5 text-sm"
            >
              Done
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

