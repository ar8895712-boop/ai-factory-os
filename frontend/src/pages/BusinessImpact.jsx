// frontend/src/pages/BusinessImpact.jsx — Financial Risk & Loss Exposure
import React from 'react'
import { useOutletContext } from 'react-router-dom'
import {
  IndianRupee,
  SlidersHorizontal,
  TrendingDown,
  ShieldCheck,
  Zap,
  Clock,
  AlertOctagon,
  ArrowRight
} from 'lucide-react'
import MetricTile from '../components/ui/MetricTile.jsx'
import FormulaPopover from '../components/ui/FormulaPopover.jsx'
import StatusBadge from '../components/ui/StatusBadge.jsx'
import { MOCK_BUSINESS_IMPACT, DEFAULT_ASSUMPTIONS } from '../mocks/index.js'

export default function BusinessImpact(props) {
  const context = useOutletContext() || {}
  const assumptions = context.assumptions || DEFAULT_ASSUMPTIONS
  const onOpenSettings = context.onOpenSettings || (() => {})

  // Compute live values dynamically using user editable assumptions!
  const impactData = MOCK_BUSINESS_IMPACT.map((item) => {
    const downtime = item.estimated_downtime_hours
    const prodLoss = Math.round(downtime * assumptions.loss_per_hour_inr)
    const energyWasted = Math.round(
      downtime * (assumptions.machine_power_kw || 45) * assumptions.energy_tariff_inr_per_kwh
    )
    const delayPenalty = Math.round(
      downtime * (assumptions.avg_orders_per_hour || 1.3) * assumptions.delay_penalty_per_order_inr
    )
    const totalLoss = prodLoss + energyWasted + delayPenalty
    const netSaving = totalLoss - item.preventive_maintenance_cost_inr

    return {
      ...item,
      production_loss_inr: prodLoss,
      energy_wasted_inr: energyWasted,
      delay_penalty_inr: delayPenalty,
      total_estimated_loss_inr: totalLoss,
      savings_vs_breakdown_inr: netSaving,
    }
  })

  const totalExposure = impactData.reduce((acc, i) => acc + i.total_estimated_loss_inr, 0)
  const totalPreventiveCost = impactData.reduce((acc, i) => acc + i.preventive_maintenance_cost_inr, 0)
  const netSavings = totalExposure - totalPreventiveCost

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-border-subtle">
        <div>
          <h1 className="heading-4 sm:heading-3 text-white">Business Impact & Financial Loss</h1>
          <p className="caption-1 text-text-secondary mt-1">
            Downtime cost quantification in Indian Rupees based on current machine health risk
          </p>
        </div>

        <button
          onClick={onOpenSettings}
          className="btn-secondary px-3.5 py-2 button-sm gap-2"
        >
          <SlidersHorizontal className="w-4 h-4 text-text-secondary" />
          <span>Edit Financial Assumptions</span>
        </button>
      </div>

      {/* Top Level Financial KPIs */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <MetricTile
          label="Total Unmitigated Loss Exposure"
          value={`₹${totalExposure.toLocaleString('en-IN')}`}
          status="critical"
          sublabel="Production loss + energy waste + order delay penalties"
          formula="Σ (Downtime × Rate + Wasted kWh × Tariff + Delayed Orders × Penalty)"
          breakdown={[
            { label: 'Loss rate', value: `₹${assumptions.loss_per_hour_inr}/hr` },
            { label: 'Energy tariff', value: `₹${assumptions.energy_tariff_inr_per_kwh}/kWh` },
            { label: 'Delay penalty', value: `₹${assumptions.delay_penalty_per_order_inr}/order` },
          ]}
          icon={IndianRupee}
        />

        <MetricTile
          label="Preventive Maintenance Cost"
          value={`₹${totalPreventiveCost.toLocaleString('en-IN')}`}
          status="info"
          sublabel="Proactive parts replacement and scheduled servicing"
          formula="Standard OEM overhaul quotation across degraded assets"
          icon={Clock}
        />

        <MetricTile
          label="Net Projected Savings"
          value={`₹${netSavings.toLocaleString('en-IN')}`}
          status="healthy"
          sublabel="Savings realized by taking proactive intervention now"
          formula="Unmitigated Loss Exposure - Preventive Maintenance Cost"
          icon={ShieldCheck}
        />
      </div>

      {/* Per Machine Financial Breakdown Table */}
      <div className="card overflow-hidden">
        <div className="p-5 border-b border-border-subtle flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h2 className="title-3 text-white">Asset Exposure Breakdown</h2>
            <p className="caption-4 text-text-muted">
              Live calculation table (scroll horizontally on mobile devices)
            </p>
          </div>

          <div className="flex items-center gap-2 caption-5 mono text-text-secondary">
            <span>Rate: ₹{assumptions.loss_per_hour_inr.toLocaleString('en-IN')}/hr</span>
            <span>•</span>
            <span>Tariff: ₹{assumptions.energy_tariff_inr_per_kwh}/kWh</span>
          </div>
        </div>

        {/* Responsive Table Container (scrolls inside its container on mobile) */}
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-border-subtle bg-bg-raised/40 caption-4 text-text-muted">
                <th className="py-3 px-4 font-medium">Machine</th>
                <th className="py-3 px-4 font-medium">Status</th>
                <th className="py-3 px-4 font-medium">Est. Downtime</th>
                <th className="py-3 px-4 font-medium">Production Loss</th>
                <th className="py-3 px-4 font-medium">Energy Waste</th>
                <th className="py-3 px-4 font-medium">Delay Penalty</th>
                <th className="py-3 px-4 font-medium">Total Loss</th>
                <th className="py-3 px-4 font-medium">Preventive Cost</th>
                <th className="py-3 px-4 font-medium text-right">Net Savings</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border-subtle">
              {impactData.map((row) => (
                <tr key={row.machine_id} className="hover:bg-bg-raised/30 transition-colors">
                  <td className="py-3.5 px-4">
                    <div className="title-4 text-white font-medium">{row.machine_name}</div>
                    <div className="caption-5 mono text-text-muted">RUL: {row.rul_cycles} cycles</div>
                  </td>
                  <td className="py-3.5 px-4">
                    <StatusBadge status={row.status} size="sm" />
                  </td>
                  <td className="py-3.5 px-4 mono text-sm text-text-secondary">
                    {row.estimated_downtime_hours} hrs
                  </td>
                  <td className="py-3.5 px-4 mono text-sm text-white">
                    ₹{row.production_loss_inr.toLocaleString('en-IN')}
                  </td>
                  <td className="py-3.5 px-4 mono text-sm text-text-secondary">
                    ₹{row.energy_wasted_inr.toLocaleString('en-IN')}
                  </td>
                  <td className="py-3.5 px-4 mono text-sm text-text-secondary">
                    ₹{row.delay_penalty_inr.toLocaleString('en-IN')}
                  </td>
                  <td className="py-3.5 px-4 mono text-sm font-semibold text-status-critical">
                    ₹{row.total_estimated_loss_inr.toLocaleString('en-IN')}
                  </td>
                  <td className="py-3.5 px-4 mono text-sm text-text-secondary">
                    ₹{row.preventive_maintenance_cost_inr.toLocaleString('en-IN')}
                  </td>
                  <td className="py-3.5 px-4 mono text-sm font-semibold text-status-healthy text-right">
                    ₹{row.savings_vs_breakdown_inr.toLocaleString('en-IN')}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Assumptions Transparency Footer */}
      <div className="card p-6 bg-bg-card/70 border border-border-subtle">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1">
            <h3 className="title-3 text-white">Calculation Transparency & Methodology</h3>
            <p className="caption-4 text-text-secondary max-w-2xl leading-relaxed">
              Every financial figure is derived from formula: Production Loss = Downtime Hours × Hourly Rate; Energy Waste = Downtime × kW × Tariff; Delay Penalty = Orders × SLA Penalty. Click any formula trigger or open the Assumptions drawer to tailor values to your facility.
            </p>
          </div>
          <button
            onClick={onOpenSettings}
            className="btn-primary px-4 py-2 button-sm flex-shrink-0"
          >
            Adjust Assumptions
          </button>
        </div>
      </div>
    </div>
  )
}

export { BusinessImpact }
