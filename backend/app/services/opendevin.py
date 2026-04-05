"""
OpenDevin API client.
Sends tasks to OpenDevin and polls for results.

OpenDevin REST API (v0.14+):
  POST /api/conversations           → create a conversation session
  POST /api/conversations/{id}/events → send a message/task
  GET  /api/conversations/{id}/events → poll for events
"""
import asyncio
import httpx
from ..config import settings


class OpenDevinError(Exception):
    pass


async def send_task(task_description: str, workspace_path: str | None = None) -> dict:
    """
    Create a new OpenDevin conversation and send the task.
    Returns {"conversation_id": ..., "status": "running"}.
    """
    base_url = settings.opendevin_url.rstrip("/")

    async with httpx.AsyncClient(timeout=30) as client:
        # Create conversation
        resp = await client.post(
            f"{base_url}/api/conversations",
            json={
                "initial_user_msg": task_description,
                "repository": None,
            },
        )
        if resp.status_code not in (200, 201):
            raise OpenDevinError(f"Failed to create conversation: {resp.status_code} {resp.text}")

        data = resp.json()
        conversation_id = data.get("conversation_id") or data.get("id")
        if not conversation_id:
            raise OpenDevinError(f"No conversation_id in response: {data}")

        return {"conversation_id": conversation_id, "status": "running"}


async def wait_for_result(conversation_id: str, timeout: int = 300) -> dict:
    """
    Poll OpenDevin until the conversation reaches a terminal state.
    Returns {"status": "success"|"error", "output": str, "error": str|None}.
    """
    base_url = settings.opendevin_url.rstrip("/")
    deadline = asyncio.get_event_loop().time() + timeout
    last_event_id = 0
    output_parts: list[str] = []

    async with httpx.AsyncClient(timeout=30) as client:
        while asyncio.get_event_loop().time() < deadline:
            resp = await client.get(
                f"{base_url}/api/conversations/{conversation_id}/events",
                params={"start_id": last_event_id},
            )
            if resp.status_code == 200:
                events = resp.json() if isinstance(resp.json(), list) else resp.json().get("events", [])
                for event in events:
                    last_event_id = max(last_event_id, event.get("id", 0) + 1)
                    etype = event.get("type") or event.get("action") or event.get("observation", "")

                    # Collect output messages
                    if "message" in event:
                        output_parts.append(str(event["message"]))
                    if "content" in event:
                        output_parts.append(str(event["content"]))

                    # Check for terminal state
                    if etype in ("AgentFinishAction", "finish", "agent_finish"):
                        return {
                            "status": "success",
                            "output": "\n".join(output_parts),
                            "error": None,
                        }
                    if etype in ("ErrorObservation", "error"):
                        return {
                            "status": "error",
                            "output": "\n".join(output_parts),
                            "error": event.get("message") or event.get("content") or "Unknown error",
                        }

            await asyncio.sleep(3)

    return {
        "status": "error",
        "output": "\n".join(output_parts),
        "error": f"Timeout after {timeout}s",
    }
