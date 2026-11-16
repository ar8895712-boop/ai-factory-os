// frontend/src/components/landing/LandingFooter.jsx
import React from 'react'
import { Link } from 'react-router-dom'
import { Activity } from 'lucide-react'

export default function LandingFooter() {
  return (
    <footer className="border-t border-border-subtle bg-bg-card/40 py-12 px-4 sm:px-6">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-6">
        {/* Brand */}
        <div className="flex items-center gap-2.5">
          <div className="w-6 h-6 rounded bg-bg-raised border border-border-subtle flex items-center justify-center">
            <Activity className="w-3 h-3 text-white" />
          </div>
          <span className="title-4 text-white font-semibold">AI Factory OS</span>
          <span className="caption-5 text-text-muted ml-2">Digital Twin Platform</span>
        </div>

        {/* Legal & Credits Links */}
        <div className="flex flex-wrap items-center justify-center gap-6 caption-4 text-text-muted">
          <Link to="/app" className="hover:text-white transition-colors">
            Demo console
          </Link>
          <a
            href="https://data.nasa.gov"
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-white transition-colors"
          >
            NASA C-MAPSS
          </a>
          <a
            href="https://archive.ics.uci.edu"
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-white transition-colors"
          >
            UCI Machine Learning
          </a>
          <span>Privacy policy</span>
          <span>Terms of use</span>
        </div>

        {/* Capstone notice */}
        <div className="caption-5 text-text-muted text-center md:text-right">
          B.Tech Capstone Project • Replaying simulated benchmark data
        </div>
      </div>
    </footer>
  )
}

