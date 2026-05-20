import { useState, useCallback } from 'react'
import type { Agent, ActivityEntry, KnowledgeEntry, Discovery, SystemMetrics, WsMessage } from '../types'
import { useWebSocket } from './useWebSocket'

export function relativeTime(iso: string): string {
  const diff = Math.floor((Date.now() - new Date(iso).getTime()) / 1000)
  if (diff < 5) return 'just now'
  if (diff < 60) return `${diff}s ago`
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
  return `${Math.floor(diff / 3600)}h ago`
}

export function useOracleStore() {
  const [agents, setAgents] = useState<Map<string, Agent>>(new Map())
  const [activities, setActivities] = useState<ActivityEntry[]>([])
  const [discoveries, setDiscoveries] = useState<Discovery[]>([])
  const [knowledge, setKnowledge] = useState<KnowledgeEntry[]>([])
  const [metrics, setMetrics] = useState<SystemMetrics>({
    total_thoughts: 0,
    total_discoveries: 0,
    total_knowledge_entries: 0,
    agent_interactions: 0,
    uptime_seconds: 0,
    status: 'stopped',
  })
  const [latestDiscovery, setLatestDiscovery] = useState<Discovery | null>(null)
  const [initialized, setInitialized] = useState(false)

  const addActivity = useCallback((entry: ActivityEntry) => {
    setActivities(prev => [entry, ...prev].slice(0, 150))
  }, [])

  const handleMessage = useCallback((msg: WsMessage) => {
    const data = msg.data as Record<string, unknown>

    switch (msg.type) {
      case 'system_state': {
        const agMap = new Map<string, Agent>()
        const agArr = (data.agents as Agent[] | undefined) ?? []
        agArr.forEach(a => agMap.set(a.id, a))
        setAgents(agMap)
        const acts = (data.recent_activities as ActivityEntry[] | undefined) ?? []
        setActivities(acts.slice(0, 150))
        const discs = (data.recent_discoveries as Discovery[] | undefined) ?? []
        setDiscoveries(discs)
        setMetrics(prev => ({
          ...prev,
          uptime_seconds: (data.uptime_seconds as number) ?? 0,
          status: (data.status as string) ?? 'stopped',
          total_knowledge_entries: (data.knowledge_count as number) ?? 0,
          total_discoveries: (data.discovery_count as number) ?? 0,
        }))
        setInitialized(true)
        break
      }
      case 'agent_update': {
        const a = data as unknown as Agent
        setAgents(prev => {
          const n = new Map(prev)
          n.set(a.id, { ...prev.get(a.id), ...a })
          return n
        })
        break
      }
      case 'agent_thinking': {
        const { agent_id, content } = data as { agent_id: string; content: string }
        setAgents(prev => {
          const n = new Map(prev)
          const ag = n.get(agent_id)
          if (ag) n.set(agent_id, { ...ag, current_thought: content })
          return n
        })
        break
      }
      case 'knowledge_added': {
        const e = data as unknown as KnowledgeEntry
        setKnowledge(prev => [e, ...prev].slice(0, 60))
        setMetrics(prev => ({ ...prev, total_knowledge_entries: prev.total_knowledge_entries + 1 }))
        addActivity({
          id: e.id,
          agent_id: e.author_agent,
          agent_name: e.author_agent.toUpperCase(),
          agent_emoji: e.author_emoji || '🔬',
          action_type: 'knowledge',
          content: `📚 Added: "${e.title}"`,
          timestamp: e.timestamp,
        })
        break
      }
      case 'discovery': {
        const d = data as unknown as Discovery
        setDiscoveries(prev => [d, ...prev].slice(0, 40))
        setLatestDiscovery(d)
        setMetrics(prev => ({ ...prev, total_discoveries: prev.total_discoveries + 1 }))
        addActivity({
          id: d.id,
          agent_id: d.agents_involved[0] ?? 'oracle',
          agent_name: 'ORACLE',
          agent_emoji: '💡',
          action_type: 'discovery',
          content: `🌟 BREAKTHROUGH: ${d.title}`,
          timestamp: d.timestamp,
        })
        setTimeout(() => setLatestDiscovery(null), 7000)
        break
      }
      case 'agent_message': {
        const m = data as { from_agent: string; from_emoji: string; to_agent: string; content: string }
        addActivity({
          id: Math.random().toString(36).slice(2),
          agent_id: m.from_agent,
          agent_name: m.from_agent.toUpperCase(),
          agent_emoji: m.from_emoji ?? '💬',
          action_type: 'message',
          content: `→ ${m.to_agent.toUpperCase()}: ${m.content.slice(0, 120)}`,
          timestamp: msg.timestamp,
        })
        setMetrics(prev => ({ ...prev, agent_interactions: prev.agent_interactions + 1 }))
        break
      }
      case 'orchestrator_log': {
        const { message } = data as { level: string; message: string }
        addActivity({
          id: Math.random().toString(36).slice(2),
          agent_id: 'nexus',
          agent_name: 'NEXUS',
          agent_emoji: '🧠',
          action_type: 'task',
          content: message,
          timestamp: msg.timestamp,
        })
        break
      }
      case 'metrics_update': {
        setMetrics(prev => ({ ...prev, ...(data as Partial<SystemMetrics>) }))
        break
      }
      default:
        break
    }
  }, [addActivity])

  const { connected, retries } = useWebSocket(handleMessage)

  return {
    agents,
    activities,
    discoveries,
    knowledge,
    metrics,
    connected,
    retries,
    latestDiscovery,
    initialized,
  }
}
