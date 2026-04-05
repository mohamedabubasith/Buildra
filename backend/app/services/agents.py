"""
Agent functions — each calls the LLM with a specific prompt.
No framework; just direct async LLM calls.
"""
import json
from sqlalchemy.orm import Session
from .llm import chat_completion, chat_completion_json


# ── Clarification Agent ───────────────────────────────────────────────────────

CLARIFICATION_SYSTEM = """You are a senior software architect helping clarify product requirements.
Given a product requirement, generate 3-5 concise clarifying questions that, when answered,
will give you enough information to design the architecture.

Return ONLY a JSON object:
{
  "questions": ["question 1", "question 2", ...]
}

If the requirement is already clear enough, return:
{
  "questions": []
}"""


async def clarification_agent(requirement_text: str, db: Session) -> list[str]:
    messages = [
        {"role": "system", "content": CLARIFICATION_SYSTEM},
        {"role": "user", "content": f"Requirement: {requirement_text}"},
    ]
    result = await chat_completion_json(messages, db)
    return result.get("questions", [])


# ── Architecture Agent ────────────────────────────────────────────────────────

ARCHITECTURE_SYSTEM = """You are a senior software architect. Given a product requirement and clarification Q&A,
generate a complete architecture document.

Return a JSON object with these exact keys:
{
  "summary": "1-2 sentence project summary",
  "tech_stack": {
    "frontend": "...",
    "backend": "...",
    "database": "...",
    "other": "..."
  },
  "modules": [
    {"name": "module name", "description": "what it does"}
  ],
  "folder_structure": "ASCII tree of the project folder structure",
  "db_schema": "SQL CREATE TABLE statements or description",
  "api_endpoints": [
    {"method": "GET", "path": "/api/...", "description": "..."}
  ]
}"""


async def architecture_agent(requirement_text: str, qa_pairs: list[dict], db: Session) -> dict:
    qa_text = "\n".join(
        f"Q: {qa['question']}\nA: {qa['answer']}" for qa in qa_pairs
    ) if qa_pairs else "No clarifications needed."

    messages = [
        {"role": "system", "content": ARCHITECTURE_SYSTEM},
        {
            "role": "user",
            "content": f"Requirement: {requirement_text}\n\nClarifications:\n{qa_text}",
        },
    ]
    return await chat_completion_json(messages, db)


def arch_to_markdown(arch: dict) -> str:
    lines = [
        f"# Architecture: {arch.get('summary', '')}",
        "",
        "## Tech Stack",
    ]
    ts = arch.get("tech_stack", {})
    for k, v in ts.items():
        lines.append(f"- **{k.title()}**: {v}")

    lines += ["", "## Modules"]
    for m in arch.get("modules", []):
        lines.append(f"- **{m['name']}**: {m['description']}")

    lines += ["", "## Folder Structure", "```", arch.get("folder_structure", ""), "```"]
    lines += ["", "## Database Schema", "```sql", arch.get("db_schema", ""), "```"]

    lines += ["", "## API Endpoints"]
    for ep in arch.get("api_endpoints", []):
        lines.append(f"- `{ep['method']} {ep['path']}` — {ep['description']}")

    return "\n".join(lines)


# ── Ticket Agent ──────────────────────────────────────────────────────────────

TICKET_SYSTEM = """You are a senior engineering manager. Given an architecture document,
break it down into feature tickets.

Return a JSON object:
{
  "tickets": [
    {
      "id": "T1",
      "title": "short title",
      "description": "what needs to be built",
      "acceptance_criteria": "how to verify it's done",
      "tasks": [
        {"id": "T1-TS1", "title": "atomic task description"},
        {"id": "T1-TS2", "title": "atomic task description"}
      ]
    }
  ]
}

Rules:
- 5-10 tickets maximum
- Each ticket has 2-5 atomic tasks
- Tasks must be concrete and actionable
- Order tickets by dependency (foundational first)"""


async def ticket_agent(arch_content: dict, db: Session) -> list[dict]:
    arch_summary = json.dumps(arch_content, indent=2)
    messages = [
        {"role": "system", "content": TICKET_SYSTEM},
        {"role": "user", "content": f"Architecture:\n{arch_summary}"},
    ]
    result = await chat_completion_json(messages, db)
    tickets = result.get("tickets", [])
    # Add status fields
    for ticket in tickets:
        ticket["status"] = "pending"
        for task in ticket.get("tasks", []):
            task["status"] = "pending"
            task["result"] = None
    return tickets


# ── Debug Agent ───────────────────────────────────────────────────────────────

DEBUG_SYSTEM = """You are a debugging expert. Given a failed task and its error output,
provide a fix instruction.

Return a JSON object:
{
  "analysis": "brief explanation of what went wrong",
  "fix_instruction": "specific instruction to fix the issue, written as a task for an AI coding agent"
}"""


async def debug_agent(task_title: str, error_output: str, db: Session) -> dict:
    messages = [
        {"role": "system", "content": DEBUG_SYSTEM},
        {
            "role": "user",
            "content": f"Failed task: {task_title}\n\nError:\n{error_output}",
        },
    ]
    return await chat_completion_json(messages, db)
