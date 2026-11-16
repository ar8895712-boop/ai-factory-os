// ==============================================================
// frontend/src/pages/FactoryGPT.jsx — Phase 6
// Factory GPT Assistant (RAG + Autonomous Tool Calling) & Memory
// ==============================================================
import React, { useState, useEffect, useRef } from 'react'
import axios from 'axios'
import {
  Bot, User, Send, Sparkles, Database, Wrench, Search,
  ChevronDown, ChevronRight, AlertTriangle, ShieldCheck,
  CheckCircle2, RefreshCw, Cpu, Layers, HelpCircle
} from 'lucide-react'

const SUGGESTED_PROMPTS = [
  "Why is Machine 3 failing?",
  "What if I shut down Machine 2 for 4 hours?",
  "What happened last time with high vibration and chatter?",
  "What is our total financial exposure across the factory floor?",
  "What is the predicted RUL and status of Turbine-04?",
]

export function FactoryGPT({ machines = [] }) {
  const [messages, setMessages] = useState([
    {
      id: 1,
      role: 'assistant',
      content:
        "Hello! I am **Factory GPT**, your asset reliability AI assistant.\n\n" +
        "I have real-time access to the **6 simulated machines**, live **NASA C-MAPSS degradation models**, " +
        "the **SimPy what-if engine**, and our **FAISS incident memory**.\n\n" +
        "I never guess numbers—I query our backend tools to give you verified diagnostics.",
      tool_calls: [],
      timestamp: new Date().toLocaleTimeString(),
    },
  ])
  const [inputQuery, setInputQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [activeView, setActiveView] = useState('chat') // 'chat' | 'memory' | 'patterns'
  const [expandedToolIndex, setExpandedToolIndex] = useState(null)

  // Memory explorer state
  const [memoryQuery, setMemoryQuery] = useState('pressure spike and valve leak')
  const [memoryMatches, setMemoryMatches] = useState([])
  const [memoryLoading, setMemoryLoading] = useState(false)
  const [patterns, setPatterns] = useState([])

  const chatEndRef = useRef(null)

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, loading])

  // Load failure patterns on mount
  useEffect(() => {
    axios.get('/api/memory/patterns')
      .then((res) => setPatterns(res.data))
      .catch((err) => console.error('Failed to load patterns:', err))
  }, [])

  // Send message to Factory GPT
  const handleSendMessage = async (textToSend) => {
    const q = textToSend || inputQuery
    if (!q.trim() || loading) return

    const userMsg = {
      id: Date.now(),
      role: 'user',
      content: q,
      tool_calls: [],
      timestamp: new Date().toLocaleTimeString(),
    }

    setMessages((prev) => [...prev, userMsg])
    setInputQuery('')
    setLoading(true)

    try {
      const historyPayload = messages.slice(-4).map((m) => ({
        role: m.role,
        content: m.content,
      }))

      const { data } = await axios.post('/api/chat/message', {
        query: q,
        conversation_history: historyPayload,
      })

      const botMsg = {
        id: Date.now() + 1,
        role: 'assistant',
        content: data.content,
        tool_calls: data.tool_calls || [],
        timestamp: new Date().toLocaleTimeString(),
      }

      setMessages((prev) => [...prev, botMsg])
    } catch (err) {
      console.error('Chat error:', err)
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          role: 'assistant',
          content: "⚠️ I encountered an error connecting to the backend tool dispatcher. Please ensure the backend is running.",
          tool_calls: [],
          timestamp: new Date().toLocaleTimeString(),
        },
      ])
    } finally {
      setLoading(false)
    }
  }

  // Handle direct FAISS memory search
  const handleSearchMemory = async () => {
    if (!memoryQuery.trim()) return
    setMemoryLoading(true)
    try {
      const { data } = await axios.post('/api/memory/search', {
        query: memoryQuery,
        top_k: 4,
      })
      setMemoryMatches(data)
    } catch (err) {
      console.error('Memory search error:', err)
    } finally {
      setMemoryLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* ── Header ─────────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-white tracking-tight">Factory GPT Assistant</h1>
            <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-gradient-to-r from-blue-500/20 to-purple-500/20 text-blue-400 border border-blue-500/30 flex items-center gap-1">
              <Sparkles size={12} /> RAG + Autonomous Tool Calling
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            LLM intelligence bounded by verified engineering models • FAISS vector incident memory
          </p>
        </div>

        {/* View Switcher */}
        <div className="flex bg-slate-900 border border-slate-800 p-1 rounded-xl text-xs font-medium">
          <button
            onClick={() => setActiveView('chat')}
            className={`px-3 py-1.5 rounded-lg transition ${
              activeView === 'chat'
                ? 'bg-blue-600 text-white font-semibold'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            Assistant Dialogue
          </button>
          <button
            onClick={() => {
              setActiveView('memory')
              if (memoryMatches.length === 0) handleSearchMemory()
            }}
            className={`px-3 py-1.5 rounded-lg transition flex items-center gap-1.5 ${
              activeView === 'memory'
                ? 'bg-blue-600 text-white font-semibold'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <Database size={12} /> Vector Memory Search
          </button>
          <button
            onClick={() => setActiveView('patterns')}
            className={`px-3 py-1.5 rounded-lg transition flex items-center gap-1.5 ${
              activeView === 'patterns'
                ? 'bg-blue-600 text-white font-semibold'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <Layers size={12} /> Discovered Patterns
          </button>
        </div>
      </div>

      {/* ── View 1: Main Chat Interface ──────────────────────── */}
      {activeView === 'chat' && (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl flex flex-col h-[650px] shadow-xl overflow-hidden">
          {/* Chat Messages Log */}
          <div className="flex-1 p-4 sm:p-6 overflow-y-auto space-y-4">
            {messages.map((m) => {
              const isBot = m.role === 'assistant'
              return (
                <div
                  key={m.id}
                  className={`flex items-start gap-3 ${isBot ? '' : 'flex-row-reverse'}`}
                >
                  <div
                    className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 text-white font-bold text-xs ${
                      isBot
                        ? 'bg-gradient-to-tr from-blue-600 to-indigo-600 shadow-md shadow-blue-500/20'
                        : 'bg-slate-700'
                    }`}
                  >
                    {isBot ? <Bot size={16} /> : <User size={16} />}
                  </div>

                  <div className={`max-w-[85%] space-y-2 ${isBot ? '' : 'items-end'}`}>
                    {/* Tool Call Badges if assistant executed tools */}
                    {isBot && m.tool_calls && m.tool_calls.length > 0 && (
                      <div className="space-y-1.5 mb-2">
                        <div className="text-[10px] uppercase font-bold tracking-wider text-slate-500 flex items-center gap-1">
                          <Cpu size={11} className="text-blue-400" />
                          Backend Tools Invoked ({m.tool_calls.length})
                        </div>
                        <div className="flex flex-wrap gap-1.5">
                          {m.tool_calls.map((tc, idx) => {
                            const isExpanded = expandedToolIndex === `${m.id}-${idx}`
                            return (
                              <div key={idx} className="w-full">
                                <button
                                  onClick={() => setExpandedToolIndex(isExpanded ? null : `${m.id}-${idx}`)}
                                  className="w-full text-left bg-slate-950 hover:bg-slate-800/80 border border-slate-800 rounded-lg px-2.5 py-1.5 flex items-center justify-between text-xs font-mono transition"
                                >
                                  <div className="flex items-center gap-1.5 text-blue-400">
                                    <span className="text-emerald-400">⚡</span>
                                    <span className="font-semibold">{tc.tool_name}</span>
                                    <span className="text-slate-500 text-[10px]">
                                      ({Object.entries(tc.arguments || {}).map(([k, v]) => `${k}=${v}`).join(', ')})
                                    </span>
                                  </div>
                                  <div className="flex items-center gap-1 text-[10px] text-slate-500">
                                    <span>inspect result</span>
                                    <ChevronDown size={12} className={`transition ${isExpanded ? 'rotate-180' : ''}`} />
                                  </div>
                                </button>
                                {isExpanded && (
                                  <div className="mt-1 p-2.5 bg-slate-950 border border-slate-800 rounded-lg text-[11px] font-mono text-slate-300 overflow-x-auto max-h-48">
                                    <pre>{JSON.stringify(tc.result, null, 2)}</pre>
                                  </div>
                                )}
                              </div>
                            )
                          })}
                        </div>
                      </div>
                    )}

                    {/* Message Bubble */}
                    <div
                      className={`p-4 rounded-2xl text-xs sm:text-sm leading-relaxed ${
                        isBot
                          ? 'bg-slate-950/80 border border-slate-800 text-slate-200'
                          : 'bg-blue-600 text-white rounded-tr-none'
                      }`}
                    >
                      <div className="whitespace-pre-wrap">{m.content}</div>
                    </div>
                    <div className="text-[10px] text-slate-500 px-1">{m.timestamp}</div>
                  </div>
                </div>
              )
            })}

            {loading && (
              <div className="flex items-start gap-3">
                <div className="w-8 h-8 rounded-xl bg-blue-600 flex items-center justify-center shrink-0 text-white">
                  <Bot size={16} />
                </div>
                <div className="bg-slate-950 border border-slate-800 p-3.5 rounded-2xl flex items-center gap-2 text-xs text-slate-400">
                  <div className="w-2 h-2 rounded-full bg-blue-400 animate-pulse" />
                  <span>Factory GPT is analyzing telemetry & querying backend tools…</span>
                </div>
              </div>
            )}
            <div ref={chatEndRef} />
          </div>

          {/* Quick Prompt Suggestions */}
          <div className="px-4 py-2 bg-slate-950/70 border-t border-slate-800/80 flex items-center gap-2 overflow-x-auto scrollbar-none">
            <span className="text-[10px] font-semibold uppercase text-slate-500 shrink-0 flex items-center gap-1">
              <Sparkles size={10} /> Quick Ask:
            </span>
            {SUGGESTED_PROMPTS.map((p, idx) => (
              <button
                key={idx}
                onClick={() => handleSendMessage(p)}
                disabled={loading}
                className="shrink-0 bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 text-xs px-2.5 py-1 rounded-lg transition"
              >
                {p}
              </button>
            ))}
          </div>

          {/* Input Box */}
          <div className="p-3 bg-slate-950 border-t border-slate-800">
            <form
              onSubmit={(e) => {
                e.preventDefault()
                handleSendMessage()
              }}
              className="flex items-center gap-2"
            >
              <input
                type="text"
                value={inputQuery}
                onChange={(e) => setInputQuery(e.target.value)}
                placeholder="Ask about machine health, failure causes, what-if simulations, or historical incidents..."
                className="flex-1 bg-slate-900 border border-slate-800 rounded-xl px-4 py-2.5 text-xs sm:text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500 transition"
              />
              <button
                type="submit"
                disabled={!inputQuery.trim() || loading}
                className="bg-blue-600 hover:bg-blue-500 disabled:opacity-40 text-white p-2.5 rounded-xl shadow-md shadow-blue-600/30 transition flex items-center justify-center"
              >
                <Send size={16} />
              </button>
            </form>
          </div>
        </div>
      )}

      {/* ── View 2: Vector Memory Explorer ───────────────────── */}
      {activeView === 'memory' && (
        <div className="space-y-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
            <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2 flex items-center gap-1.5">
              <Database size={13} className="text-blue-400" /> FAISS Vector Incident Retrieval
            </h3>
            <p className="text-xs text-slate-400 mb-4">
              Query historical factory incidents using 384-dimensional dense semantic vectors. Returns closest cosine matches.
            </p>

            <div className="flex gap-2">
              <input
                type="text"
                value={memoryQuery}
                onChange={(e) => setMemoryQuery(e.target.value)}
                placeholder="Search symptoms (e.g. 'compressor thermal surge', 'vibration in milling spindle')..."
                className="flex-1 bg-slate-950 border border-slate-800 rounded-xl px-4 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500"
              />
              <button
                onClick={handleSearchMemory}
                disabled={memoryLoading}
                className="bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold px-4 py-2 rounded-xl flex items-center gap-1.5 transition"
              >
                {memoryLoading ? <RefreshCw size={13} className="animate-spin" /> : <Search size={13} />}
                <span>Vector Search</span>
              </button>
            </div>
          </div>

          {/* Results Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {memoryMatches.map((m) => (
              <div
                key={m.incident_id}
                className="bg-slate-900 border border-slate-800 rounded-2xl p-4 space-y-3"
              >
                <div className="flex items-start justify-between">
                  <div>
                    <span className="text-xs font-bold text-white">{m.machine_name}</span>
                    <span className="text-[10px] text-slate-500 ml-2 font-mono">Incident #{m.incident_id}</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className="text-[10px] px-2 py-0.5 rounded-full font-bold uppercase bg-blue-500/10 text-blue-400 border border-blue-500/20 font-mono">
                      {(m.similarity_score * 100).toFixed(1)}% Match
                    </span>
                    <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold uppercase ${
                      m.severity === 'critical'
                        ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                        : 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                    }`}>
                      {m.severity}
                    </span>
                  </div>
                </div>

                <p className="text-xs text-slate-300 leading-relaxed">
                  {m.description}
                </p>

                {m.resolution_notes && (
                  <div className="p-2.5 rounded-xl bg-slate-950 border border-slate-800/80 text-xs">
                    <div className="text-[10px] font-semibold text-emerald-400 uppercase tracking-wider mb-0.5 flex items-center gap-1">
                      <CheckCircle2 size={11} /> Resolution Applied
                    </div>
                    <div className="text-slate-300 text-[11px] leading-relaxed">
                      {m.resolution_notes}
                    </div>
                  </div>
                )}

                <div className="flex items-center justify-between text-[10px] text-slate-500 font-mono pt-1 border-t border-slate-800/60">
                  <span>Action: {m.action_taken || 'inspected'}</span>
                  <span>{new Date(m.timestamp).toLocaleDateString()}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── View 3: Failure Pattern Signatures ───────────────── */}
      {activeView === 'patterns' && (
        <div className="space-y-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
            <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2 flex items-center gap-1.5">
              <Layers size={13} className="text-purple-400" /> Discovered Failure Signatures
            </h3>
            <p className="text-xs text-slate-400">
              Aggregated from historical failure logs. Identifies recurring degradation patterns and optimal self-healing actions.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {patterns.map((p, idx) => (
              <div
                key={idx}
                className="bg-slate-900 border border-slate-800 rounded-2xl p-4 space-y-3"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold font-mono text-purple-400 uppercase">
                    {p.category.replace(/_/g, ' ')}
                  </span>
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 font-mono">
                    {p.frequency} event(s)
                  </span>
                </div>

                <div>
                  <div className="text-[10px] uppercase font-semibold text-slate-500 mb-1">Affected Machines</div>
                  <div className="flex flex-wrap gap-1">
                    {p.affected_machines.map((name, i) => (
                      <span key={i} className="text-[10px] px-2 py-0.5 rounded bg-slate-950 text-slate-300 border border-slate-800">
                        {name}
                      </span>
                    ))}
                  </div>
                </div>

                <div>
                  <div className="text-[10px] uppercase font-semibold text-slate-500 mb-1">Common Sensor Symptoms</div>
                  <div className="flex flex-wrap gap-1">
                    {p.common_symptoms.map((sym, i) => (
                      <span key={i} className="text-[10px] px-2 py-0.5 rounded bg-rose-500/10 text-rose-300 border border-rose-500/20 font-mono">
                        {sym}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="pt-2 border-t border-slate-800 flex items-center justify-between text-xs">
                  <span className="text-[10px] text-slate-500 uppercase">Recommended Action:</span>
                  <span className="font-mono text-emerald-400 font-bold text-[11px]">
                    {p.recommended_action}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

