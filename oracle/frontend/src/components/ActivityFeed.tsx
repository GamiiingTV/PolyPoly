import type { ActivityEntry } from '../types'
import { relativeTime } from '../hooks/useOracleStore'

interface Props {
  activities: ActivityEntry[]
}

const AGENT_COLORS: Record<string, string> = {
  nexus: '#6366f1',
  quantum: '#7c3aed',
  helix: '#059669',
  neural: '#2563eb',
  atlas: '#64748b',
  gaia: '#16a34a',
  cipher: '#0891b2',
  medicus: '#dc2626',
  alchemist: '#d97706',
  dynamo: '#ca8a04',
  axiom: '#7e22ce',
  ethikos: '#be185d',
  forge: '#b45309',
  cosmos: '#1d4ed8',
  synapse: '#be123c',
  herald: '#0f766e',
}

function getActionIcon(actionType: string): string {
  switch (actionType) {
    case 'knowledge': return '📚'
    case 'discovery': return '💡'
    case 'message': return '💬'
    case 'task': return '🎯'
    case 'thinking': return '💭'
    default: return '🔬'
  }
}

function getAgentColor(agentId: string): string {
  return AGENT_COLORS[agentId.toLowerCase()] ?? '#64748b'
}

interface ActivityItemProps {
  activity: ActivityEntry
}

function ActivityItem({ activity }: ActivityItemProps) {
  const color = getAgentColor(activity.agent_id)
  const icon = getActionIcon(activity.action_type)

  return (
    <div
      className="animate-slide-in border-l-2 pl-2 py-1.5 mb-1 rounded-sm bg-white/[0.02]"
      style={{ borderColor: color }}
    >
      <div className="flex items-center justify-between gap-1 mb-0.5">
        <div className="flex items-center gap-1 min-w-0">
          <span className="text-[11px]">{activity.agent_emoji}</span>
          <span
            className="text-[10px] font-bold truncate"
            style={{ color }}
          >
            {activity.agent_name}
          </span>
          <span className="text-[10px] flex-shrink-0">{icon}</span>
        </div>
        <span className="text-[9px] text-slate-600 flex-shrink-0 ml-1">
          {relativeTime(activity.timestamp)}
        </span>
      </div>
      <div className="text-[10px] text-slate-300 leading-relaxed line-clamp-2">
        {activity.content}
      </div>
    </div>
  )
}

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center h-full text-slate-600 py-8">
      <div className="text-2xl mb-2">🔮</div>
      <div className="text-[11px] text-center italic">
        Waiting for research activity
        <span className="inline-flex gap-0.5 ml-0.5">
          <span className="animate-bounce" style={{ animationDelay: '0ms' }}>.</span>
          <span className="animate-bounce" style={{ animationDelay: '150ms' }}>.</span>
          <span className="animate-bounce" style={{ animationDelay: '300ms' }}>.</span>
        </span>
      </div>
    </div>
  )
}

export default function ActivityFeed({ activities }: Props) {
  return (
    <div className="h-full flex flex-col overflow-hidden">
      {/* Header */}
      <div className="px-3 py-2 border-b border-white/5 flex-shrink-0">
        <span className="text-[11px] font-bold tracking-widest text-slate-400">
          ⚡ LIVE FEED
        </span>
      </div>

      {/* Scroll area */}
      <div className="flex-1 overflow-y-auto px-2 py-1">
        {activities.length === 0 ? (
          <EmptyState />
        ) : (
          activities.map(activity => (
            <ActivityItem key={activity.id} activity={activity} />
          ))
        )}
      </div>
    </div>
  )
}
