// frontend/src/components/landing/FAQSection.jsx
import React, { useState } from 'react'
import { ChevronDown } from 'lucide-react'

const FAQS = [
  {
    q: 'What datasets are used to train and validate the predictive models?',
    a: 'The platform uses three gold standard industrial benchmarks: NASA C-MAPSS FD001 (100 turbofan run-to-failure engines), UCI AI4I 2020 Predictive Maintenance Dataset (10,000 synthetic CNC milling records), and the SKAB Water Circulation Pump benchmark. No synthetic customer claims are made.',
  },
  {
    q: 'How is Remaining Useful Life calculated?',
    a: 'RUL is predicted cycle by cycle using a multi-layer Long Short-Term Memory (LSTM) neural network trained on sensor degradation trajectories. The output estimates remaining operating cycles before critical thresholds are breached.',
  },
  {
    q: 'Where do the business loss numbers in Indian Rupees come from?',
    a: 'Loss figures are derived from three transparent inputs: downtime hours multiplied by your hourly production loss rate, energy wasted during degraded cycles multiplied by your local power tariff, and delay penalties for scheduled deliveries.',
  },
  {
    q: 'Can I customize the loss calculation assumptions?',
    a: 'Yes. Every loss figure is governed by editable parameters (hourly downtime rate, energy tariff per kWh, penalty per delayed order) accessible in the Assumptions settings drawer. Hovering over any metric displays the exact formula used.',
  },
  {
    q: 'How does the What If simulation engine work?',
    a: 'The simulator lets you compare a baseline run-to-failure scenario against operational interventions: immediate shutdown for overhaul, 15% speed derating, or workload re-routing. It projects the resulting changes in downtime, power consumption, and net savings.',
  },
  {
    q: 'What is the role of the Engineer Assistant?',
    a: 'The assistant answers questions about machine health in plain language using retrieval over live telemetry, SHAP explanations, and historical incident logs. It explains the physical sensor causes behind any alert and never fabricates telemetry.',
  },
  {
    q: 'Does this platform require real sensor hardware to test?',
    a: 'No. The interactive demo features a built-in simulation player that replays degradation cycles with live step, pause, and speed controls, mirroring a real SCADA or OPC UA sensor stream.',
  },
  {
    q: 'Can the mock data layer be replaced with real factory IoT endpoints?',
    a: 'Yes. All components consume typed data interfaces aligned directly with FastAPI backend routes. Connecting real MQTT, Modbus, or REST feeds requires modifying only the API adapter layer.',
  },
]

export default function FAQSection() {
  const [openIdx, setOpenIdx] = useState(null)

  const toggle = (idx) => {
    setOpenIdx(openIdx === idx ? null : idx)
  }

  // Schema for SEO / AEO
  const faqSchema = {
    '@context': 'https://schema.org',
    '@type': 'FAQPage',
    mainEntity: FAQS.map((item) => ({
      '@type': 'Question',
      name: item.q,
      acceptedAnswer: {
        '@type': 'Answer',
        text: item.a,
      },
    })),
  }

  return (
    <section id="faq" className="py-20 sm:py-28 px-4 sm:px-6 max-w-4xl mx-auto border-t border-border-subtle">
      {/* Schema Injection */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(faqSchema) }}
      />

      <div className="text-center max-w-xl mx-auto mb-14">
        <div className="caption-5 uppercase tracking-wider text-text-muted font-semibold mb-2">
          Frequently Asked Questions
        </div>
        <h2 className="heading-3 sm:heading-2 text-white mb-4">
          Answers to technical and operational questions
        </h2>
        <p className="body-2 text-text-secondary">
          Everything you need to know about models, assumptions, and deployment.
        </p>
      </div>

      <div className="space-y-3">
        {FAQS.map((item, idx) => {
          const isOpen = openIdx === idx
          return (
            <div
              key={idx}
              className="card overflow-hidden transition-colors border border-border-subtle hover:border-border-default"
            >
              <button
                type="button"
                onClick={() => toggle(idx)}
                className="w-full p-5 text-left flex items-center justify-between gap-4 focus-visible:ring-1 focus-visible:ring-white"
                aria-expanded={isOpen}
              >
                <span className="title-3 text-white font-medium">{item.q}</span>
                <ChevronDown
                  className={`w-4 h-4 text-text-muted transition-transform duration-300 flex-shrink-0 ${
                    isOpen ? 'rotate-180 text-white' : ''
                  }`}
                />
              </button>
              {isOpen && (
                <div className="px-5 pb-5 pt-1 border-t border-border-subtle/50">
                  <p className="caption-1 text-text-secondary leading-relaxed">
                    {item.a}
                  </p>
                </div>
              )}
            </div>
          )
        })}
      </div>
    </section>
  )
}

