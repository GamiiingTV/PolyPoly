import type { Agent, ActivityEntry, Discovery, KnowledgeEntry, SystemMetrics } from '../types'
import OracleHeader from './OracleHeader'
import AgentGrid from './AgentGrid'
import ActivityFeed from './ActivityFeed'
import DiscoveryPanel from './DiscoveryPanel'

interface Props {
  agents: Map<string, Agent>
  activities: ActivityEntry[]
  discoveries: Discovery[]
  knowledge: KnowledgeEntry[]
  metrics: SystemMetrics
  connected: boolean
  retries: number
  latestDiscovery: Discovery | null
  initialized: boolean
}

function starRating(level: number): string {
  return '★'.repeat(Math.min(level, 5))
}

function BreakthroughOverlay({ discovery }: { discovery: Discovery }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm animate-fade-in">
      <div
        className="max-w-lg w-full mx-4 rounded-2xl p-8 text-center animate-fade-in"
        style={{
          background: 'linear-gradient(135deg, #1a1000 0%, #0f1f38 50%, #1a0f00 100%)',
          border: '1px solid rgba(245, 158, 11, 0.5)',
          boxShadow:
            '0 0 40px rgba(245,158,11,0.3), 0 0 80px rgba(245,158,11,0.15), inset 0 1px 0 rgba(255,255,255,0.05)',
        }}
      >
        {/* Icon */}
        <div className="text-5xl mb-4">💡</div>

        {/* Label */}
        <div className="text-[11px] font-bold tracking-[0.4em] text-amber-400 mb-3 uppercase">
          Découverte Révolutionnaire
        </div>

        {/* Title */}
        <div className="text-2xl font-bold text-white mb-3 leading-snug">
          {discovery.title}
        </div>

        {/* Stars */}
        <div className="text-amber-400 text-2xl mb-4" title={`Level ${discovery.breakthrough_level}`}>
          {starRating(discovery.breakthrough_level)}
        </div>

        {/* Description */}
        <div className="text-sm text-slate-300 leading-relaxed mb-4">
          {discovery.description}
        </div>

        {/* Agents */}
        {discovery.agents_involved.length > 0 && (
          <div className="text-[11px] text-slate-500">
            Achieved by: {discovery.agents_involved.map(a => a.toUpperCase()).join(', ')}
          </div>
        )}
      </div>
    </div>
  )
}

export default function Dashboard({
  agents,
  activities,
  discoveries,
  metrics,
  connected,
  retries,
  latestDiscovery,
  initialized,
}: Props) {
  const showOverlay = latestDiscovery !== null && latestDiscovery.breakthrough_level >= 7

  return (
    <div className="flex flex-col h-screen bg-[#030712] overflow-hidden">
      {/* Fixed header */}
      <OracleHeader metrics={metrics} connected={connected} retries={retries} />

      {/* Content below header */}
      <div className="flex h-[calc(100vh-72px)] mt-[72px] overflow-hidden">
        {/* Left column: Agent grid + Discoveries */}
        <div className="flex-1 flex flex-col gap-2 p-3 overflow-hidden">
          {/* Agent grid — scrollable */}
          <div className="flex-1 overflow-y-auto">
            <AgentGrid agents={agents} initialized={initialized} />
          </div>

          {/* Discovery panel — fixed height */}
          <DiscoveryPanel discoveries={discoveries} />
        </div>

        {/* Right column: Activity feed */}
        <div className="w-80 lg:w-96 h-full overflow-hidden border-l border-indigo-500/20 flex-shrink-0">
          <ActivityFeed activities={activities} />
        </div>
      </div>

      {/* Breakthrough overlay */}
      {showOverlay && latestDiscovery && (
        <BreakthroughOverlay discovery={latestDiscovery} />
      )}
    </div>
  )
}
