import type { Discovery } from '../types'
import { relativeTime } from '../hooks/useOracleStore'

interface Props {
  discoveries: Discovery[]
}

interface DiscoveryCardProps {
  discovery: Discovery
}

function starRating(level: number): string {
  return '★'.repeat(Math.min(level, 5))
}

function DiscoveryCard({ discovery }: DiscoveryCardProps) {
  const isBreakthrough = discovery.breakthrough_level >= 8

  return (
    <div
      className={`w-64 shrink-0 rounded-lg bg-[#0f1f38] border p-3 ${
        isBreakthrough
          ? 'border-amber-500/40 shadow-md shadow-amber-500/20'
          : 'border-white/5'
      }`}
    >
      {/* Title */}
      <div className="text-xs font-bold text-white line-clamp-2 mb-1">
        {discovery.title}
      </div>

      {/* Star level */}
      <div
        className={`text-sm mb-1 ${
          discovery.breakthrough_level >= 7 ? 'text-amber-400' : 'text-slate-500'
        }`}
      >
        {starRating(discovery.breakthrough_level)}
      </div>

      {/* Description */}
      <div className="text-[10px] text-slate-400 line-clamp-3 mb-2">
        {discovery.description}
      </div>

      {/* Agents */}
      <div className="text-[10px] text-slate-500 mb-1 truncate">
        {discovery.agents_involved.length > 0
          ? `By: ${discovery.agents_involved.map(a => a.toUpperCase()).join(', ')}`
          : 'By: ORACLE'}
      </div>

      {/* Timestamp */}
      <div className="text-[9px] text-slate-600">
        {relativeTime(discovery.timestamp)}
      </div>
    </div>
  )
}

function EmptyState() {
  return (
    <div className="flex items-center justify-center w-full py-4">
      <span className="text-[11px] text-slate-600 italic">
        No breakthroughs yet — research in progress...
      </span>
    </div>
  )
}

export default function DiscoveryPanel({ discoveries }: Props) {
  return (
    <div className="bg-[#0a1628] border-t border-white/5 p-3 shrink-0 h-56 overflow-hidden">
      {/* Header */}
      <div className="text-[10px] font-bold tracking-widest text-amber-500 mb-2">
        🌟 BREAKTHROUGHS
      </div>

      {/* Horizontal scroll */}
      <div className="flex gap-3 overflow-x-auto pb-2">
        {discoveries.length === 0 ? (
          <EmptyState />
        ) : (
          discoveries.map(discovery => (
            <DiscoveryCard key={discovery.id} discovery={discovery} />
          ))
        )}
      </div>
    </div>
  )
}
