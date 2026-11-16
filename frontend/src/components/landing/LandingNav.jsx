// frontend/src/components/landing/LandingNav.jsx
import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { Activity, Menu, X, ArrowRight } from 'lucide-react'

const NAV_LINKS = [
  { label: 'Overview', href: '#hero' },
  { label: 'Capabilities', href: '#benefits' },
  { label: 'How it works', href: '#how-it-works' },
  { label: 'Benchmarks', href: '#proof' },
  { label: 'FAQ', href: '#faq' },
]

export default function LandingNav() {
  const [isOpen, setIsOpen] = useState(false)
  const [scrolled, setScrolled] = useState(false)

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 20)
    }
    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  return (
    <>
      <header
        className={`fixed top-4 inset-x-0 mx-auto max-w-5xl px-4 z-40 transition-all duration-300 ${
          scrolled ? 'top-2' : 'top-4'
        }`}
      >
        <nav
          aria-label="Main Navigation"
          className="h-14 px-4 sm:px-6 rounded-2xl bg-bg-card/85 backdrop-blur-md border border-border-default flex items-center justify-between shadow-2xl"
        >
          {/* Brand */}
          <Link to="/" className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-lg bg-bg-raised border border-border-subtle flex items-center justify-center">
              <Activity className="w-3.5 h-3.5 text-white" />
            </div>
            <span className="title-4 font-semibold text-white tracking-tight">AI Factory OS</span>
          </Link>

          {/* Desktop Links */}
          <div className="hidden md:flex items-center gap-6">
            {NAV_LINKS.map((link) => (
              <a
                key={link.label}
                href={link.href}
                className="caption-1 text-text-secondary hover:text-white transition-colors duration-200"
              >
                {link.label}
              </a>
            ))}
          </div>

          {/* CTA & Mobile Hamburger */}
          <div className="flex items-center gap-3">
            <Link
              to="/app"
              className="hidden sm:inline-flex items-center gap-1.5 px-4 py-1.5 rounded-lg bg-white text-black button-xsm hover:bg-neutral-200 active:bg-neutral-300 transition-colors"
            >
              <span>Book a demo</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>

            <button
              onClick={() => setIsOpen(!isOpen)}
              className="md:hidden p-1.5 rounded-lg text-text-secondary hover:text-white hover:bg-bg-raised transition-colors"
              aria-label={isOpen ? 'Close menu' : 'Open menu'}
              aria-expanded={isOpen}
            >
              {isOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </nav>
      </header>

      {/* Mobile Full-Height Menu */}
      {isOpen && (
        <div className="fixed inset-0 z-30 md:hidden bg-bg-base/98 backdrop-blur-xl flex flex-col justify-between p-6 pt-24 animate-fade-up">
          <div className="space-y-4">
            <div className="caption-5 text-text-muted uppercase tracking-wider font-semibold mb-2">
              Navigation
            </div>
            {NAV_LINKS.map((link, idx) => (
              <a
                key={link.label}
                href={link.href}
                onClick={() => setIsOpen(false)}
                style={{ animationDelay: `${idx * 60}ms` }}
                className="block heading-5 text-white hover:text-text-secondary transition-colors py-2"
              >
                {link.label}
              </a>
            ))}
          </div>

          <div className="pt-6 border-t border-border-subtle space-y-3">
            <Link
              to="/app"
              onClick={() => setIsOpen(false)}
              className="w-full btn-primary py-3"
            >
              <span>Book a demo</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
            <p className="caption-5 text-text-muted text-center">
              Runs on NASA C-MAPSS and AI4I public benchmark datasets
            </p>
          </div>
        </div>
      )}
    </>
  )
}

