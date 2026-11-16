// frontend/src/components/landing/HeroSection.jsx
import React from 'react'
import { Link } from 'react-router-dom'
import { ArrowRight, CheckCircle2, AlertTriangle, AlertCircle, TrendingUp } from 'lucide-react'
import AnomalyTrendChart from '../charts/AnomalyTrendChart.jsx'
import Sparkline from '../charts/Sparkline.jsx'

const MOCK_ANOMALY_TREND = [
  { cycle: 150, score: 0.12 },
  { cycle: 160, score: 0.18 },
  { cycle: 170, score: 0.24 },
  { cycle: 180, score: 0.38 },
  { cycle: 190, score: 0.52 },
  { cycle: 200, score: 0.71 },
  { cycle: 210, score: 0.89 },
]

export default function HeroSection() {
  return (
    <section id="hero" className="pt-28 sm:pt-36 pb-16 sm:pb-24 px-4 sm:px-6 max-w-7xl mx-auto text-center">
      {/* Eyebrow badge */}
      <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-bg-card border border-border-default mb-6">
        <span className="status-dot status-dot-healthy" />
        <span className="caption-4 text-text-secondary">
          Digital twin platform for plant engineers
        </span>
      </div>

      {/* Hero Heading: max-width 680px, gradient #FFFFFF -> #9B9B9B, meaningful line breaks */}
      <h1 className="hero-gradient heading-2 sm:heading-1 max-w-hero mx-auto font-semibold tracking-tight text-center mb-6">
        Predict machine failure before downtime strikes your floor
      </h1>

      {/* Subheadline: no hyphens, sentence case, max-width 620px */}
      <p className="body-2 text-text-secondary max-w-xl mx-auto mb-8">
        AI Factory Operating System continuously monitors machine health, predicts Remaining Useful Life, simulates what if scenarios, and estimates business loss in Indian Rupees.
      </p>

      {/* CTA Strip: Primary CTA + Secondary text link */}
      <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-4">
        <Link to="/app" className="btn-primary w-full sm:w-auto">
          <span>Book a demo</span>
          <ArrowRight className="w-4 h-4" />
        </Link>
        <a
          href="#proof"
          className="caption-1 text-text-secondary hover:text-white transition-colors duration-200 py-2 px-3"
        >
          Explore benchmark metrics
        </a>
      </div>

      {/* Proof Line */}
      <div className="caption-4 text-text-muted mb-14">
        Validated on NASA C-MAPSS and AI4I public benchmarks with 14 cycle RMSE
      </div>

      {/* Hero Visual: Real Coded Dashboard Mockup (NOT a stock image) */}
      <div className="card p-4 sm:p-6 bg-bg-card/90 border border-border-default rounded-2xl shadow-2xl max-w-5xl mx-auto text-left overflow-hidden">
        {/* Mockup Header Strip */}
        <div className="flex flex-wrap items-center justify-between gap-3 pb-4 mb-4 border-b border-border-subtle">
          <div className="flex items-center gap-3">
            <span className="caption-5 uppercase tracking-wider text-text-muted font-semibold">
              Live Twin Console
            </span>
            <span className="px-2 py-0.5 rounded bg-bg-raised border border-border-subtle caption-5 mono text-text-secondary">
              Plant health: 76.8%
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className="status-dot status-dot-healthy" />
            <span className="caption-5 text-text-secondary">Replaying Cycle 183</span>
          </div>
        </div>

        {/* 3 Machine Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4">
          {/* Card 1: Compressor Unit A (Healthy) */}
          <div className="card-raised p-4 rounded-xl border border-border-subtle">
            <div className="flex justify-between items-start mb-2">
              <div>
                <div className="title-4 text-white font-medium">Compressor Unit A</div>
                <div className="caption-5 text-text-muted">Bay 1 • NASA C-MAPSS</div>
              </div>
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs bg-status-healthy/10 text-status-healthy border border-status-healthy/25">
                <CheckCircle2 className="w-3 h-3" />
                <span>Healthy</span>
              </span>
            </div>
            <div className="flex items-baseline justify-between mt-3 mb-2">
              <span className="caption-5 text-text-muted">Health score</span>
              <span className="heading-6 mono text-status-healthy">87.3%</span>
            </div>
            <div className="flex items-baseline justify-between mb-3">
              <span className="caption-5 text-text-muted">Predicted RUL</span>
              <span className="title-4 mono text-white">178 cycles</span>
            </div>
            <Sparkline
              status="healthy"
              data={[{ health: 95 }, { health: 93 }, { health: 91 }, { health: 89 }, { health: 87.3 }]}
            />
          </div>

          {/* Card 2: Turbine Engine B (Warning) */}
          <div className="card-raised p-4 rounded-xl border border-border-subtle">
            <div className="flex justify-between items-start mb-2">
              <div>
                <div className="title-4 text-white font-medium">Turbine Engine B</div>
                <div className="caption-5 text-text-muted">Bay 2 • NASA C-MAPSS</div>
              </div>
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs bg-status-warning/10 text-status-warning border border-status-warning/25">
                <AlertTriangle className="w-3 h-3" />
                <span>Warning</span>
              </span>
            </div>
            <div className="flex items-baseline justify-between mt-3 mb-2">
              <span className="caption-5 text-text-muted">Health score</span>
              <span className="heading-6 mono text-status-warning">54.7%</span>
            </div>
            <div className="flex items-baseline justify-between mb-3">
              <span className="caption-5 text-text-muted">Predicted RUL</span>
              <span className="title-4 mono text-white">36 cycles</span>
            </div>
            <Sparkline
              status="warning"
              data={[{ health: 85 }, { health: 74 }, { health: 65 }, { health: 58 }, { health: 54.7 }]}
            />
          </div>

          {/* Card 3: Milling Station C (Critical) */}
          <div className="card-raised p-4 rounded-xl border border-border-subtle">
            <div className="flex justify-between items-start mb-2">
              <div>
                <div className="title-4 text-white font-medium">Milling Station C</div>
                <div className="caption-5 text-text-muted">Bay 3 • AI4I 2020</div>
              </div>
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs bg-status-critical/10 text-status-critical border border-status-critical/25">
                <AlertCircle className="w-3 h-3" />
                <span>Critical</span>
              </span>
            </div>
            <div className="flex items-baseline justify-between mt-3 mb-2">
              <span className="caption-5 text-text-muted">Health score</span>
              <span className="heading-6 mono text-status-critical">23.1%</span>
            </div>
            <div className="flex items-baseline justify-between mb-3">
              <span className="caption-5 text-text-muted">Predicted RUL</span>
              <span className="title-4 mono text-white">11 cycles</span>
            </div>
            <Sparkline
              status="critical"
              data={[{ health: 60 }, { health: 48 }, { health: 37 }, { health: 28 }, { health: 23.1 }]}
            />
          </div>
        </div>

        {/* Anomaly Trend Chart Panel */}
        <div className="card-raised p-4 rounded-xl border border-border-subtle">
          <div className="flex items-center justify-between mb-3">
            <div>
              <span className="title-4 text-white">Critical anomaly progression</span>
              <span className="caption-5 text-text-muted ml-2">Milling Station C (Machine 3)</span>
            </div>
            <span className="caption-5 mono text-status-critical">
              Current score: 0.89 (Threshold: 0.75)
            </span>
          </div>
          <AnomalyTrendChart data={MOCK_ANOMALY_TREND} height={160} />
        </div>
      </div>
    </section>
  )
}

