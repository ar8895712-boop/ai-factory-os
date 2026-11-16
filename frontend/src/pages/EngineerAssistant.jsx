// frontend/src/pages/EngineerAssistant.jsx — Operational Engineer AI Assistant
import React, { useState } from 'react'
import {
  Bot,
  Send,
  HelpCircle,
  Sparkles,
  Database,
  ArrowRight,
  ShieldAlert,
  Sliders,
  CheckCircle2
} from 'lucide-react'
import { MOCK_QUERIES, SUGGESTED_QUESTIONS } from '../mocks/index.js'

export default function EngineerAssistant() {
  const [queryInput, setQueryInput] = useState('')
  const [conversations, setConversations] = useState(MOCK_QUERIES)
  const [isTyping, setIsTyping] = useState(false)

  const handleAsk = (questionText) => {
    const q = questionText || queryInput
    if (!q.trim()) return

    setQueryInput('')
    setIsTyping(true)

    // Simulate grounded assistant reasoning
    setTimeout(() => {
      const matched = MOCK_QUERIES.find((item) =>
        item.query.toLowerCase().includes(q.toLowerCase().slice(0, 15))
      )

      const newResponse = matched || {
        query: q,
        answer: `Regarding "${q}": Based on current telemetry from NASA C-MAPSS FD001 cycle 183, Milling Station C requires immediate inspection due to exhaust temperature T50 exceeding nominal threshold by 31 units. Remaining Useful Life is estimated at 11 cycles. Other monitored assets are operating within safe tolerances.`,
        data_sources: [
          { label: 'Asset targeted', value: 'Milling Station C (M-03)', source: 'Machine telemetry' },
          { label: 'Anomaly reading', value: '0.89 / 1.0', source: 'Reconstruction error' },
          { label: 'Predicted RUL', value: '11 cycles', source: 'LSTM regression' },
        ],
        suggested_actions: [
          'Inspect bearing manifold and temperature sensors',
          'Run a What-If simulation to model shutdown vs. derating',
        ],
        timestamp: new Date().toISOString(),
      }

      setConversations((prev) => [newResponse, ...prev])
      setIsTyping(false)
    }, 450)
  }

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div className="pb-2 border-b border-border-subtle">
        <h1 className="heading-4 sm:heading-3 text-white">Plant Engineer Assistant</h1>
        <p className="caption-1 text-text-secondary mt-1">
          Grounded diagnostic assistant that explains machine telemetry and suggests verified actions
        </p>
      </div>

      {/* Query Input Box */}
      <div className="card p-5 bg-bg-card border border-border-default">
        <form
          onSubmit={(e) => {
            e.preventDefault()
            handleAsk()
          }}
          className="relative"
        >
          <input
            type="text"
            placeholder="Ask anything about machine health, RUL, root causes, or financial impact..."
            value={queryInput}
            onChange={(e) => setQueryInput(e.target.value)}
            className="w-full pl-4 pr-12 py-3 bg-bg-raised border border-border-default rounded-xl text-white placeholder-text-muted focus:border-white focus:ring-1 focus:ring-white text-sm"
          />
          <button
            type="submit"
            disabled={!queryInput.trim() || isTyping}
            className="absolute right-2 top-1/2 -translate-y-1/2 p-2 rounded-lg bg-white text-black hover:bg-neutral-200 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
            aria-label="Send question"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>

        {/* Suggested Questions */}
        <div className="mt-4 pt-3 border-t border-border-subtle">
          <div className="caption-5 text-text-muted font-medium mb-2 flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5 text-text-muted" />
            <span>Suggested Questions:</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {SUGGESTED_QUESTIONS.slice(0, 4).map((q, idx) => (
              <button
                key={idx}
                onClick={() => handleAsk(q)}
                className="px-3 py-1.5 rounded-lg bg-bg-raised/80 hover:bg-bg-raised text-text-secondary hover:text-white border border-border-subtle caption-4 transition-colors text-left"
              >
                {q}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Answer Feed */}
      <div className="space-y-6">
        {isTyping && (
          <div className="card p-5 animate-pulse flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-bg-raised flex items-center justify-center">
              <Bot className="w-4 h-4 text-text-muted" />
            </div>
            <span className="caption-4 text-text-muted">
              Synthesizing live telemetry and historical case embeddings...
            </span>
          </div>
        )}

        {conversations.map((item, idx) => (
          <div key={idx} className="card p-6 space-y-5 border border-border-default">
            {/* User Question */}
            <div className="flex items-start gap-3">
              <div className="w-7 h-7 rounded-lg bg-bg-raised border border-border-subtle flex items-center justify-center text-text-muted flex-shrink-0 mt-0.5">
                <HelpCircle className="w-4 h-4" />
              </div>
              <h2 className="title-3 text-white font-medium">{item.query}</h2>
            </div>

            {/* Grounded Plain Language Answer */}
            <div className="p-4 rounded-xl bg-bg-raised/60 border border-border-subtle">
              <div className="flex items-center gap-2 mb-2 caption-5 font-semibold text-text-muted uppercase tracking-wider">
                <Bot className="w-3.5 h-3.5 text-status-info" />
                <span>Diagnostic Assessment</span>
              </div>
              <p className="body-3 text-text-primary leading-relaxed">
                {item.answer}
              </p>
            </div>

            {/* "Data Used" Transparency Section (Mandatory from prompt) */}
            {item.data_sources && item.data_sources.length > 0 && (
              <div>
                <div className="caption-5 font-semibold text-text-muted uppercase tracking-wider mb-2 flex items-center gap-1.5">
                  <Database className="w-3.5 h-3.5" />
                  <span>Data Used to Derive This Answer</span>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2.5">
                  {item.data_sources.map((ds, sIdx) => (
                    <div
                      key={sIdx}
                      className="p-3 rounded-lg bg-bg-card border border-border-subtle"
                    >
                      <div className="caption-5 text-text-muted">{ds.label}</div>
                      <div className="title-5 mono text-white font-medium mt-0.5">{ds.value}</div>
                      <div className="caption-5 text-text-muted mt-1 text-[10px]">{ds.source}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Action Suggestions */}
            {item.suggested_actions && item.suggested_actions.length > 0 && (
              <div className="pt-3 border-t border-border-subtle">
                <span className="caption-5 font-semibold text-text-muted uppercase tracking-wider block mb-2">
                  Suggested Engineering Actions
                </span>
                <div className="space-y-1.5">
                  {item.suggested_actions.map((action, aIdx) => (
                    <div
                      key={aIdx}
                      className="flex items-center gap-2 caption-4 text-text-secondary"
                    >
                      <CheckCircle2 className="w-3.5 h-3.5 text-status-healthy flex-shrink-0" />
                      <span>{action}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

