// frontend/src/components/landing/BenefitsSection.jsx
import React from 'react'
import { ShieldCheck, Cpu, Sliders, IndianRupee } from 'lucide-react'

const BENEFITS = [
  {
    icon: Cpu,
    title: 'Remaining useful life forecasting',
    lead: 'Act weeks before failure occurs.',
    description: 'LSTM neural networks compute cycle by cycle remaining life across each monitored subsystem so maintenance teams can order components before unscheduled stoppages happen.',
  },
  {
    icon: IndianRupee,
    title: 'Financial exposure in Indian Rupees',
    lead: 'Translate technical risk into boardroom economics.',
    description: 'Every alert quantifies production downtime loss, energy waste, and delay penalties using your own plant tariff assumptions with visible calculation formulas.',
  },
  {
    icon: Sliders,
    title: 'Live what if scenario simulation',
    lead: 'Test intervention strategies risk free.',
    description: 'Simulate the production, energy, and financial impact of shutting down a machine, throttling speed by 15 percent, or shifting workload to a standby unit before taking physical action.',
  },
  {
    icon: ShieldCheck,
    title: 'Transparent SHAP root cause explanations',
    lead: 'No black box recommendations.',
    description: 'Every risk score breaks down into top contributing sensors and directional impacts, allowing technicians to inspect the physical reason behind any warning.',
  },
]

export default function BenefitsSection() {
  return (
    <section id="benefits" className="py-20 sm:py-28 px-4 sm:px-6 max-w-7xl mx-auto">
      <div className="max-w-2xl mb-14">
        <div className="caption-5 uppercase tracking-wider text-text-muted font-semibold mb-2">
          Core Capabilities
        </div>
        <h2 className="heading-3 sm:heading-2 text-white mb-4">
          Built for the reality of industrial maintenance
        </h2>
        <p className="body-2 text-text-secondary">
          Traditional maintenance schedules waste component life or react too late. AI Factory OS bridges live machine telemetry with business consequences.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {BENEFITS.map((item, idx) => {
          const Icon = item.icon
          return (
            <div
              key={idx}
              className="card p-6 sm:p-8 flex flex-col justify-between hover:border-neutral-700 transition-colors duration-300"
            >
              <div>
                <div className="w-10 h-10 rounded-xl bg-bg-raised border border-border-default flex items-center justify-center text-white mb-5">
                  <Icon className="w-5 h-5" aria-hidden="true" />
                </div>
                <h3 className="title-2 text-white font-semibold mb-2">
                  {item.title}
                </h3>
                <div className="body-3 text-text-primary font-medium mb-3">
                  {item.lead}
                </div>
                <p className="caption-1 text-text-secondary leading-relaxed">
                  {item.description}
                </p>
              </div>
            </div>
          )
        })}
      </div>
    </section>
  )
}

