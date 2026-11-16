// frontend/src/pages/LandingPage.jsx
import React from 'react'
import LandingNav from '../components/landing/LandingNav.jsx'
import HeroSection from '../components/landing/HeroSection.jsx'
import BenefitsSection from '../components/landing/BenefitsSection.jsx'
import TaglineReveal from '../components/landing/TaglineReveal.jsx'
import HowItWorksSection from '../components/landing/HowItWorksSection.jsx'
import TrustProofSection from '../components/landing/TrustProofSection.jsx'
import FAQSection from '../components/landing/FAQSection.jsx'
import FinalCTASection from '../components/landing/FinalCTASection.jsx'
import LandingFooter from '../components/landing/LandingFooter.jsx'

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-bg-base text-white flex flex-col selection:bg-neutral-700 selection:text-white">
      <LandingNav />
      <main id="main-content" className="flex-1">
        <HeroSection />
        <BenefitsSection />
        <TaglineReveal />
        <HowItWorksSection />
        <TrustProofSection />
        <FAQSection />
        <FinalCTASection />
      </main>
      <LandingFooter />
    </div>
  )
}

