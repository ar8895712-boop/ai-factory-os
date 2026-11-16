// frontend/src/pages/NotFound.jsx — Custom Branded 404
import React from 'react'
import { Link } from 'react-router-dom'
import { Activity, ArrowLeft } from 'lucide-react'

export default function NotFound() {
  return (
    <div className="min-h-screen bg-bg-base text-white flex flex-col items-center justify-center p-6 text-center">
      <div className="w-14 h-14 rounded-2xl bg-bg-card border border-border-default flex items-center justify-center text-white mb-6 shadow-xl">
        <Activity className="w-7 h-7 text-text-muted" />
      </div>

      <div className="mono caption-3 uppercase tracking-widest text-text-muted mb-2">
        Error 404 • Resource Not Located
      </div>

      <h1 className="heading-3 sm:heading-2 text-white max-w-md mb-4">
        This telemetry route does not exist
      </h1>

      <p className="body-2 text-text-secondary max-w-sm mb-8">
        The requested digital twin panel or machine identifier could not be verified on the operating floor.
      </p>

      <div className="flex flex-col sm:flex-row items-center gap-3">
        <Link to="/app" className="btn-primary px-6 py-2.5 button-sm gap-2">
          <ArrowLeft className="w-4 h-4" />
          <span>Return to Dashboard</span>
        </Link>
        <Link to="/" className="btn-secondary px-6 py-2.5 button-sm">
          <span>Landing Page</span>
        </Link>
      </div>
    </div>
  )
}

