"""
In-memory SSE queue manager.
Each project gets an asyncio.Queue. The /logs SSE endpoint drains it.
Any service can push events via push_event().
"""
import asyncio
import json
from collections import defaultdict

# project_id -> list of subscriber queues
_subscribers: dict[str, list[asyncio.Queue]] = defaultdict(list)


def subscribe(project_id: str) -> asyncio.Queue:
    q: asyncio.Queue = asyncio.Queue()
    _subscribers[project_id].append(q)
    return q


def unsubscribe(project_id: str, q: asyncio.Queue) -> None:
    try:
        _subscribers[project_id].remove(q)
    except ValueError:
        pass


async def push_event(project_id: str, event_type: str, data: dict) -> None:
    payload = json.dumps({"type": event_type, "data": data})
    for q in list(_subscribers.get(project_id, [])):
        await q.put(payload)


async def event_generator(project_id: str):
    q = subscribe(project_id)
    try:
        while True:
            try:
                payload = await asyncio.wait_for(q.get(), timeout=30)
                yield f"data: {payload}\n\n"
            except asyncio.TimeoutError:
                # Send keepalive comment
                yield ": keepalive\n\n"
    finally:
        unsubscribe(project_id, q)
