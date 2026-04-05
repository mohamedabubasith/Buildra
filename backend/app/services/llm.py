import json
import httpx
from sqlalchemy.orm import Session
from ..models import LLMConfig
from ..services.crypto import decrypt


class LLMConfigNotFound(Exception):
    pass


def get_llm_config(db: Session) -> dict:
    cfg = db.query(LLMConfig).first()
    if not cfg:
        raise LLMConfigNotFound("LLM config not set. Please configure in Settings.")
    return {
        "api_endpoint": cfg.api_endpoint.rstrip("/"),
        "api_key": decrypt(cfg.api_key_encrypted),
        "model": cfg.model,
    }


async def chat_completion(
    messages: list[dict],
    db: Session,
    json_mode: bool = False,
    temperature: float = 0.2,
) -> str:
    cfg = get_llm_config(db)

    payload: dict = {
        "model": cfg["model"],
        "messages": messages,
        "temperature": temperature,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(
            f"{cfg['api_endpoint']}/chat/completions",
            headers={
                "Authorization": f"Bearer {cfg['api_key']}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]


async def chat_completion_json(messages: list[dict], db: Session) -> dict:
    """Returns parsed JSON from the LLM."""
    raw = await chat_completion(messages, db, json_mode=True)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Try to extract JSON from markdown code block
        import re
        match = re.search(r"```(?:json)?\s*([\s\S]+?)```", raw)
        if match:
            return json.loads(match.group(1))
        raise ValueError(f"LLM did not return valid JSON: {raw[:200]}")
