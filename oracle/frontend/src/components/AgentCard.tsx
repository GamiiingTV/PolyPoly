import type { Agent, AgentStatus } from '../types'

interface Props {
  agent: Agent
}

function getStatusColor(status: AgentStatus): string {
  switch (status) {
    case 'thinking': return 'bg-blue-500'
    case 'researching': return 'bg-emerald-500'
    case 'collaborating': return 'bg-yellow-500'
    case 'synthesizing': return 'bg-purple-500'
    case 'writing': return 'bg-cyan-500'
    default: return 'bg-slate-600'
  }
}

function isActive(status: AgentStatus): boolean {
  return status !== 'idle'
}

function getEnergyColor(energy: number): string {
  if (energy > 70) return 'bg-emerald-500'
  if (energy > 40) return 'bg-amber-500'
  return 'bg-red-500'
}

export default function AgentCard({ agent }: Props) {
  const active = isActive(agent.status)
  const statusDotClass = `${getStatusColor(agent.status)} ${active ? 'animate-pulse' : ''}`

  const cardStyle: React.CSSProperties = {
    borderLeft: `3px solid ${agent.color}`,
    ...(active ? { boxShadow: `0 0 12px ${agent.color}40` } : {}),
  }

  return (
    <div
      className={`relative rounded-lg bg-[#0f1f38] border border-white/5 overflow-hidden card-hover ${active ? 'animate-glow' : ''}`}
      style={cardStyle}
    >
      {/* Top bar */}
      <div className="flex justify-between items-start px-3 pt-3 pb-1">
        <div className="flex items-center gap-2 min-w-0">
          <span className="text-2xl flex-shrink-0">{agent.emoji}</span>
          <span className="text-sm font-bold text-white tracking-wider truncate">
            {agent.name.toUpperCase()}
          </span>
        </div>
        <div
          className={`w-2.5 h-2.5 rounded-full flex-shrink-0 mt-0.5 ml-1 ${statusDotClass}`}
          title={agent.status}
        />
      </div>

      {/* Role */}
      <div className="text-[10px] text-slate-400 px-3 pb-1 truncate">{agent.role}</div>

      {/* Full name */}
      <div className="text-[10px] text-slate-500 italic px-3 pb-2 truncate">{agent.full_name}</div>

      {/* Divider */}
      <div className="border-t border-white/5" />

      {/* Current task */}
      {agent.current_task && (
        <div className="text-[10px] text-slate-300 italic px-3 py-1 truncate">
          <span className="text-slate-500">Tâche : </span>
          {agent.current_task}
        </div>
      )}

      {/* Current thought */}
      <div className="text-[11px] text-slate-200 px-3 py-1 line-clamp-2 min-h-[2rem] transition-all duration-500">
        {agent.current_thought || (
          <span className="text-slate-600 italic">
            {active ? 'En traitement...' : 'En veille'}
          </span>
        )}
      </div>

      {/* Divider */}
      <div className="border-t border-white/5" />

      {/* Stats bar */}
      <div className="flex gap-3 px-3 py-2 text-[10px] text-slate-400">
        <span title="Contributions">💡 {agent.contributions}</span>
        <span title="Discoveries">🔬 {agent.discoveries}</span>
        <span title="Collaborations">🤝 {agent.collaborations}</span>
      </div>

      {/* Energy bar */}
      <div className="h-[2px] w-full bg-white/5">
        <div
          className={`h-full transition-all duration-1000 ${getEnergyColor(agent.energy)}`}
          style={{ width: `${Math.max(0, Math.min(100, agent.energy))}%` }}
        />
      </div>
    </div>
  )
}
