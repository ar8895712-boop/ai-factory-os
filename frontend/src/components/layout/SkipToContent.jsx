// frontend/src/components/layout/SkipToContent.jsx
import React from 'react'

export default function SkipToContent() {
  return (
    <a
      href="#main-content"
      className="sr-only focus:not-sr-only focus:fixed focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-white focus:text-black focus:rounded-lg focus:button-sm focus:shadow-lg focus:ring-2 focus:ring-status-info"
    >
      Skip to main content
    </a>
  )
}

