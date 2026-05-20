import { useState, useRef, useEffect } from 'react'
import type { JarvisContribution, JarvisContradiction, JarvisMessage, JarvisPhase } from '../types'

interface Props {
  phase: JarvisPhase
  contributions: JarvisContribution[]
  contradictions: JarvisContradiction[]
  messages: JarvisMessage[]
  onSend: (msg: string) => void
  onBuild: () => void
}

function PhaseBar({ phase }: { phase: JarvisPhase }) {
  const steps: { key: JarvisPhase; label: string }[] = [
    { key: 'contributing', label: 'Contributions' },
    { key: 'debate', label: 'Débat' },
    { key: 'synthesis', label: 'Synthèse' },
    { key: 'ready', label: 'En ligne' },
  ]
  const order: JarvisPhase[] = ['idle', 'building', 'contributing', 'debate', 'synthesis', 'ready']
  const current = order.indexOf(phase)

  return (
    <div className="flex items-center gap-1 px-3 py-2 border-b border-blue-500/20">
      {steps.map((s, i) => {
        const stepOrder = order.indexOf(s.key)
        const done = current >= stepOrder
        return (
          <div key={s.key} className="flex items-center gap-1 flex-1">
            <div className={`flex-1 h-0.5 ${i === 0 ? 'hidden' : ''} ${done ? 'bg-blue-400' : 'bg-slate-700'}`} />
            <div className={`text-[10px] font-bold tracking-wide whitespace-nowrap ${done ? 'text-blue-400' : 'text-slate-600'}`}>
              {done && s.key === phase && s.key !== 'ready' ? (
                <span className="animate-pulse">{s.label}</span>
              ) : s.label}
            </div>
          </div>
        )
      })}
    </div>
  )
}

function ContributionCard({ c }: { c: JarvisContribution }) {
  return (
    <div className="rounded-lg p-2.5 bg-slate-900/70 border border-slate-700/50">
      <div className="flex items-center gap-1.5 mb-1">
        <span className="text-sm">{c.agent_emoji}</span>
        <span className="text-[11px] font-bold text-slate-300">{c.agent_name}</span>
        {c.contradicts.length > 0 && (
          <span className="ml-auto text-[9px] text-red-400 border border-red-500/30 rounded px-1">
            ⚡ {c.contradicts.map(x => x.toUpperCase()).join(', ')}
          </span>
        )}
      </div>
      <p className="text-[11px] text-slate-400 leading-relaxed">{c.contribution}</p>
      <div className="mt-1.5 text-[10px] text-blue-400/80 font-medium">→ {c.key_requirement}</div>
      <div className="mt-0.5 text-[10px] text-amber-500/70 italic">⚠ {c.warning}</div>
    </div>
  )
}

function ClashCard({ clash }: { clash: JarvisContradiction }) {
  return (
    <div className="rounded-lg p-2.5 bg-red-950/30 border border-red-500/30">
      <div className="flex items-center gap-2 mb-1">
        <span className="text-sm">{clash.agent_a_emoji}</span>
        <span className="text-[11px] font-bold text-red-400">{clash.agent_a.toUpperCase()}</span>
        <span className="text-red-500 font-bold">⚡</span>
        <span className="text-[11px] font-bold text-red-400">{clash.agent_b.toUpperCase()}</span>
        <span className="text-sm">{clash.agent_b_emoji}</span>
      </div>
      <p className="text-[11px] text-red-300/80 leading-relaxed">{clash.topic}</p>
    </div>
  )
}

function ChatBubble({ msg }: { msg: JarvisMessage }) {
  const isJarvis = msg.role === 'assistant'
  return (
    <div className={`flex ${isJarvis ? 'justify-start' : 'justify-end'}`}>
      <div
        className={`max-w-[85%] rounded-xl px-3 py-2 text-[12px] leading-relaxed ${
          isJarvis
            ? 'bg-slate-800 border border-blue-500/20 text-slate-200'
            : 'bg-blue-600 text-white'
        }`}
      >
        {isJarvis && (
          <div className="text-[10px] font-bold text-blue-400 mb-1 tracking-widest">J.A.R.V.I.S</div>
        )}
        <p>{msg.content}</p>
        {isJarvis && msg.dispatches.length > 0 && (
          <div className="mt-1.5 flex flex-wrap gap-1">
            {msg.dispatches.map((d, i) => (
              <span
                key={i}
                className="text-[9px] bg-blue-900/50 border border-blue-500/30 text-blue-300 rounded px-1.5 py-0.5"
              >
                ⚡ {d.agent_id.toUpperCase()}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default function JarvisChat({ phase, contributions, contradictions, messages, onSend, onBuild }: Props) {
  const [input, setInput] = useState('')
  const [showDesign, setShowDesign] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = () => {
    const txt = input.trim()
    if (!txt) return
    setInput('')
    onSend(txt)
  }

  // ── Idle state — big "Build JARVIS" button ─────────────────────────
  if (phase === 'idle') {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-4 px-4">
        <div className="text-4xl">🤖</div>
        <div className="text-center">
          <div className="text-sm font-bold text-slate-200 mb-1">J.A.R.V.I.S</div>
          <div className="text-[11px] text-slate-500 leading-relaxed">
            Les 16 agents vont concevoir ensemble votre intelligence centrale.<br />
            Ils débattront, se contrediront, et convergeront.
          </div>
        </div>
        <button
          onClick={onBuild}
          className="px-5 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-sm font-bold transition-colors"
        >
          Construire J.A.R.V.I.S
        </button>
      </div>
    )
  }

  // ── Building state — design session live ───────────────────────────
  if (phase !== 'ready') {
    return (
      <div className="flex flex-col h-full">
        <PhaseBar phase={phase} />
        <div className="flex-1 overflow-y-auto p-2 space-y-2">
          {contributions.length === 0 && (
            <div className="text-center text-slate-500 text-[12px] pt-8 animate-pulse">
              Les agents se concertent...
            </div>
          )}
          {contributions.map((c, i) => <ContributionCard key={i} c={c} />)}
          {contradictions.map((clash, i) => <ClashCard key={i} clash={clash} />)}
        </div>
      </div>
    )
  }

  // ── Ready state — chat interface ───────────────────────────────────
  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center gap-2 px-3 py-2 border-b border-blue-500/20 bg-slate-900/50">
        <div className="w-2 h-2 rounded-full bg-blue-400 animate-pulse" />
        <span className="text-[11px] font-bold text-blue-400 tracking-widest">J.A.R.V.I.S</span>
        <span className="text-[10px] text-slate-500">— OPÉRATIONNEL</span>
        <button
          onClick={() => setShowDesign(v => !v)}
          className="ml-auto text-[9px] text-slate-500 hover:text-slate-300 transition-colors"
        >
          {showDesign ? '▾ masquer' : '▸ conception'}
        </button>
      </div>

      {/* Design session collapsible */}
      {showDesign && (
        <div className="max-h-48 overflow-y-auto border-b border-slate-700/50 p-2 space-y-2 bg-slate-950/50">
          {contributions.map((c, i) => <ContributionCard key={i} c={c} />)}
          {contradictions.map((clash, i) => <ClashCard key={i} clash={clash} />)}
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-3 space-y-3">
        {messages.length === 0 && (
          <div className="text-center text-slate-600 text-[11px] pt-4">
            Systèmes en ligne — parlez-moi.
          </div>
        )}
        {messages.map((m, i) => <ChatBubble key={i} msg={m} />)}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="flex gap-2 p-2 border-t border-blue-500/20">
        <input
          ref={inputRef}
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleSend()}
          placeholder="Parlez à J.A.R.V.I.S..."
          className="flex-1 bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-[12px] text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500"
        />
        <button
          onClick={handleSend}
          disabled={!input.trim()}
          className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 disabled:opacity-30 text-white text-[12px] font-bold rounded-lg transition-colors"
        >
          →
        </button>
      </div>
    </div>
  )
}
