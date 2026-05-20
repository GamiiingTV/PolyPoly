import type { Agent } from '../types'
import AgentCard from './AgentCard'

interface Props {
  agents: Map<string, Agent>
  initialized: boolean
}

const STATUS_ORDER: Record<string, number> = {
  thinking: 0,
  researching: 1,
  collaborating: 2,
  synthesizing: 3,
  writing: 4,
  idle: 5,
}

function sortAgents(agents: Map<string, Agent>): Agent[] {
  return Array.from(agents.values()).sort((a, b) => {
    const ao = STATUS_ORDER[a.status] ?? 5
    const bo = STATUS_ORDER[b.status] ?? 5
    if (ao !== bo) return ao - bo
    return a.name.localeCompare(b.name)
  })
}

function SkeletonCard() {
  return (
    <div className="rounded-lg bg-[#0f1f38] border border-white/5 overflow-hidden animate-pulse">
      <div className="flex items-center gap-2 px-3 pt-3 pb-2">
        <div className="w-8 h-8 rounded-full bg-white/10" />
        <div className="flex-1">
          <div className="h-3 bg-white/10 rounded w-2/3 mb-1.5" />
          <div className="h-2 bg-white/5 rounded w-1/2" />
        </div>
        <div className="w-2.5 h-2.5 rounded-full bg-white/10" />
      </div>
      <div className="px-3 pb-2">
        <div className="h-2 bg-white/5 rounded w-3/4 mb-1" />
      </div>
      <div className="border-t border-white/5 mx-3" />
      <div className="px-3 py-2">
        <div className="h-2 bg-white/5 rounded w-full mb-1" />
        <div className="h-2 bg-white/5 rounded w-4/5" />
      </div>
      <div className="border-t border-white/5 mx-3" />
      <div className="flex gap-3 px-3 py-2">
        <div className="h-2 bg-white/5 rounded w-8" />
        <div className="h-2 bg-white/5 rounded w-8" />
        <div className="h-2 bg-white/5 rounded w-8" />
      </div>
      <div className="h-[2px] bg-white/5" />
    </div>
  )
}

export default function AgentGrid({ agents, initialized }: Props) {
  if (!initialized) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-4 gap-2 p-1">
        {Array.from({ length: 8 }).map((_, i) => (
          <SkeletonCard key={i} />
        ))}
      </div>
    )
  }

  const sorted = sortAgents(agents)

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-4 gap-2 p-1">
      {sorted.map(agent => (
        <AgentCard key={agent.id} agent={agent} />
      ))}
    </div>
  )
}
