"""O.R.A.C.L.E — Message Bus for agent communication"""
import asyncio
from typing import Callable, Awaitable
from loguru import logger
from ..models.schemas import AgentMessage


class MessageBus:
    def __init__(self):
        self._queues: dict[str, asyncio.Queue] = {}
        self._broadcast_callbacks: list[Callable] = []

    def register_agent(self, agent_id: str):
        if agent_id not in self._queues:
            self._queues[agent_id] = asyncio.Queue(maxsize=50)

    def unregister_agent(self, agent_id: str):
        self._queues.pop(agent_id, None)

    async def publish(self, message: AgentMessage):
        """Send message to specific agent or broadcast."""
        if message.to_agent == "broadcast":
            await self._do_broadcast(message)
        else:
            q = self._queues.get(message.to_agent)
            if q:
                try:
                    q.put_nowait(message)
                except asyncio.QueueFull:
                    logger.warning(f"Queue full for {message.to_agent}, dropping message")

    async def _do_broadcast(self, message: AgentMessage):
        for agent_id, q in self._queues.items():
            if agent_id != message.from_agent:
                try:
                    q.put_nowait(message)
                except asyncio.QueueFull:
                    pass
        for cb in self._broadcast_callbacks:
            try:
                await cb(message)
            except Exception as e:
                logger.error(f"Broadcast callback error: {e}")

    async def get_message(self, agent_id: str, timeout: float = 0.1) -> AgentMessage | None:
        """Non-blocking message retrieval for an agent."""
        q = self._queues.get(agent_id)
        if not q:
            return None
        try:
            return await asyncio.wait_for(q.get(), timeout=timeout)
        except asyncio.TimeoutError:
            return None

    def add_broadcast_listener(self, callback: Callable):
        self._broadcast_callbacks.append(callback)

    @property
    def agent_count(self) -> int:
        return len(self._queues)
