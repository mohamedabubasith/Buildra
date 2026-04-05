"""
Execution router — ticket generation + task execution via OpenDevin.
"""
import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Project, Log
from ..schemas import TicketOut, TaskItem, ExecuteResponse
from ..services.agents import ticket_agent, debug_agent
from ..services.opendevin import send_task, wait_for_result, OpenDevinError
from ..services.sse import push_event
from ..config import TICKETS_DIR

router = APIRouter(tags=["execution"])


def _get_project(project_id: str, db: Session) -> Project:
    p = db.query(Project).filter(Project.id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    return p


def _ticket_dir(project_id: str) -> Path:
    d = TICKETS_DIR / project_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def _load_tickets(project_id: str) -> list[dict]:
    d = _ticket_dir(project_id)
    tickets = []
    for f in sorted(d.glob("T*.json")):
        tickets.append(json.loads(f.read_text()))
    return tickets


def _save_ticket(project_id: str, ticket: dict):
    path = _ticket_dir(project_id) / f"{ticket['id']}.json"
    path.write_text(json.dumps(ticket, indent=2))


def _add_log(db: Session, project_id: str, message: str, level: str = "info"):
    log = Log(project_id=project_id, level=level, message=message)
    db.add(log)
    db.commit()


# ── Ticket Generation (called from workflow router after arch approval) ────────

async def _generate_tickets(project_id: str, db: Session):
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project or not project.architecture:
            return

        arch_content = json.loads(project.architecture.content)
        await push_event(project_id, "log", {"level": "info", "message": "Generating tickets from architecture..."})

        tickets = await ticket_agent(arch_content, db)

        # Add project_id to each ticket and save to files
        for ticket in tickets:
            ticket["project_id"] = project_id
            _save_ticket(project_id, ticket)

        project.status = "arch_approved"
        _add_log(db, project_id, f"Generated {len(tickets)} tickets.")
        db.commit()

        await push_event(project_id, "tickets_ready", {"count": len(tickets)})
        await push_event(project_id, "status_change", {"status": "arch_approved"})
        await push_event(project_id, "log", {"level": "info", "message": f"{len(tickets)} tickets created. Ready to execute."})

    except Exception as e:
        _add_log(db, project_id, f"Ticket generation failed: {e}", "error")
        await push_event(project_id, "log", {"level": "error", "message": f"Ticket generation failed: {e}"})


# ── Ticket List ───────────────────────────────────────────────────────────────

@router.get("/projects/{project_id}/tickets", response_model=list[TicketOut])
def list_tickets(project_id: str, db: Session = Depends(get_db)):
    _get_project(project_id, db)
    tickets = _load_tickets(project_id)
    result = []
    for t in tickets:
        result.append(TicketOut(
            id=t["id"],
            project_id=t.get("project_id", project_id),
            title=t["title"],
            description=t.get("description", ""),
            acceptance_criteria=t.get("acceptance_criteria", ""),
            status=t.get("status", "pending"),
            tasks=[TaskItem(**task) for task in t.get("tasks", [])],
        ))
    return result


# ── Execute ───────────────────────────────────────────────────────────────────

@router.post("/projects/{project_id}/execute", response_model=ExecuteResponse)
async def execute_project(
    project_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    project = _get_project(project_id, db)
    if project.status not in ("arch_approved", "failed"):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot execute from status '{project.status}'. Architecture must be approved first."
        )

    tickets = _load_tickets(project_id)
    if not tickets:
        raise HTTPException(status_code=400, detail="No tickets found. Generate tickets first.")

    task_count = sum(len(t.get("tasks", [])) for t in tickets)
    background_tasks.add_task(_run_execution, project_id, db)

    return ExecuteResponse(message="Execution started.", task_count=task_count)


async def _run_execution(project_id: str, db: Session):
    """Iterate all tickets → tasks, send each to OpenDevin, handle failures."""
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        project.status = "executing"
        db.commit()
        await push_event(project_id, "status_change", {"status": "executing"})

        tickets = _load_tickets(project_id)
        arch_doc = ""
        if project.architecture:
            arch_doc = project.architecture.markdown

        for ticket in tickets:
            if ticket.get("status") == "done":
                continue

            ticket["status"] = "in_progress"
            _save_ticket(project_id, ticket)
            await push_event(project_id, "ticket_update", {"id": ticket["id"], "status": "in_progress"})
            await push_event(project_id, "log", {"level": "info", "message": f"Starting ticket: {ticket['title']}"})

            ticket_success = True
            for task in ticket.get("tasks", []):
                if task.get("status") == "done":
                    continue

                success = await _execute_task(project_id, ticket, task, arch_doc, db)
                if not success:
                    ticket_success = False
                    ticket["status"] = "failed"
                    _save_ticket(project_id, ticket)
                    await push_event(project_id, "ticket_update", {"id": ticket["id"], "status": "failed"})
                    break

                # Update task in ticket file
                for t in ticket["tasks"]:
                    if t["id"] == task["id"]:
                        t["status"] = task["status"]
                        t["result"] = task.get("result")
                _save_ticket(project_id, ticket)

            if ticket_success:
                ticket["status"] = "done"
                _save_ticket(project_id, ticket)
                await push_event(project_id, "ticket_update", {"id": ticket["id"], "status": "done"})
                _add_log(db, project_id, f"Ticket done: {ticket['title']}")

        # Check overall success
        final_tickets = _load_tickets(project_id)
        all_done = all(t.get("status") == "done" for t in final_tickets)
        project = db.query(Project).filter(Project.id == project_id).first()
        project.status = "done" if all_done else "failed"
        db.commit()

        final_status = "done" if all_done else "failed"
        await push_event(project_id, "status_change", {"status": final_status})
        await push_event(project_id, "log", {
            "level": "info" if all_done else "error",
            "message": "All tasks completed successfully!" if all_done else "Some tasks failed. Check logs.",
        })

    except Exception as e:
        _add_log(db, project_id, f"Execution error: {e}", "error")
        await push_event(project_id, "log", {"level": "error", "message": f"Execution error: {e}"})
        project = db.query(Project).filter(Project.id == project_id).first()
        if project:
            project.status = "failed"
            db.commit()


async def _execute_task(
    project_id: str,
    ticket: dict,
    task: dict,
    arch_doc: str,
    db: Session,
    retry: bool = False,
) -> bool:
    """Send a single task to OpenDevin. Returns True on success."""
    context = f"""
Project Architecture:
{arch_doc[:2000]}

Ticket: {ticket['title']}
Ticket Description: {ticket.get('description', '')}
Acceptance Criteria: {ticket.get('acceptance_criteria', '')}

Task to execute: {task['title']}
{"(RETRY — previous attempt failed, fix the issue)" if retry else ""}
"""
    task["status"] = "in_progress"
    await push_event(project_id, "task_update", {"id": task["id"], "status": "in_progress"})
    await push_event(project_id, "log", {"level": "info", "message": f"  → Task: {task['title']}"})

    MAX_RETRIES = 3
    for attempt in range(MAX_RETRIES):
        try:
            conv = await send_task(context)
            result = await wait_for_result(conv["conversation_id"])

            if result["status"] == "success":
                task["status"] = "done"
                task["result"] = result["output"][:500] if result["output"] else "OK"
                await push_event(project_id, "task_update", {"id": task["id"], "status": "done"})
                await push_event(project_id, "log", {"level": "info", "message": f"  ✓ Done: {task['title']}"})
                return True

            # Failed — try debug agent
            error = result.get("error") or result.get("output") or "Unknown error"
            await push_event(project_id, "log", {"level": "warn", "message": f"  ✗ Failed (attempt {attempt + 1}): {error[:200]}"})

            if attempt < MAX_RETRIES - 1:
                fix = await debug_agent(task["title"], error, db)
                await push_event(project_id, "log", {"level": "info", "message": f"  🔧 Fix: {fix.get('fix_instruction', '')[:200]}"})
                # Append fix instruction to task for next retry
                task["title"] = f"{task['title']} — FIX: {fix.get('fix_instruction', '')}"

        except OpenDevinError as e:
            await push_event(project_id, "log", {"level": "warn", "message": f"  OpenDevin error (attempt {attempt+1}): {e}"})
            if attempt < MAX_RETRIES - 1:
                import asyncio
                await asyncio.sleep(5)

    task["status"] = "failed"
    await push_event(project_id, "task_update", {"id": task["id"], "status": "failed"})
    return False
