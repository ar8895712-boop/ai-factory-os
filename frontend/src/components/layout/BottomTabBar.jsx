// frontend/src/components/layout/BottomTabBar.jsx
import React from 'react'
import { NavLink } from 'react-router-dom'
import { LayoutDashboard, Cpu, AlertTriangle, Sliders, Bot } from 'lucide-react'

const TABS = [
  { name: 'Overview', to: '/app/overview', icon: LayoutDashboard },
  { name: 'Detail', to: '/app/machines/1', icon: Cpu },
  { name: 'Alerts', to: '/app/alerts', icon: AlertTriangle },
  { name: 'What-If', to: '/app/whatif', icon: Sliders },
  { name: 'Assistant', to: '/app/assistant', icon: Bot },
]

export default function BottomTabBar() {
  return (
    <nav
      aria-label="Mobile Navigation"
      className="lg:hidden fixed bottom-0 inset-x-0 bg-bg-card/95 backdrop-blur-md border-t border-border-subtle z-40 px-2 py-1.5 flex items-center justify-around"
    >
      {TABS.map((tab) => {
        const Icon = tab.icon
        return (
          <NavLink
            key={tab.to}
            to={tab.to}
            className={({ isActive }) =>
              `flex flex-col items-center justify-center py-1 px-3 rounded-lg transition-colors ${
                isActive
                  ? 'text-white font-medium'
                  : 'text-text-secondary hover:text-white'
              }`
            }
          >
            <Icon className="w-5 h-5 mb-0.5" />
            <span className="caption-5">{tab.name}</span>
          </NavLink>
        )
      })}
    </nav>
  )
}

