// ==============================================================
// frontend/src/components/Navbar.jsx — Header & Simulation Bar
// ==============================================================
import React, { useState } from 'react'
import {
  Activity,
  AlertTriangle,
  BarChart3,
  Bot,
  DollarSign,
  FastForward,
  Gauge,
  Pause,
  Play,
  RotateCcw,
  Sliders,
  StepForward,
  Wifi,
  WifiOff,
} from 'lucide-react'

export function Navbar({
  activeTab,
  setActiveTab,
  isConnected,
  simStatus,
  onStartSim,
  onPauseSim,
  onResetSim,
  onStepSim,
  onSpeedChange,
  alertCount = 0,
}) {
  const [speed, setSpeed] = useState(simStatus?.speed_factor || 1.0)

  const handleSpeedSelect = (e) => {
    const newSpeed = parseFloat(e.target.value)
    setSpeed(newSpeed)
    onSpeedChange(newSpeed)
  }

  const tabs = [
    { id: 'overview', label: 'Factory Overview', icon: Activity },
    { id: 'detail', label: 'Machine Detail', icon: Gauge },
    { id: 'alerts', label: 'Alerts', icon: AlertTriangle, badge: alertCount },
    { id: 'business', label: 'Business Impact (₹)', icon: DollarSign },
    { id: 'whatif', label: 'What-If Simulator', icon: Sliders },
    { id: 'chat', label: 'Factory GPT', icon: Bot },
  ]

  return (
    <header className="bg-slate-900 border-b border-slate-800 sticky top-0 z-50 px-4 py-3 shadow-lg">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
        {/* Brand */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center shadow-lg shadow-blue-500/20 text-white font-black text-xl">
            ⚙️
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="font-bold text-lg text-white tracking-tight">AI Factory OS</h1>
              <span className="text-[10px] uppercase font-semibold bg-blue-500/10 text-blue-400 px-2 py-0.5 rounded border border-blue-500/20">
                Digital Twin
              </span>
            </div>
            <p className="text-xs text-slate-400">Predictive Maintenance & Asset Intelligence</p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="flex items-center gap-1 bg-slate-950/60 p-1 rounded-xl border border-slate-800">
          {tabs.map((tab) => {
            const Icon = tab.icon
            const isActive = activeTab === tab.id
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  isActive
                    ? 'bg-blue-600 text-white shadow-md shadow-blue-600/30 font-semibold'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                }`}
              >
                <Icon className="w-4 h-4" />
                <span>{tab.label}</span>
                {tab.badge > 0 && (
                  <span className="px-1.5 py-0.2 bg-rose-500 text-white text-[10px] font-bold rounded-full">
                    {tab.badge}
                  </span>
                )}
              </button>
            )
          })}
        </nav>

        {/* Simulation Controls & Connection */}
        <div className="flex items-center gap-3">
          {/* Live Status indicator */}
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-950 border border-slate-800 text-xs">
            {isConnected ? (
              <>
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                <span className="text-emerald-400 font-medium">LIVE STREAM</span>
              </>
            ) : (
              <>
                <span className="w-2 h-2 rounded-full bg-slate-500" />
                <span className="text-slate-400 font-medium">DISCONNECTED</span>
              </>
            )}
          </div>

          {/* Controls Bar */}
          <div className="flex items-center gap-1 bg-slate-950/80 p-1 rounded-xl border border-slate-800">
            {simStatus?.is_running ? (
              <button
                onClick={onPauseSim}
                title="Pause live simulation"
                className="p-1.5 text-amber-400 hover:bg-amber-500/20 rounded-lg transition"
              >
                <Pause className="w-4 h-4" />
              </button>
            ) : (
              <button
                onClick={onStartSim}
                title="Start live simulation replay"
                className="p-1.5 text-emerald-400 hover:bg-emerald-500/20 rounded-lg transition"
              >
                <Play className="w-4 h-4 fill-emerald-400" />
              </button>
            )}

            <button
              onClick={onStepSim}
              title="Step 1 cycle"
              className="p-1.5 text-slate-300 hover:bg-slate-800 rounded-lg transition"
            >
              <StepForward className="w-4 h-4" />
            </button>

            <button
              onClick={onResetSim}
              title="Reset all machines to cycle 1"
              className="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 rounded-lg transition"
            >
              <RotateCcw className="w-4 h-4" />
            </button>

            {/* Speed selector */}
            <div className="flex items-center pl-1 border-l border-slate-800 text-xs">
              <FastForward className="w-3.5 h-3.5 text-slate-400 mr-1" />
              <select
                value={speed}
                onChange={handleSpeedSelect}
                className="bg-transparent text-slate-200 text-xs font-semibold focus:outline-none cursor-pointer pr-1"
              >
                <option value={0.5} className="bg-slate-900">0.5x</option>
                <option value={1.0} className="bg-slate-900">1.0x</option>
                <option value={2.0} className="bg-slate-900">2.0x</option>
                <option value={5.0} className="bg-slate-900">5.0x</option>
                <option value={10.0} className="bg-slate-900">10x</option>
              </select>
            </div>
          </div>
        </div>
      </div>
    </header>
  )
}

