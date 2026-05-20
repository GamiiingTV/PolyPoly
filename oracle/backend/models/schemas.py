"""O.R.A.C.L.E — Data schemas"""
from __future__ import annotations
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field
import uuid
from datetime import datetime


class AgentStatus(str, Enum):
    idle = "idle"
    thinking = "thinking"
    researching = "researching"
    collaborating = "collaborating"
    synthesizing = "synthesizing"
    writing = "writing"


class ActivityEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: str
    agent_name: str
    agent_emoji: str
    action_type: str  # "thinking", "knowledge", "discovery", "message", "task"
    content: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class AgentInfo(BaseModel):
    id: str
    name: str
    full_name: str
    role: str
    specialty: str
    emoji: str
    color: str
    status: AgentStatus = AgentStatus.idle
    current_task: str | None = None
    current_thought: str | None = None
    contributions: int = 0
    discoveries: int = 0
    collaborations: int = 0
    energy: int = 100
    recent_activities: list[ActivityEntry] = Field(default_factory=list)


class KnowledgeEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    content: str
    author_agent: str
    author_emoji: str
    tags: list[str] = Field(default_factory=list)
    importance: int = Field(ge=1, le=10, default=5)
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class Discovery(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    agents_involved: list[str] = Field(default_factory=list)
    breakthrough_level: int = Field(ge=1, le=10, default=5)
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class AgentMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    from_agent: str
    from_emoji: str
    to_agent: str  # "broadcast" for all
    content: str
    msg_type: str = "insight"  # "insight", "question", "request", "response"
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class SystemMetrics(BaseModel):
    total_thoughts: int = 0
    total_discoveries: int = 0
    total_knowledge_entries: int = 0
    agent_interactions: int = 0
    uptime_seconds: float = 0
    status: str = "stopped"


class WsMessage(BaseModel):
    type: str
    data: dict[str, Any]
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
