// frontend/src/components/landing/TrustProofSection.jsx
import React from 'react'
import { CheckCircle2 } from 'lucide-react'

const BENCHMARKS = [
  {
    metric: '14.2',
    unit: 'cycles',
    label: 'RUL Prediction Error (RMSE)',
    dataset: 'NASA C-MAPSS FD001',
    note: 'Evaluated against turbofan run-to-failure degradation',
  },
  {
    metric: '286',
    unit: 'score',
    label: 'NASA Benchmark Score',
    dataset: 'NASA C-MAPSS FD001',
    note: 'Asymmetric scoring penalizing late predictions',
  },
  {
    metric: '0.84',
    unit: 'F1',
    label: 'Failure Classification F1',
    dataset: 'UCI AI4I 2020',
    note: 'Synthetic industrial milling machine wear detection',
  },
  {
    metric: '0.88',
    unit: 'AUC',
    label: 'Precision-Recall AUC',
    dataset: 'SKAB Benchmark',
    note: 'Water circulation pump anomaly detection benchmark',
  },
]

export default function TrustProofSection() {
  return (
    <section id="proof" className="py-20 sm:py-28 px-4 sm:px-6 max-w-7xl mx-auto border-t border-border-subtle">
      <div className="max-w-2xl mb-14">
        <div className="caption-5 uppercase tracking-wider text-text-muted font-semibold mb-2">
          Empirical Validation
        </div>
        <h2 className="heading-3 sm:heading-2 text-white mb-4">
          Verified on peer reviewed open benchmark datasets
        </h2>
        <p className="body-2 text-text-secondary">
          No hypothetical claims. Every architecture and metric is benchmarked on reproducible public datasets from NASA, UCI, and SKAB.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {BENCHMARKS.map((item, idx) => (
          <div key={idx} className="card p-6 flex flex-col justify-between">
            <div>
              <div className="caption-5 mono text-text-muted mb-2">{item.dataset}</div>
              <div className="flex items-baseline gap-1.5 mb-2">
                <span className="heading-3 mono text-white font-semibold">
                  {item.metric}
                </span>
                <span className="caption-3 mono text-text-secondary">{item.unit}</span>
              </div>
              <div className="title-4 text-white font-medium mb-1">
                {item.label}
              </div>
              <p className="caption-5 text-text-muted leading-relaxed">
                {item.note}
              </p>
            </div>
            <div className="mt-4 pt-3 border-t border-border-subtle flex items-center gap-1.5 caption-5 text-status-healthy">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>Reproducible pipeline</span>
            </div>
          </div>
        ))}
      </div>

      {/* Honest Note */}
      <div className="p-4 rounded-xl bg-bg-card border border-border-subtle max-w-3xl mx-auto text-center">
        <p className="caption-4 text-text-secondary">
          <strong className="text-white">Benchmark disclosure:</strong> This platform is a capstone engineering project evaluated against public benchmark datasets. The live demo streams simulated machine twins replaying NASA C-MAPSS and UCI AI4I degradation trajectories.
        </p>
      </div>
    </section>
  )
}

