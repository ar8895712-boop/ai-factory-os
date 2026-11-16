// frontend/src/components/landing/TaglineReveal.jsx
import React, { useEffect, useRef, useState } from 'react'

const TAGLINE_LINES = [
  "Maintenance that acts on evidence, not instinct.",
  "Every cost figure is derived from your own assumptions. Every alert is backed by a model you can inspect."
]

export default function TaglineReveal() {
  const containerRef = useRef(null)
  const [progress, setProgress] = useState(0)
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false)

  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)')
    setPrefersReducedMotion(mediaQuery.matches)

    const handleScroll = () => {
      if (!containerRef.current) return
      const rect = containerRef.current.getBoundingClientRect()
      const windowHeight = window.innerHeight
      // Calculate how far through the section the user has scrolled
      const start = windowHeight * 0.8
      const end = windowHeight * 0.2
      const current = rect.top

      if (current > start) {
        setProgress(0)
      } else if (current < end) {
        setProgress(1)
      } else {
        const p = (start - current) / (start - end)
        setProgress(Math.max(0, Math.min(1, p)))
      }
    }

    window.addEventListener('scroll', handleScroll, { passive: true })
    handleScroll()
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  // Split lines into words
  const allWords = TAGLINE_LINES.flatMap((line, lineIdx) =>
    line.split(' ').map((word) => ({ word, lineIdx }))
  )

  return (
    <section
      ref={containerRef}
      className="py-24 sm:py-36 px-4 sm:px-6 max-w-5xl mx-auto text-center"
      aria-label="Core philosophy"
    >
      <div className="caption-5 uppercase tracking-widest text-text-muted font-semibold mb-6">
        The Principles Behind The Operating System
      </div>

      <div className="heading-3 sm:heading-2 max-w-4xl mx-auto leading-relaxed">
        {allWords.map((item, idx) => {
          const wordThreshold = idx / allWords.length
          const isRevealed = prefersReducedMotion || progress >= wordThreshold

          return (
            <span
              key={idx}
              className="inline-block mr-2.5 transition-opacity duration-300"
              style={{
                opacity: isRevealed ? 1 : 0.25,
                color: isRevealed ? '#FFFFFF' : '#6B6B6B',
                transitionTimingFunction: 'cubic-bezier(0.22, 1, 0.36, 1)',
              }}
            >
              {item.word}
            </span>
          )
        })}
      </div>
    </section>
  )
}

