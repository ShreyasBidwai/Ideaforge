from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.core.streaming import format_sse_event

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import User, Solution, ProblemStatement, Session
from app.models.project import Project
from app.models.document import Document
from app.models.sprint import Sprint
from app.models.sprint_task import SprintTask
from app.schemas.project import ProjectResponse, DocumentResponse, SprintResponse, SprintTaskResponse
from app.services.doc_generation_service import DocGenerationService
from app.services.sprint_generation_service import SprintGenerationService
from app.ai.provider import get_ai_provider, AIProvider
from app.services.project_dir_service import ProjectDirService
import uuid

router = APIRouter(dependencies=[Depends(get_current_user)])

@router.post("/solutions/{solution_id}/create-project", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    solution_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Fetch solution with problem and session details
    stmt = (
        select(Solution)
        .where(Solution.id == solution_id)
        .options(selectinload(Solution.problem_statement).selectinload(ProblemStatement.session))
    )
    result = await db.execute(stmt)
    solution = result.scalars().first()
    if not solution:
        raise HTTPException(status_code=404, detail="Solution not found")

    # Check if solution is approved
    if solution.status != "approved":
        raise HTTPException(status_code=400, detail="Solution must be approved to create a project")

    # Check if project already exists
    stmt_existing = select(Project).where(Project.solution_id == solution_id)
    res_existing = await db.execute(stmt_existing)
    existing_project = res_existing.scalars().first()
    if existing_project:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A project already exists for this solution"
        )

    problem = solution.problem_statement
    session = problem.session

    project_id = uuid.uuid4()
    project_dir = ProjectDirService.create_project_dir(str(project_id), solution.title)

    new_project = Project(
        id=project_id,
        user_id=current_user.id,
        solution_id=solution.id,
        name=solution.title,
        description=solution.description,
        industry=session.industry,
        location=session.location,
        maturity_level=session.maturity_level,
        tech_stack=solution.tech_stack or [],
        status="doc_generation",
        project_dir=project_dir
    )
    db.add(new_project)
    await db.commit()
    await db.refresh(new_project)
    return new_project

@router.get("/projects", response_model=list[ProjectResponse])
async def list_projects(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Project).where(Project.user_id == current_user.id).order_by(Project.created_at.desc())
    res = await db.execute(stmt)
    return res.scalars().all()

@router.get("/projects/{id}")
async def get_project(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(Project)
        .where(Project.id == id, Project.user_id == current_user.id)
        .options(selectinload(Project.documents), selectinload(Project.sprints))
    )
    res = await db.execute(stmt)
    project = res.scalars().first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@router.post("/projects/{id}/generate-docs", response_model=list[DocumentResponse])
async def generate_docs(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    ai_provider: AIProvider = Depends(get_ai_provider)
):
    service = DocGenerationService(ai_provider, db)
    return await service.generate_all_docs(id, current_user.id)

@router.post("/projects/{id}/generate-docs/stream")
async def generate_docs_stream(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    ai_provider: AIProvider = Depends(get_ai_provider)
):
    service = DocGenerationService(ai_provider, db)
    
    # Verify project exists and belongs to user
    stmt = select(Project).where(Project.id == id, Project.user_id == current_user.id)
    res = await db.execute(stmt)
    project = res.scalars().first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    async def event_generator():
        try:
            async for event in service.generate_all_docs_stream(id, current_user.id):
                sse_type = "progress"
                if event["status"] == "complete":
                    sse_type = "complete"
                yield format_sse_event(sse_type, event)
        except Exception as e:
            yield format_sse_event("error", {"status": "error", "message": str(e)})

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.post("/projects/{id}/generate-docs/cancel")
async def cancel_generate_docs(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Project).where(Project.id == id, Project.user_id == current_user.id)
    res = await db.execute(stmt)
    project = res.scalars().first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    cancelled = DocGenerationService.cancel_generation(str(id))
    if cancelled:
        project.status = "doc_generation_failed"
        await db.commit()
        return {"status": "success", "message": "Document generation cancelled successfully."}
    
    if project.status == "doc_generation":
        project.status = "doc_generation_failed"
        await db.commit()
        return {"status": "success", "message": "Reset project status."}

    return {"status": "ignored", "message": "No active document generation task to cancel."}

@router.get("/projects/{id}/documents", response_model=list[DocumentResponse])
async def list_project_documents(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt_proj = select(Project).where(Project.id == id, Project.user_id == current_user.id)
    proj_res = await db.execute(stmt_proj)
    if not proj_res.scalars().first():
        raise HTTPException(status_code=404, detail="Project not found")

    stmt = select(Document).where(Document.project_id == id)
    res = await db.execute(stmt)
    return res.scalars().all()

@router.get("/projects/{id}/documents/{doc_id}", response_model=DocumentResponse)
async def get_project_document(
    id: UUID,
    doc_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(Document)
        .join(Project, Document.project_id == Project.id)
        .where(Document.id == doc_id, Document.project_id == id, Project.user_id == current_user.id)
    )
    res = await db.execute(stmt)
    doc = res.scalars().first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc

@router.post("/projects/{id}/generate-sprints", response_model=list[SprintResponse])
async def generate_sprints(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    ai_provider: AIProvider = Depends(get_ai_provider)
):
    service = SprintGenerationService(db, ai_provider)
    return await service.generate_sprints(id, current_user.id)

@router.post("/projects/{id}/generate-sprints/stream")
async def generate_sprints_stream(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    ai_provider: AIProvider = Depends(get_ai_provider)
):
    service = SprintGenerationService(db, ai_provider)
    
    # Verify project exists and belongs to user
    stmt = select(Project).where(Project.id == id, Project.user_id == current_user.id)
    res = await db.execute(stmt)
    project = res.scalars().first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    async def event_generator():
        try:
            async for event in service.generate_sprints_stream(id, current_user.id):
                sse_type = "progress"
                if event["status"] == "complete":
                    sse_type = "complete"
                yield format_sse_event(sse_type, event)
        except HTTPException as he:
            yield format_sse_event("error", {"status": "error", "message": he.detail})
        except Exception as e:
            yield format_sse_event("error", {"status": "error", "message": str(e)})

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.post("/projects/{id}/generate-sprints/cancel")
async def cancel_generate_sprints(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Project).where(Project.id == id, Project.user_id == current_user.id)
    res = await db.execute(stmt)
    project = res.scalars().first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    cancelled = SprintGenerationService.cancel_generation(str(id))
    if cancelled:
        project.status = "doc_review"
        await db.commit()
        return {"status": "success", "message": "Sprint generation cancelled successfully."}

    if project.status == "doc_review" or project.status == "building":
        from app.services.claude_service import ClaudeService
        ClaudeService.terminate_process(str(id))

    return {"status": "ignored", "message": "No active sprint generation task to cancel."}

@router.get("/projects/{id}/sprints", response_model=list[SprintResponse])
async def list_project_sprints(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = SprintGenerationService(db)
    return await service.get_sprints(id, current_user.id)

@router.get("/projects/{id}/sprints/{sprint_id}/tasks", response_model=list[SprintTaskResponse])
async def list_sprint_tasks(
    id: UUID,
    sprint_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Verify project belongs to user
    stmt_proj = select(Project).where(Project.id == id, Project.user_id == current_user.id)
    proj_res = await db.execute(stmt_proj)
    if not proj_res.scalars().first():
        raise HTTPException(status_code=404, detail="Project not found")

    # Verify sprint belongs to project
    stmt_sprint = select(Sprint).where(Sprint.id == sprint_id, Sprint.project_id == id)
    sprint_res = await db.execute(stmt_sprint)
    if not sprint_res.scalars().first():
        raise HTTPException(status_code=404, detail="Sprint not found")

    stmt = select(SprintTask).where(SprintTask.sprint_id == sprint_id).order_by(SprintTask.task_number.asc())
    res = await db.execute(stmt)
    return res.scalars().all()

@router.get("/tasks/{task_id}", response_model=SprintTaskResponse)
async def get_task(
    task_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = SprintGenerationService(db)
    return await service.get_task(task_id, current_user.id)

@router.get("/projects/{id}/setup-guide")
async def get_setup_guide(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Project).where(Project.id == id, Project.user_id == current_user.id)
    res = await db.execute(stmt)
    project = res.scalars().first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    steps = [
        {"label": "Create PostgreSQL database", "command": "createdb ideaforge"},
        {"label": "Clone/Access the generated repository", "command": f"cd {project.project_dir or '/tmp'}"},
    ]

    has_python = False
    has_node = False
    
    tech_stack = project.tech_stack or []
    if isinstance(tech_stack, dict):
        tech_stack_list = list(tech_stack.keys()) + list(tech_stack.values())
    else:
        tech_stack_list = list(tech_stack)

    tech_stack_str = " ".join([str(t).lower() for t in tech_stack_list])
    
    if "python" in tech_stack_str or "fastapi" in tech_stack_str or "django" in tech_stack_str or "flask" in tech_stack_str:
        has_python = True
    if "react" in tech_stack_str or "node" in tech_stack_str or "typescript" in tech_stack_str or "vue" in tech_stack_str:
        has_node = True

    if has_python:
        steps.append({"label": "Install Python dependencies", "command": "pip install -r requirements.txt"})
        steps.append({"label": "Run migrations", "command": "alembic upgrade head"})
        steps.append({"label": "Start backend server", "command": "uvicorn app.main:app --reload"})
    
    if has_node:
        steps.append({"label": "Install Node dependencies", "command": "npm install"})
        steps.append({"label": "Start frontend dev server", "command": "npm run dev"})
        
    return {"steps": steps}

@router.get("/projects/{id}/env-template")
async def get_env_template(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Project).where(Project.id == id, Project.user_id == current_user.id)
    res = await db.execute(stmt)
    project = res.scalars().first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    env_content = """# App Configuration
APP_NAME=IdeaForge App
APP_ENV=development
PORT=8000

# Database Settings
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/ideaforge

# Security
JWT_SECRET=supersecretjwtkeyplaceholder
"""
    return {"env_template": env_content}


from fastapi.responses import FileResponse

@router.get("/projects/{id}/files")
async def get_project_files(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Project).where(Project.id == id, Project.user_id == current_user.id)
    res = await db.execute(stmt)
    project = res.scalars().first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    project_dir = project.project_dir
    if not project_dir:
        project_dir = ProjectDirService.get_project_dir(str(project.id), project.name)
        project.project_dir = project_dir
        await db.commit()

    return ProjectDirService.get_project_structure(project_dir)

@router.get("/projects/{id}/files/{path:path}")
async def get_project_file_content(
    id: UUID,
    path: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Project).where(Project.id == id, Project.user_id == current_user.id)
    res = await db.execute(stmt)
    project = res.scalars().first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    project_dir = project.project_dir
    if not project_dir:
        raise HTTPException(status_code=404, detail="Project directory not initialized")

    content = ProjectDirService.get_file_content(project_dir, path)
    if content is None:
        raise HTTPException(status_code=404, detail="File not found or access denied")

    return {"content": content}

@router.get("/projects/{id}/download")
async def download_project(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Project).where(Project.id == id, Project.user_id == current_user.id)
    res = await db.execute(stmt)
    project = res.scalars().first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    project_dir = project.project_dir
    if not project_dir:
        project_dir = ProjectDirService.get_project_dir(str(project.id), project.name)
        project.project_dir = project_dir
        await db.commit()

    zip_path = ProjectDirService.create_zip(project_dir)
    return FileResponse(
        zip_path,
        media_type="application/zip",
        filename=f"{ProjectDirService.sanitize_name(project.name)}.zip"
    )


import asyncio
from app.core.database import async_session
from app.services.build_orchestrator import BuildOrchestrator

@router.patch("/projects/{id}/documents/{doc_id}")
async def update_project_document(
    id: UUID,
    doc_id: UUID,
    payload: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt_proj = select(Project).where(Project.id == id, Project.user_id == current_user.id)
    res_proj = await db.execute(stmt_proj)
    project = res_proj.scalars().first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    stmt_doc = select(Document).where(Document.id == doc_id, Document.project_id == id)
    res_doc = await db.execute(stmt_doc)
    doc = res_doc.scalars().first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if "content" in payload:
        doc.content = payload["content"]
    if "title" in payload:
        doc.title = payload["title"]

    await db.commit()
    await db.refresh(doc)
    return doc

@router.post("/projects/{id}/documents/{doc_id}/approve")
async def approve_project_document(
    id: UUID,
    doc_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt_proj = select(Project).where(Project.id == id, Project.user_id == current_user.id)
    res_proj = await db.execute(stmt_proj)
    project = res_proj.scalars().first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    stmt_doc = select(Document).where(Document.id == doc_id, Document.project_id == id)
    res_doc = await db.execute(stmt_doc)
    doc = res_doc.scalars().first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    doc.status = "approved"
    await db.commit()
    await db.refresh(doc)
    return doc

@router.post("/projects/{id}/documents/approve-all")
async def approve_all_project_documents(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt_proj = select(Project).where(Project.id == id, Project.user_id == current_user.id)
    res_proj = await db.execute(stmt_proj)
    project = res_proj.scalars().first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    stmt_docs = select(Document).where(Document.project_id == id)
    res_docs = await db.execute(stmt_docs)
    docs = res_docs.scalars().all()

    for doc in docs:
        doc.status = "approved"

    await db.commit()
    return {"message": "All documents approved successfully"}

@router.patch("/tasks/{task_id}/prompt")
async def update_task_prompt(
    task_id: UUID,
    payload: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(SprintTask)
        .join(Sprint, SprintTask.sprint_id == Sprint.id)
        .join(Project, Sprint.project_id == Project.id)
        .where(SprintTask.id == task_id, Project.user_id == current_user.id)
    )
    res = await db.execute(stmt)
    task = res.scalars().first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if "prompt" in payload:
        task.prompt = payload["prompt"]
        from app.services.prompt_validator import PromptValidator
        task.validation_results = PromptValidator.validate_prompt(payload["prompt"])

    await db.commit()
    await db.refresh(task)
    return task

@router.post("/projects/{id}/approve-and-build")
async def approve_everything_and_build(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Project).where(Project.id == id, Project.user_id == current_user.id)
    res = await db.execute(stmt)
    project = res.scalars().first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    stmt_docs = select(Document).where(Document.project_id == id)
    res_docs = await db.execute(stmt_docs)
    docs = res_docs.scalars().all()

    if not docs or not all(doc.status == "approved" for doc in docs):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="All documents must be approved before triggering build"
        )

    # Verify that sprint plan and tasks have been generated
    from app.models import Sprint
    stmt_sprints = select(Sprint).where(Sprint.project_id == id)
    res_sprints = await db.execute(stmt_sprints)
    sprints = res_sprints.scalars().all()
    if not sprints:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sprint plan and tasks must be generated before starting the build. Please generate the sprint plan first."
        )

    # Trigger background build
    async def run_in_background():
        async with async_session() as background_db:
            orch = BuildOrchestrator(background_db)
            await orch.start_build(id, current_user.id)

    asyncio.create_task(run_in_background())
    return {"message": "All documents approved, starting build", "status": "building"}

@router.post("/projects/{id}/validate-prompts")
async def validate_project_prompts(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Project).where(Project.id == id, Project.user_id == current_user.id)
    res = await db.execute(stmt)
    project = res.scalars().first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    stmt_tasks = (
        select(SprintTask)
        .join(Sprint, SprintTask.sprint_id == Sprint.id)
        .where(Sprint.project_id == id)
    )
    res_tasks = await db.execute(stmt_tasks)
    tasks = res_tasks.scalars().all()

    # Convert to list of dicts for PromptValidator
    task_dicts = []
    for t in tasks:
        task_dicts.append({
            "name": t.name,
            "prompt": t.prompt
        })

    from app.services.prompt_validator import PromptValidator
    return PromptValidator.validate_all_prompts(task_dicts)


@router.delete("/projects/{id}")
async def delete_project(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    import logging
    logger = logging.getLogger(__name__)
    
    stmt = select(Project).where(Project.id == id, Project.user_id == current_user.id)
    res = await db.execute(stmt)
    project = res.scalars().first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Cancel build if queued or running
    try:
        from app.services.build_queue import BuildQueue
        from app.services.build_orchestrator import BuildOrchestrator
        queue = BuildQueue.get_instance()
        await queue.cancel_queued(id, current_user.id)
        orch = BuildOrchestrator(db)
        await orch.cancel_build(id, current_user.id)
    except Exception as e:
        logger.warning(f"Error canceling build for deleted project {id}: {e}")

    # Remove project files on disk
    try:
        import shutil
        import os
        if project.project_dir and os.path.exists(project.project_dir):
            shutil.rmtree(project.project_dir)
    except Exception as e:
        logger.warning(f"Error removing project files on disk for project {id}: {e}")

    # Delete project from database (cascade deletes sprints, tasks, logs, etc.)
    await db.delete(project)
    await db.commit()

    return {"message": "Project deleted successfully"}




