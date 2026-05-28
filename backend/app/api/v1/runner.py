import asyncio
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import User
from app.models.project import Project
from app.services.project_runner import ProjectRunner
from app.services.setup_manifest_service import SetupManifestService
from app.services.project_dir_service import ProjectDirService
from app.core.streaming import format_sse_event

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.post("/projects/{id}/run/install")
async def run_install(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Project).where(Project.id == id, Project.user_id == current_user.id)
    res = await db.execute(stmt)
    project = res.scalars().first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    project_dir = ProjectDirService.get_project_dir(str(project.id), project.name)
    result = await ProjectRunner.install(id, project_dir)
    return result


@router.post("/projects/{id}/run/start")
async def run_start(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Project).where(Project.id == id, Project.user_id == current_user.id)
    res = await db.execute(stmt)
    project = res.scalars().first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Gate on setup manifest ready
    manifest_service = SetupManifestService(db)
    ready = await manifest_service.all_required_complete(id)
    if not ready:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot start project: human setup steps are incomplete."
        )

    project_dir = ProjectDirService.get_project_dir(str(project.id), project.name)
    result = await ProjectRunner.start(id, project_dir)
    return result


@router.post("/projects/{id}/run/stop")
async def run_stop(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Project).where(Project.id == id, Project.user_id == current_user.id)
    res = await db.execute(stmt)
    project = res.scalars().first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    result = await ProjectRunner.stop(id)
    return result


@router.get("/projects/{id}/run/status")
async def get_run_status(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Project).where(Project.id == id, Project.user_id == current_user.id)
    res = await db.execute(stmt)
    project = res.scalars().first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return ProjectRunner.status(id)


@router.get("/projects/{id}/run/logs")
async def get_run_logs(
    id: UUID,
    source: str = Query("backend", enum=["backend", "frontend", "install"]),
    tail: int = 200,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Project).where(Project.id == id, Project.user_id == current_user.id)
    res = await db.execute(stmt)
    project = res.scalars().first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    logs = ProjectRunner.get_logs(id, source=source, tail=tail)
    return {"logs": logs}


@router.get("/projects/{id}/run/logs/stream")
async def stream_run_logs(
    id: UUID,
    source: str = Query("backend", enum=["backend", "frontend", "install"]),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Project).where(Project.id == id, Project.user_id == current_user.id)
    res = await db.execute(stmt)
    project = res.scalars().first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    async def event_generator():
        last_index = 0
        while True:
            status_info = ProjectRunner.status(id)
            is_active = status_info["alive"] or status_info["status"] == "installing"
            
            logs = ProjectRunner.get_logs(id, source=source, tail=1000)
            if len(logs) > last_index:
                new_lines = logs[last_index:]
                last_index = len(logs)
                for line in new_lines:
                    yield format_sse_event("log", line)

            if not is_active and len(logs) == last_index:
                yield format_sse_event("end", "=== Stream ended ===")
                break
                
            await asyncio.sleep(0.5)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
