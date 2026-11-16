// frontend/src/components/landing/HowItWorksSection.jsx
import React from 'react'
import { ArrowRight } from 'lucide-react'

const STEPS = [
  {
    step: '01',
    title: 'Stream telemetry into the digital twin',
    description: 'Connect sensor feeds across temperature, pressure, vibration, and rotational speeds. The twin maintains a live state representation of each physical asset.',
  },
  {
    step: '02',
    title: 'Predict degradation and financial loss',
    description: 'Machine learning models predict remaining useful cycles and anomaly scores, combining them with your plant economic parameters to quantify loss in Rupees.',
  },
  {
    step: '03',
    title: 'Simulate and execute optimal actions',
    description: 'Test operational interventions in the simulation engine, inspect root causes with SHAP explanations, and coordinate repairs with the plant engineer assistant.',
  },
]

export default function HowItWorksSection() {
  return (
    <section id="how-it-works" className="py-20 sm:py-28 px-4 sm:px-6 max-w-7xl mx-auto border-t border-border-subtle">
      <div className="max-w-2xl mb-14">
        <div className="caption-5 uppercase tracking-wider text-text-muted font-semibold mb-2">
          Architecture
        </div>
        <h2 className="heading-3 sm:heading-2 text-white mb-4">
          From live sensor readings to decisive action in three steps
        </h2>
        <p className="body-2 text-text-secondary">
          A continuous loop from edge data collection to executive loss estimation.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 relative">
        {STEPS.map((item, idx) => (
          <div
            key={idx}
            className="card p-6 sm:p-8 flex flex-col justify-between relative group"
          >
            <div>
              <div className="heading-4 mono text-text-muted mb-4 group-hover:text-white transition-colors">
                {item.step}
              </div>
              <h3 className="heading-6 text-white mb-3">
                {item.title}
              </h3>
              <p className="caption-1 text-text-secondary leading-relaxed">
                {item.description}
              </p>
            </div>
            {idx < STEPS.length - 1 && (
              <div className="hidden md:block absolute -right-3 top-1/2 -translate-y-1/2 z-10 text-border-default">
                <ArrowRight className="w-5 h-5 text-border-default" />
              </div>
            )}
          </div>
        ))}
      </div>
    </section>
  )
}

