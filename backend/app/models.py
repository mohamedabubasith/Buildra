import uuid
from datetime import datetime
from sqlalchemy import String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base


def new_id() -> str:
    return str(uuid.uuid4())


class LLMConfig(Base):
    __tablename__ = "llm_configs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    api_endpoint: Mapped[str] = mapped_column(String, nullable=False)
    api_key_encrypted: Mapped[str] = mapped_column(String, nullable=False)
    model: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String, nullable=False)
    # new | clarifying | arch_pending | arch_approved | executing | done | failed
    status: Mapped[str] = mapped_column(String, default="new")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    requirement: Mapped["Requirement"] = relationship("Requirement", back_populates="project", uselist=False)
    architecture: Mapped["ArchitectureDoc"] = relationship("ArchitectureDoc", back_populates="project", uselist=False)
    logs: Mapped[list["Log"]] = relationship("Log", back_populates="project", order_by="Log.created_at")


class Requirement(Base):
    __tablename__ = "requirements"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    project_id: Mapped[str] = mapped_column(String, ForeignKey("projects.id"), nullable=False)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    # JSON string: [{"question": "...", "answer": "..."}]
    clarification_qa: Mapped[str] = mapped_column(Text, default="[]")
    # Pending clarification question (one at a time)
    pending_question: Mapped[str | None] = mapped_column(Text, nullable=True)
    final_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    project: Mapped["Project"] = relationship("Project", back_populates="requirement")


class ArchitectureDoc(Base):
    __tablename__ = "architecture_docs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    project_id: Mapped[str] = mapped_column(String, ForeignKey("projects.id"), nullable=False)
    # JSON string of full arch content
    content: Mapped[str] = mapped_column(Text, nullable=False)
    markdown: Mapped[str] = mapped_column(Text, nullable=False)
    approved: Mapped[bool] = mapped_column(Boolean, default=False)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    project: Mapped["Project"] = relationship("Project", back_populates="architecture")


class Log(Base):
    __tablename__ = "logs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    project_id: Mapped[str] = mapped_column(String, ForeignKey("projects.id"), nullable=False)
    level: Mapped[str] = mapped_column(String, default="info")  # info | warn | error
    message: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    project: Mapped["Project"] = relationship("Project", back_populates="logs")
