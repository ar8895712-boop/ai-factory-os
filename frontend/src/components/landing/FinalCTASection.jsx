// frontend/src/components/landing/FinalCTASection.jsx
import React from 'react'
import { Link } from 'react-router-dom'
import { ArrowRight } from 'lucide-react'

export default function FinalCTASection() {
  return (
    <section className="py-20 sm:py-28 px-4 sm:px-6 max-w-5xl mx-auto text-center border-t border-border-subtle">
      <div className="card p-8 sm:p-14 bg-bg-card/90 border border-border-default rounded-3xl relative overflow-hidden">
        <div className="caption-5 uppercase tracking-wider text-text-muted font-semibold mb-3">
          Get Started
        </div>
        <h2 className="heading-3 sm:heading-2 text-white max-w-xl mx-auto mb-4">
          Experience the factory operating system in action
        </h2>
        <p className="body-2 text-text-secondary max-w-lg mx-auto mb-8">
          Explore machine health scorecards, live anomaly trajectories, what if simulation controls, and transparent financial loss models.
        </p>

        {/* Identical to Hero CTA */}
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

        {/* Identical proof line */}
        <div className="caption-4 text-text-muted">
          Validated on NASA C-MAPSS and AI4I public benchmarks with 14 cycle RMSE
        </div>
      </div>
    </section>
  )
}

