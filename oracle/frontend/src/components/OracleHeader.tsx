import type { SystemMetrics } from '../types'

interface Props {
  metrics: SystemMetrics
  connected: boolean
  retries: number
}

function formatUptime(seconds: number): string {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = Math.floor(seconds % 60)
  return [
    String(h).padStart(2, '0'),
    String(m).padStart(2, '0'),
    String(s).padStart(2, '0'),
  ].join(':')
}

function handleStart() {
  fetch('/api/oracle/start', { method: 'POST' }).catch(console.error)
}

function handleStop() {
  fetch('/api/oracle/stop', { method: 'POST' }).catch(console.error)
}

interface MetricChipProps {
  label: string
  value: string | number
  icon: string
}

function MetricChip({ label, value, icon }: MetricChipProps) {
  return (
    <div className="flex items-center gap-1.5 bg-white/5 rounded px-2 py-1 text-[10px]">
      <span>{icon}</span>
      <span className="text-slate-400">{label}</span>
      <span className="text-white font-bold">{value}</span>
    </div>
  )
}

export default function OracleHeader({ metrics, connected, retries }: Props) {
  return (
    <header className="fixed top-0 left-0 right-0 z-50 h-[72px] bg-[#0a1628]/90 backdrop-blur border-b border-indigo-500/20 px-4 flex items-center justify-between gap-4">
      {/* Left: Branding */}
      <div className="flex flex-col">
        <span className="text-2xl font-bold tracking-[0.3em] text-indigo-400 text-glow">
          O&bull;R&bull;A&bull;C&bull;L&bull;E
        </span>
        <span className="text-[10px] text-slate-500 tracking-widest uppercase">
          Moteur Orchestré de Recherche et d'Apprentissage Collaboratif
        </span>
      </div>

      {/* Center: Connection status */}
      <div className="flex items-center gap-2">
        {connected ? (
          <>
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-[11px] font-bold tracking-widest text-emerald-400">EN DIRECT</span>
          </>
        ) : (
          <>
            <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
            <span className="text-[11px] font-bold tracking-widest text-red-400">
              RECONNEXION{retries > 0 ? ` (${retries})` : ''}...
            </span>
          </>
        )}
      </div>

      {/* Right: Metrics + Controls */}
      <div className="flex items-center gap-2 flex-wrap justify-end">
        <MetricChip icon="📚" label="BC" value={metrics.total_knowledge_entries} />
        <MetricChip icon="💡" label="Déc" value={metrics.total_discoveries} />
        <MetricChip icon="🤝" label="Msgs" value={metrics.agent_interactions} />
        <MetricChip icon="⏱" label="Durée" value={formatUptime(metrics.uptime_seconds)} />

        {/* Start button */}
        <button
          onClick={handleStart}
          className="flex items-center gap-1 px-3 py-1.5 rounded bg-indigo-600 hover:bg-indigo-500 text-white text-[11px] font-bold tracking-wider transition-colors"
        >
          <span>▶</span>
          <span>DÉMARRER</span>
        </button>

        {/* Stop button */}
        <button
          onClick={handleStop}
          className="flex items-center gap-1 px-3 py-1.5 rounded bg-slate-700 hover:bg-slate-600 text-white text-[11px] font-bold tracking-wider transition-colors"
        >
          <span>⏹</span>
          <span>ARRÊTER</span>
        </button>
      </div>
    </header>
  )
}
