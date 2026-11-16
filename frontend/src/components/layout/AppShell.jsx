// frontend/src/components/layout/AppShell.jsx
import React, { useState, useEffect } from 'react'
import { Outlet, Link, useLocation } from 'react-router-dom'
import SkipToContent from './SkipToContent.jsx'
import Sidebar from './Sidebar.jsx'
import BottomTabBar from './BottomTabBar.jsx'
import SettingsDrawer from './SettingsDrawer.jsx'
import { MOCK_MACHINES, DEFAULT_ASSUMPTIONS } from '../../mocks/index.js'
import { Play, Pause, RotateCcw, FastForward, SlidersHorizontal, Activity } from 'lucide-react'

export default function AppShell() {
  const [machines, setMachines] = useState(MOCK_MACHINES)
  const [assumptions, setAssumptions] = useState(DEFAULT_ASSUMPTIONS)
  const [isSettingsOpen, setIsSettingsOpen] = useState(false)
  const [simStatus, setSimStatus] = useState({ is_running: false, speed_factor: 1.0 })
  const [alertCount, setAlertCount] = useState(5)
  const [isBackendConnected, setIsBackendConnected] = useState(false)
  const location = useLocation()

  // Attempt live API fetch; fall back gracefully to mock data
  const refreshMachines = () => {
    fetch('/api/machines')
      .then((r) => {
        if (!r.ok) throw new Error('API non-200')
        return r.json()
      })
      .then((data) => {
        if (Array.isArray(data) && data.length > 0) {
          setMachines(data)
          setIsBackendConnected(true)
        }
      })
      .catch(() => {
        setIsBackendConnected(false)
      })

    fetch('/api/simulation/status')
      .then((r) => r.json())
      .then((data) => setSimStatus(data))
      .catch(() => {})

    fetch('/api/alerts?resolved=false')
      .then((r) => r.json())
      .then((data) => {
        if (Array.isArray(data)) setAlertCount(data.length)
      })
      .catch(() => {})
  }

  useEffect(() => {
    refreshMachines()
  }, [])

  // Simulation controls
  const handleToggleSim = () => {
    const nextState = !simStatus.is_running
    const endpoint = nextState ? '/api/simulation/start' : '/api/simulation/pause'
    fetch(endpoint, { method: 'POST' })
      .catch(() => {})
      .finally(() => setSimStatus((s) => ({ ...s, is_running: nextState })))
  }

  const handleResetSim = () => {
    fetch('/api/simulation/reset', { method: 'POST' })
      .catch(() => {})
      .finally(() => {
        setSimStatus((s) => ({ ...s, is_running: false }))
        refreshMachines()
      })
  }

  const handleStepSim = () => {
    fetch('/api/simulation/step', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ steps: 1 }),
    })
      .catch(() => {})
      .finally(() => refreshMachines())
  }

  const handleSpeedChange = (speed) => {
    fetch('/api/simulation/speed', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ speed_factor: speed }),
    })
      .catch(() => {})
      .finally(() => setSimStatus((s) => ({ ...s, speed_factor: speed })))
  }

  const handleResetAssumptions = () => {
    setAssumptions(DEFAULT_ASSUMPTIONS)
  }

  return (
    <div className="min-h-screen bg-bg-base text-white flex flex-col font-sans">
      <SkipToContent />

      {/* Desktop Sidebar */}
      <Sidebar
        alertCount={alertCount}
        onOpenSettings={() => setIsSettingsOpen(true)}
      />

      {/* Main Content Column */}
      <div className="lg:pl-60 flex flex-col min-h-screen">
        {/* Top Control Header */}
        <header className="h-16 bg-bg-card/80 backdrop-blur-md border-b border-border-subtle sticky top-0 z-20 px-4 sm:px-6 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link to="/" className="lg:hidden flex items-center gap-2">
              <div className="w-7 h-7 rounded bg-bg-raised border border-border-default flex items-center justify-center">
                <Activity className="w-3.5 h-3.5 text-white" />
              </div>
              <span className="title-4 font-semibold text-white">AI Factory OS</span>
            </Link>
            <div className="hidden sm:flex items-center gap-2">
              <span className="caption-4 text-text-muted">Twin Stream:</span>
              <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded bg-bg-raised border border-border-subtle caption-4 mono text-text-secondary">
                <span className={`status-dot ${isBackendConnected ? 'status-dot-healthy' : 'status-dot-info'}`} />
                {isBackendConnected ? 'Live Backend Connected' : 'Demo Mode (Simulated Replay)'}
              </span>
            </div>
          </div>

          {/* Simulation Controls Strip */}
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-1 bg-bg-raised p-1 rounded-lg border border-border-subtle">
              <button
                onClick={handleToggleSim}
                className="p-1.5 rounded-md hover:bg-neutral-800 text-text-primary transition-colors focus-visible:ring-1 focus-visible:ring-white"
                title={simStatus.is_running ? 'Pause stream' : 'Start stream'}
                aria-label={simStatus.is_running ? 'Pause stream' : 'Start stream'}
              >
                {simStatus.is_running ? (
                  <Pause className="w-4 h-4 text-status-warning" />
                ) : (
                  <Play className="w-4 h-4 text-status-healthy" />
                )}
              </button>
              <button
                onClick={handleStepSim}
                className="p-1.5 rounded-md hover:bg-neutral-800 text-text-secondary hover:text-white transition-colors"
                title="Step 1 cycle"
                aria-label="Step 1 cycle"
              >
                <FastForward className="w-4 h-4" />
              </button>
              <button
                onClick={handleResetSim}
                className="p-1.5 rounded-md hover:bg-neutral-800 text-text-secondary hover:text-white transition-colors"
                title="Reset simulation"
                aria-label="Reset simulation"
              >
                <RotateCcw className="w-4 h-4" />
              </button>
            </div>

            {/* Speed pill */}
            <select
              value={simStatus.speed_factor}
              onChange={(e) => handleSpeedChange(Number(e.target.value))}
              className="bg-bg-raised border border-border-subtle text-text-secondary hover:text-white text-xs rounded-lg px-2 py-1.5 mono focus:ring-1 focus:ring-white"
              aria-label="Simulation speed factor"
            >
              <option value="0.5">0.5x</option>
              <option value="1.0">1.0x</option>
              <option value="2.0">2.0x</option>
              <option value="5.0">5.0x</option>
            </select>

            {/* Assumptions Drawer button */}
            <button
              onClick={() => setIsSettingsOpen(true)}
              className="btn-secondary px-3 py-1.5 button-xsm gap-1.5"
              title="Edit business assumptions"
            >
              <SlidersHorizontal className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Assumptions</span>
            </button>
          </div>
        </header>

        {/* Content Outlet */}
        <main id="main-content" className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl w-full mx-auto pb-24 lg:pb-8">
          <Outlet
            context={{
              machines,
              setMachines,
              assumptions,
              setAssumptions,
              refreshMachines,
              isBackendConnected,
              onOpenSettings: () => setIsSettingsOpen(true),
            }}
          />
        </main>

        {/* Footer */}
        <footer className="border-t border-border-subtle bg-bg-card py-4 px-6 text-center caption-4 text-text-muted hidden lg:block">
          AI Factory Operating System • Simulated machines replaying benchmark data (NASA C-MAPSS, AI4I 2020, SKAB)
        </footer>
      </div>

      {/* Mobile Bottom Tab Bar */}
      <BottomTabBar />

      {/* Financial Assumptions Drawer */}
      <SettingsDrawer
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        assumptions={assumptions}
        onUpdateAssumptions={setAssumptions}
        onResetAssumptions={handleResetAssumptions}
      />
    </div>
  )
}
