// frontend/src/components/layout/Sidebar.jsx
import React from 'react'
import { NavLink, Link } from 'react-router-dom'
import {
  LayoutDashboard,
  Cpu,
  AlertTriangle,
  IndianRupee,
  Sliders,
  Database,
  Bot,
  ArrowLeft,
  Activity,
  SlidersHorizontal
} from 'lucide-react'

const NAV_ITEMS = [
  { name: 'Overview', to: '/app/overview', icon: LayoutDashboard },
  { name: 'Machine Detail', to: '/app/machines/1', icon: Cpu },
  { name: 'Alerts', to: '/app/alerts', icon: AlertTriangle, badge: true },
  { name: 'Business Impact', to: '/app/business', icon: IndianRupee },
  { name: 'What-If Simulator', to: '/app/whatif', icon: Sliders },
  { name: 'Factory Memory', to: '/app/memory', icon: Database },
  { name: 'Engineer Assistant', to: '/app/assistant', icon: Bot },
]

export default function Sidebar({ alertCount = 5, onOpenSettings }) {
  return (
    <aside className="hidden lg:flex lg:flex-col lg:w-60 lg:fixed lg:inset-y-0 bg-bg-card border-r border-border-subtle z-30">
      {/* Brand Header */}
      <div className="h-16 flex items-center justify-between px-4 border-b border-border-subtle">
        <Link to="/" className="flex items-center gap-2 group">
          <div className="w-8 h-8 rounded-lg bg-bg-raised border border-border-default flex items-center justify-center text-white group-hover:border-neutral-500 transition-colors">
            <Activity className="w-4 h-4 text-white" />
          </div>
          <div>
            <div className="title-4 text-white font-semibold">AI Factory OS</div>
            <div className="caption-5 text-text-muted">Digital Twin Platform</div>
          </div>
        </Link>
      </div>

      {/* Nav Links */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        <div className="px-3 pb-2 caption-5 text-text-muted uppercase tracking-wider font-semibold">
          Operations
        </div>
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon
          return (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex items-center justify-between px-3 py-2 rounded-lg title-4 transition-colors duration-200 ${
                  isActive
                    ? 'bg-bg-raised text-white font-medium border border-border-subtle'
                    : 'text-text-secondary hover:text-white hover:bg-bg-raised/50'
                }`
              }
            >
              <div className="flex items-center gap-2.5">
                <Icon className="w-4 h-4 flex-shrink-0" />
                <span>{item.name}</span>
              </div>
              {item.badge && alertCount > 0 && (
                <span className="px-1.5 py-0.5 rounded-full caption-5 bg-status-critical/15 text-status-critical border border-status-critical/30 mono">
                  {alertCount}
                </span>
              )}
            </NavLink>
          )
        })}
      </nav>

      {/* Bottom Actions & Benchmark Disclaimer */}
      <div className="p-3 border-t border-border-subtle space-y-2">
        {onOpenSettings && (
          <button
            onClick={onOpenSettings}
            className="w-full flex items-center gap-2 px-3 py-2 rounded-lg title-4 text-text-secondary hover:text-white hover:bg-bg-raised transition-colors"
          >
            <SlidersHorizontal className="w-4 h-4" />
            <span>Assumptions</span>
          </button>
        )}

        <Link
          to="/"
          className="flex items-center gap-2 px-3 py-2 rounded-lg title-4 text-text-secondary hover:text-white hover:bg-bg-raised transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Exit to landing</span>
        </Link>

        <div className="px-3 py-2 rounded-lg bg-bg-raised/40 border border-border-subtle">
          <div className="flex items-center gap-1.5 caption-4 text-text-muted">
            <span className="status-dot status-dot-healthy" />
            <span>Replaying benchmark data</span>
          </div>
          <div className="caption-5 text-text-muted mt-0.5">
            NASA C-MAPSS + AI4I 2020
          </div>
        </div>
      </div>
    </aside>
  )
}

