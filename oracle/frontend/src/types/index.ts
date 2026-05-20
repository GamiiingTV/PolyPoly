export type AgentStatus = 'idle' | 'thinking' | 'researching' | 'collaborating' | 'synthesizing' | 'writing'

export interface ActivityEntry {
  id: string
  agent_id: string
  agent_name: string
  agent_emoji: string
  action_type: string
  content: string
  timestamp: string
}

export interface Agent {
  id: string
  name: string
  full_name: string
  role: string
  specialty: string
  emoji: string
  color: string
  status: AgentStatus
  current_task: string | null
  current_thought: string | null
  contributions: number
  discoveries: number
  collaborations: number
  energy: number
  recent_activities: ActivityEntry[]
}

export interface KnowledgeEntry {
  id: string
  title: string
  content: string
  author_agent: string
  author_emoji: string
  tags: string[]
  importance: number
  timestamp: string
}

export interface Discovery {
  id: string
  title: string
  description: string
  agents_involved: string[]
  breakthrough_level: number
  timestamp: string
}

export interface SystemMetrics {
  total_thoughts: number
  total_discoveries: number
  total_knowledge_entries: number
  agent_interactions: number
  uptime_seconds: number
  status: string
}

export interface WsMessage {
  type: string
  data: Record<string, unknown>
  timestamp: string
}

// JARVIS types
export interface JarvisContribution {
  agent_id: string
  agent_name: string
  agent_emoji: string
  contribution: string
  key_requirement: string
  warning: string
  agrees_with: string[]
  contradicts: string[]
  timestamp: string
}

export interface JarvisContradiction {
  agent_a: string
  agent_a_emoji: string
  agent_b: string
  agent_b_emoji: string
  topic: string
  timestamp: string
}

export type JarvisPhase = 'idle' | 'building' | 'contributing' | 'debate' | 'synthesis' | 'ready'

export interface JarvisMessage {
  role: 'user' | 'assistant'
  content: string
  dispatches: { agent_id: string; task: string }[]
  timestamp: string
}
