"""
Workflow router — handles the requirement → clarification → architecture pipeline.
"""
import json
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Project, Requirement, ArchitectureDoc, Log
from ..schemas import (
    RequirementIn, ClarifyAnswerIn, RequirementOut, QAPair,
    ArchitectureOut, LogOut,
)
from ..services.agents import clarification_agent, architecture_agent, arch_to_markdown
from ..services.sse import push_event, event_generator
from ..config import DOCS_DIR

router = APIRouter(tags=["workflow"])


def _get_project(project_id: str, db: Session) -> Project:
    p = db.query(Project).filter(Project.id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    return p


def _add_log(db: Session, project_id: str, message: str, level: str = "info"):
    log = Log(project_id=project_id, level=level, message=message)
    db.add(log)
    db.commit()


# ── Requirement ───────────────────────────────────────────────────────────────

@router.post("/projects/{project_id}/requirement", response_model=RequirementOut)
async def submit_requirement(
    project_id: str,
    body: RequirementIn,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    project = _get_project(project_id, db)

    # Upsert requirement
    req = project.requirement
    if req:
        req.raw_text = body.text
        req.clarification_qa = "[]"
        req.pending_question = None
        req.final_text = None
    else:
        req = Requirement(project_id=project_id, raw_text=body.text)
        db.add(req)

    project.status = "clarifying"
    db.commit()
    db.refresh(req)

    background_tasks.add_task(_run_clarification, project_id, body.text, db)

    qa = json.loads(req.clarification_qa)
    return RequirementOut(
        id=req.id,
        project_id=project_id,
        raw_text=req.raw_text,
        clarification_qa=[QAPair(**x) for x in qa],
        pending_question=req.pending_question,
        final_text=req.final_text,
    )


async def _run_clarification(project_id: str, requirement_text: str, db: Session):
    try:
        await push_event(project_id, "log", {"level": "info", "message": "Analyzing requirement..."})
        questions = await clarification_agent(requirement_text, db)

        req = db.query(Requirement).filter(Requirement.project_id == project_id).first()
        if not req:
            return

        if questions:
            req.pending_question = questions[0]
            db.commit()
            await push_event(project_id, "clarification_question", {"question": questions[0]})
            await push_event(project_id, "log", {"level": "info", "message": f"Clarification needed: {questions[0]}"})
        else:
            # No clarification needed — go straight to architecture
            req.final_text = requirement_text
            project = db.query(Project).filter(Project.id == project_id).first()
            project.status = "arch_pending"
            db.commit()
            await push_event(project_id, "status_change", {"status": "arch_pending"})
            await push_event(project_id, "log", {"level": "info", "message": "No clarification needed. Generating architecture..."})
            await _run_architecture(project_id, db)

    except Exception as e:
        _add_log(db, project_id, f"Clarification error: {e}", "error")
        await push_event(project_id, "log", {"level": "error", "message": str(e)})


# ── Clarification Answer ──────────────────────────────────────────────────────

@router.post("/projects/{project_id}/clarify", response_model=RequirementOut)
async def answer_clarification(
    project_id: str,
    body: ClarifyAnswerIn,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    project = _get_project(project_id, db)
    req = project.requirement
    if not req or not req.pending_question:
        raise HTTPException(status_code=400, detail="No pending clarification question")

    qa = json.loads(req.clarification_qa)
    qa.append({"question": req.pending_question, "answer": body.answer})
    req.clarification_qa = json.dumps(qa)
    req.pending_question = None
    req.final_text = req.raw_text  # Mark as ready
    project.status = "arch_pending"
    db.commit()
    db.refresh(req)

    background_tasks.add_task(_run_architecture, project_id, db)

    return RequirementOut(
        id=req.id,
        project_id=project_id,
        raw_text=req.raw_text,
        clarification_qa=[QAPair(**x) for x in qa],
        pending_question=None,
        final_text=req.final_text,
    )


# ── Architecture Generation ───────────────────────────────────────────────────

async def _run_architecture(project_id: str, db: Session):
    try:
        await push_event(project_id, "log", {"level": "info", "message": "Generating architecture..."})

        req = db.query(Requirement).filter(Requirement.project_id == project_id).first()
        qa = json.loads(req.clarification_qa) if req else []

        arch_content = await architecture_agent(req.raw_text, qa, db)
        markdown = arch_to_markdown(arch_content)

        # Save to DB
        project = db.query(Project).filter(Project.id == project_id).first()
        existing = project.architecture
        if existing:
            existing.content = json.dumps(arch_content)
            existing.markdown = markdown
            existing.approved = False
            existing.approved_at = None
        else:
            doc = ArchitectureDoc(
                project_id=project_id,
                content=json.dumps(arch_content),
                markdown=markdown,
            )
            db.add(doc)

        # Save markdown file
        docs_path = DOCS_DIR / f"{project_id}.md"
        docs_path.write_text(markdown)

        project.status = "arch_pending"
        db.commit()

        await push_event(project_id, "status_change", {"status": "arch_pending"})
        await push_event(project_id, "architecture_ready", {"markdown": markdown})
        await push_event(project_id, "log", {"level": "info", "message": "Architecture generated. Awaiting approval."})

    except Exception as e:
        db.rollback()
        project = db.query(Project).filter(Project.id == project_id).first()
        if project:
            project.status = "failed"
            db.commit()
        await push_event(project_id, "log", {"level": "error", "message": f"Architecture generation failed: {e}"})


@router.get("/projects/{project_id}/architecture", response_model=ArchitectureOut | None)
def get_architecture(project_id: str, db: Session = Depends(get_db)):
    project = _get_project(project_id, db)
    doc = project.architecture
    if not doc:
        return None
    return ArchitectureOut(
        id=doc.id,
        project_id=project_id,
        content=json.loads(doc.content),
        markdown=doc.markdown,
        approved=doc.approved,
        approved_at=doc.approved_at,
    )


@router.post("/projects/{project_id}/architecture/approve")
async def approve_architecture(
    project_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    project = _get_project(project_id, db)
    doc = project.architecture
    if not doc:
        raise HTTPException(status_code=404, detail="No architecture document found")

    doc.approved = True
    doc.approved_at = datetime.utcnow()
    project.status = "arch_approved"
    db.commit()

    await push_event(project_id, "status_change", {"status": "arch_approved"})
    await push_event(project_id, "log", {"level": "info", "message": "Architecture approved. Generating tickets..."})

    from .execution import _generate_tickets
    background_tasks.add_task(_generate_tickets, project_id, db)

    return {"message": "Architecture approved. Ticket generation started."}


# ── Logs (SSE) ─────────────────────────────────────────────────────────────────

@router.get("/projects/{project_id}/logs")
def stream_logs(project_id: str, db: Session = Depends(get_db)):
    _get_project(project_id, db)
    return StreamingResponse(
        event_generator(project_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/projects/{project_id}/logs/history", response_model=list[LogOut])
def get_log_history(project_id: str, db: Session = Depends(get_db)):
    _get_project(project_id, db)
    return db.query(Log).filter(Log.project_id == project_id).order_by(Log.created_at).all()
