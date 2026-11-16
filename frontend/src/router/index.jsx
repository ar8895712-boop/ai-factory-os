// frontend/src/router/index.jsx
import React, { lazy, Suspense } from 'react'
import { createBrowserRouter } from 'react-router-dom'
import AppShell from '../components/layout/AppShell.jsx'

// Lazy-loaded pages for code splitting
const LandingPage      = lazy(() => import('../pages/LandingPage.jsx'))
const FactoryOverview  = lazy(() => import('../pages/FactoryOverview.jsx'))
const MachineDetail    = lazy(() => import('../pages/MachineDetail.jsx'))
const Alerts           = lazy(() => import('../pages/Alerts.jsx'))
const BusinessImpact   = lazy(() => import('../pages/BusinessImpact.jsx'))
const WhatIfSimulator  = lazy(() => import('../pages/WhatIfSimulator.jsx'))
const FactoryMemory    = lazy(() => import('../pages/FactoryMemory.jsx'))
const EngineerAssistant = lazy(() => import('../pages/EngineerAssistant.jsx'))
const NotFound         = lazy(() => import('../pages/NotFound.jsx'))

function PageLoader() {
  return (
    <div className="flex items-center justify-center min-h-screen bg-bg-base">
      <div className="flex flex-col items-center gap-4">
        <div className="w-8 h-8 border-2 border-border-default border-t-white rounded-full animate-spin" />
        <span className="caption-2 text-text-muted">Loading</span>
      </div>
    </div>
  )
}

function withSuspense(Component) {
  return (
    <Suspense fallback={<PageLoader />}>
      <Component />
    </Suspense>
  )
}

export const router = createBrowserRouter([
  {
    path: '/',
    element: withSuspense(LandingPage),
  },
  {
    path: '/app',
    element: <AppShell />,
    children: [
      { index: true,            element: withSuspense(FactoryOverview) },
      { path: 'overview',       element: withSuspense(FactoryOverview) },
      { path: 'machines/:id',   element: withSuspense(MachineDetail) },
      { path: 'alerts',         element: withSuspense(Alerts) },
      { path: 'business',       element: withSuspense(BusinessImpact) },
      { path: 'whatif',         element: withSuspense(WhatIfSimulator) },
      { path: 'memory',         element: withSuspense(FactoryMemory) },
      { path: 'assistant',      element: withSuspense(EngineerAssistant) },
    ],
  },
  {
    path: '*',
    element: withSuspense(NotFound),
  },
])

