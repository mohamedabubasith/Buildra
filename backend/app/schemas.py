from pydantic import BaseModel
from datetime import datetime
from typing import Any


# ── LLM Config ──────────────────────────────────────────────────────────────

class LLMConfigIn(BaseModel):
    api_endpoint: str
    api_key: str
    model: str


class LLMConfigOut(BaseModel):
    id: str
    api_endpoint: str
    model: str
    created_at: datetime

    class Config:
        from_attributes = True


# ── Projects ─────────────────────────────────────────────────────────────────

class ProjectCreate(BaseModel):
    name: str


class ProjectOut(BaseModel):
    id: str
    name: str
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ── Requirements ─────────────────────────────────────────────────────────────

class RequirementIn(BaseModel):
    text: str


class ClarifyAnswerIn(BaseModel):
    answer: str


class QAPair(BaseModel):
    question: str
    answer: str


class RequirementOut(BaseModel):
    id: str
    project_id: str
    raw_text: str
    clarification_qa: list[QAPair]
    pending_question: str | None
    final_text: str | None


# ── Architecture ──────────────────────────────────────────────────────────────

class ArchitectureOut(BaseModel):
    id: str
    project_id: str
    content: Any  # parsed JSON
    markdown: str
    approved: bool
    approved_at: datetime | None


# ── Tickets ───────────────────────────────────────────────────────────────────

class TaskItem(BaseModel):
    id: str
    title: str
    status: str
    result: Any | None = None


class TicketOut(BaseModel):
    id: str
    project_id: str
    title: str
    description: str
    acceptance_criteria: str
    status: str
    tasks: list[TaskItem]


# ── Logs ──────────────────────────────────────────────────────────────────────

class LogOut(BaseModel):
    id: str
    project_id: str
    level: str
    message: str
    created_at: datetime

    class Config:
        from_attributes = True


# ── Execution ─────────────────────────────────────────────────────────────────

class ExecuteResponse(BaseModel):
    message: str
    task_count: int
